import csv
import io
import logging

from django.contrib import messages
from django.core.validators import validate_email
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from pretix.control.permissions import EventPermissionRequiredMixin

from .forms import DJForm, SettingsForm
from .models import DJ, Guest, GuestListSettings
from .tasks import send_dj_invitation, send_guest_invitation

logger = logging.getLogger(__name__)

CSV_MAX_SIZE = 1024 * 1024  # 1 MB


class GuestListSettingsView(EventPermissionRequiredMixin, UpdateView):
    permission = 'can_change_event_settings'
    template_name = 'pretix_guestlist/settings.html'
    form_class = SettingsForm

    def get_object(self, queryset=None):
        obj, _ = GuestListSettings.objects.get_or_create(event=self.request.event)
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:settings', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })

    def form_valid(self, form):
        messages.success(self.request, _('Settings saved.'))
        return super().form_valid(form)


class DJListView(EventPermissionRequiredMixin, ListView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_list.html'
    context_object_name = 'djs'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)


class DJCreateView(EventPermissionRequiredMixin, CreateView):
    permission = 'can_change_event_settings'
    model = DJ
    form_class = DJForm
    template_name = 'pretix_guestlist/dj_form.html'

    def form_valid(self, form):
        form.instance.event = self.request.event
        messages.success(self.request, _('DJ created.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class DJUpdateView(EventPermissionRequiredMixin, UpdateView):
    permission = 'can_change_event_settings'
    model = DJ
    form_class = DJForm
    template_name = 'pretix_guestlist/dj_form.html'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:dj.detail', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
            'pk': self.object.pk,
        })

    def form_valid(self, form):
        messages.success(self.request, _('DJ updated.'))
        return super().form_valid(form)


class DJDetailView(EventPermissionRequiredMixin, DetailView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_detail.html'
    context_object_name = 'dj'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['guests'] = self.object.guests.select_related('order').all()
        return ctx


class DJDeleteView(EventPermissionRequiredMixin, DeleteView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_delete.html'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_success_url(self):
        messages.success(self.request, _('DJ deleted.'))
        return reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class SendInvitationView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        dj = get_object_or_404(DJ, pk=kwargs['pk'], event=request.event)
        send_dj_invitation(dj.pk)
        messages.success(request, _('Invitation sent to {name}.').format(name=dj.name))
        return redirect(reverse('plugins:pretix_guestlist:dj.detail', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
            'pk': dj.pk,
        }))


class SendAllInvitationsView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        djs = DJ.objects.filter(event=request.event, invitation_sent=False)
        count = 0
        for dj in djs:
            send_dj_invitation(dj.pk)
            count += 1
        if count:
            messages.success(request, _('Invitations sent to {count} DJs.').format(count=count))
        else:
            messages.info(request, _('All invitations have already been sent.'))
        return redirect(reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
        }))


class ResendGuestInvitationView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        dj = get_object_or_404(DJ, pk=kwargs['pk'], event=request.event)
        guest = get_object_or_404(Guest, pk=kwargs['guest_pk'], dj=dj, status=Guest.STATUS_INVITED)
        send_guest_invitation(guest.pk)
        messages.success(request, _('Invitation resent to {email}.').format(email=guest.email))
        return redirect(reverse('plugins:pretix_guestlist:dj.detail', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
            'pk': dj.pk,
        }))


class CSVTemplateDownloadView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="dj_import_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['name', 'email', 'half_price_quota', 'free_quota'])
        writer.writerow(['DJ Pretix', 'dj@email.com', '1', '1'])
        return response


class CSVUploadView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        redirect_url = reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
        })

        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, _('No file uploaded.'))
            return redirect(redirect_url)

        if not csv_file.name.endswith('.csv'):
            messages.error(request, _('Please upload a CSV file.'))
            return redirect(redirect_url)

        if csv_file.size > CSV_MAX_SIZE:
            messages.error(request, _('File too large. Maximum size is 1 MB.'))
            return redirect(redirect_url)

        try:
            decoded = csv_file.read().decode('utf-8-sig')

            # Auto-detect delimiter (comma or semicolon)
            first_line = decoded.split('\n')[0]
            delimiter = ';' if ';' in first_line and ',' not in first_line else ','

            reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
            # Strip whitespace from header names
            reader.fieldnames = [f.strip() for f in (reader.fieldnames or [])]

            required_fields = {'name', 'email'}
            if not required_fields.issubset(set(reader.fieldnames)):
                messages.error(request, _('CSV must contain columns: name, email. Found: {cols}').format(
                    cols=', '.join(reader.fieldnames)))
                return redirect(redirect_url)

            created = 0
            skipped = 0
            errors = []

            with transaction.atomic():
                for i, row in enumerate(reader, start=2):
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip()

                    if not name or not email:
                        errors.append(_('Row {row}: name and email are required.').format(row=i))
                        continue

                    # Validate email format
                    try:
                        validate_email(email)
                    except Exception:
                        errors.append(_('Row {row}: invalid email address.').format(row=i))
                        continue

                    # Skip duplicates (same email for this event)
                    if DJ.objects.filter(event=request.event, email__iexact=email).exists():
                        skipped += 1
                        continue

                    try:
                        half_price_quota = int(row.get('half_price_quota', '5').strip() or '5')
                    except ValueError:
                        half_price_quota = 5

                    try:
                        free_quota = int(row.get('free_quota', '10').strip() or '10')
                    except ValueError:
                        free_quota = 10

                    DJ.objects.create(
                        event=request.event,
                        name=name,
                        email=email,
                        half_price_quota=half_price_quota,
                        free_quota=free_quota,
                    )
                    created += 1

            if created:
                messages.success(request, _('Successfully imported {count} DJs.').format(count=created))
            if skipped:
                messages.info(request, _('Skipped {count} duplicate emails.').format(count=skipped))
            if errors:
                messages.warning(request, ' | '.join(str(e) for e in errors))

        except Exception as e:
            logger.warning('CSV import failed: %s', e)
            messages.error(request, _('Error reading CSV file.'))

        return redirect(redirect_url)
