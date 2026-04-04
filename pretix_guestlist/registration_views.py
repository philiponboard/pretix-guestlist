import logging
from decimal import Decimal

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.views import View
from pretix.base.signals import order_placed

from .forms import DJAddGuestForm, GuestRegistrationForm
from .models import DJ, Guest, GuestListSettings
from .tasks import send_guest_invitation

logger = logging.getLogger(__name__)


def _create_voucher_for_guest(guest, product, event):
    """Create a Pretix voucher for a guest so they can see the hidden GL product."""
    from pretix.base.models import Voucher

    code = 'GL-{}'.format(get_random_string(12).upper())

    voucher = Voucher.objects.create(
        event=event,
        code=code,
        max_usages=1,
        valid_until=event.date_to or event.date_from,
        item=product,
        price_mode='none',
        value=Decimal('0.00'),
        show_hidden_items=True,
        tag='guestlist',
        comment=str(_('Guest list voucher for {}')).format(guest.email),
    )

    guest.voucher = voucher
    guest.save(update_fields=['voucher'])

    return voucher


class DJDashboardView(View):
    """DJ dashboard: view guests, add new guests, resend invitations."""

    def dispatch(self, request, *args, **kwargs):
        self.dj = get_object_or_404(
            DJ.objects.select_related('event', 'event__organizer'),
            token=kwargs['token'],
        )
        self.event = self.dj.event
        self.settings = GuestListSettings.objects.filter(event=self.event).first()
        return super().dispatch(request, *args, **kwargs)

    def _get_context(self, add_form=None, error=None):
        return {
            'dj': self.dj,
            'event': self.event,
            'settings': self.settings,
            'guests': self.dj.guests.select_related('order').order_by('-registered_at'),
            'add_form': add_form or DJAddGuestForm(),
            'error': error,
        }

    def get(self, request, *args, **kwargs):
        return render(request, 'pretix_guestlist/dashboard.html', self._get_context())

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '')

        if action == 'add_guest':
            return self._handle_add_guest(request)
        elif action == 'resend':
            return self._handle_resend(request)

        return redirect(request.path)

    def _handle_add_guest(self, request):
        form = DJAddGuestForm(request.POST)
        if not form.is_valid():
            return render(request, 'pretix_guestlist/dashboard.html',
                          self._get_context(add_form=form))

        email = form.cleaned_data['email']
        ticket_type = form.cleaned_data['ticket_type']

        if ticket_type == Guest.TICKET_HALF:
            try:
                guest = self._create_quota_guest(email, ticket_type)
            except QuotaExhausted:
                return render(request, 'pretix_guestlist/dashboard.html',
                              self._get_context(add_form=form, error=_('Half-price quota exhausted.')))
        elif ticket_type == Guest.TICKET_FREE:
            try:
                guest = self._create_quota_guest(email, ticket_type)
            except QuotaExhausted:
                return render(request, 'pretix_guestlist/dashboard.html',
                              self._get_context(add_form=form, error=_('Free ticket quota exhausted.')))
        else:
            # Full Price — unlimited
            guest = Guest.objects.create(
                dj=self.dj,
                email=email,
                ticket_type=ticket_type,
                status=Guest.STATUS_INVITED,
            )

        send_guest_invitation(guest.pk)
        return redirect(request.path)

    @transaction.atomic
    def _create_quota_guest(self, email, ticket_type):
        dj = DJ.objects.select_for_update().get(pk=self.dj.pk)

        if ticket_type == Guest.TICKET_HALF:
            if dj.half_price_invited_count >= dj.half_price_quota:
                raise QuotaExhausted()
        elif ticket_type == Guest.TICKET_FREE:
            if dj.free_invited_count >= dj.free_quota:
                raise QuotaExhausted()

        return Guest.objects.create(
            dj=dj,
            email=email,
            ticket_type=ticket_type,
            status=Guest.STATUS_INVITED,
        )

    def _handle_resend(self, request):
        guest_id = request.POST.get('guest_id')
        if guest_id:
            guest = get_object_or_404(Guest, pk=guest_id, dj=self.dj)
            send_guest_invitation(guest.pk)
        return redirect(request.path)


class GuestRegistrationView(View):
    """Guest self-registration via personal token link."""

    def dispatch(self, request, *args, **kwargs):
        self.dj = get_object_or_404(
            DJ.objects.select_related('event', 'event__organizer'),
            token=kwargs['dj_token'],
        )
        self.guest = get_object_or_404(
            Guest.objects.select_related('dj'),
            guest_token=kwargs['guest_token'],
            dj=self.dj,
        )
        self.event = self.dj.event
        self.settings = GuestListSettings.objects.filter(event=self.event).first()

        if self.guest.status != Guest.STATUS_INVITED:
            return render(request, 'pretix_guestlist/already_registered.html', {
                'guest': self.guest, 'event': self.event, 'dj': self.dj,
            })

        return super().dispatch(request, *args, **kwargs)

    def _get_product(self):
        if not self.settings:
            return None
        return self.settings.get_product_for_ticket_type(self.guest.ticket_type)

    def _get_price(self):
        product = self._get_product()
        if not product:
            return Decimal('0.00')
        return product.default_price or Decimal('0.00')

    def get(self, request, *args, **kwargs):
        form = GuestRegistrationForm(initial={'email': self.guest.email})
        return render(request, 'pretix_guestlist/guest_register.html', {
            'form': form,
            'guest': self.guest,
            'dj': self.dj,
            'event': self.event,
            'price': self._get_price(),
            'is_free': self._get_price() == Decimal('0.00'),
        })

    def post(self, request, *args, **kwargs):
        form = GuestRegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, 'pretix_guestlist/guest_register.html', {
                'form': form,
                'guest': self.guest,
                'dj': self.dj,
                'event': self.event,
                'price': self._get_price(),
                'is_free': self._get_price() == Decimal('0.00'),
            })

        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']

        product = self._get_product()
        if not product:
            raise Http404(_('No product configured for this ticket type.'))

        price = product.default_price or Decimal('0.00')

        if price == Decimal('0.00'):
            return self._register_free(first_name, last_name, email, product)
        else:
            return self._register_paid(request, first_name, last_name, email, product)

    @transaction.atomic
    def _register_free(self, first_name, last_name, email, product):
        guest = Guest.objects.select_for_update().get(pk=self.guest.pk)
        if guest.status != Guest.STATUS_INVITED:
            return render(self.request, 'pretix_guestlist/already_registered.html', {
                'guest': guest, 'event': self.event, 'dj': self.dj,
            })

        guest.first_name = first_name
        guest.last_name = last_name
        guest.email = email

        order, position = self._create_pretix_order(product, first_name, last_name, email)
        guest.status = Guest.STATUS_REGISTERED
        guest.order = order
        guest.order_position = position
        guest.save()

        return render(self.request, 'pretix_guestlist/register_success.html', {
            'dj': self.dj, 'event': self.event, 'guest': guest,
        })

    def _register_paid(self, request, first_name, last_name, email, product):
        guest = self.guest
        guest.first_name = first_name
        guest.last_name = last_name
        guest.email = email
        guest.save(update_fields=['first_name', 'last_name', 'email'])

        # Create voucher for guest (makes hidden product visible in checkout)
        voucher = _create_voucher_for_guest(guest, product, self.event)

        # Redirect to Pretix voucher redeem page (shows only the GL product)
        checkout_url = '/{organizer}/{event}/redeem?voucher={voucher_code}'.format(
            organizer=self.event.organizer.slug,
            event=self.event.slug,
            voucher_code=voucher.code,
        )
        return redirect(checkout_url)

    def _create_pretix_order(self, product, first_name, last_name, email):
        from pretix.base.models import Order, OrderPosition

        name_parts = {
            '_scheme': 'given_family',
            'given_name': first_name,
            'family_name': last_name,
        }

        sales_channel = self.event.organizer.sales_channels.filter(
            identifier='web'
        ).first()

        order = Order.objects.create(
            event=self.event,
            email=email,
            status=Order.STATUS_PAID,
            locale=self.event.settings.locale or 'en',
            total=Decimal('0.00'),
            meta_info='{"guestlist_plugin": true}',
            sales_channel=sales_channel,
        )

        position = OrderPosition.objects.create(
            order=order,
            item=product,
            variation=None,
            price=Decimal('0.00'),
            attendee_name_parts=name_parts,
            attendee_email=email,
        )

        order.create_transactions(is_new=True, positions=[position])
        order_placed.send(sender=self.event, order=order)

        if email:
            self._send_confirmation_mail(order)

        return order, position

    def _send_confirmation_mail(self, order):
        from pretix.base.email import get_email_context

        try:
            email_template = self.event.settings.mail_text_order_free or self.event.settings.mail_text_order_placed
            subject_template = self.event.settings.mail_subject_order_free or self.event.settings.mail_subject_order_placed
            email_context = get_email_context(event=self.event, order=order)

            order.send_mail(
                subject_template, email_template, email_context,
                'pretix.event.order.email.order_placed',
                attach_tickets=True,
            )
        except Exception as e:
            logger.warning('Failed to send confirmation mail for order %s: %s', order.code, e)


class QuotaExhausted(Exception):
    pass
