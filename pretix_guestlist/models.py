from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


class GuestListSettings(models.Model):
    event = models.OneToOneField(
        'pretixbase.Event',
        on_delete=models.CASCADE,
        related_name='guestlist_settings',
    )
    product_full = models.ForeignKey(
        'pretixbase.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guestlist_full',
        verbose_name=_('Full Price Product'),
    )
    product_half = models.ForeignKey(
        'pretixbase.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guestlist_half',
        verbose_name=_('Half Price Product'),
    )
    product_free = models.ForeignKey(
        'pretixbase.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guestlist_free',
        verbose_name=_('Free Product'),
    )
    hide_products = models.BooleanField(
        default=True,
        verbose_name=_('Hide products from shop'),
        help_text=_('Automatically hide guest list products from the normal shop. '
                     'Guests can only access them via their personal link.'),
    )
    send_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Send reminder emails'),
        help_text=_('Automatically send reminder emails to guests who have not registered yet '
                     '(7 days and 2 days before the event).'),
    )
    mail_subject = models.CharField(
        max_length=255,
        default=_('Your guest list for {event_name}'),
        verbose_name=_('E-Mail subject'),
    )
    mail_template = models.TextField(
        default=_(
            'Hello {dj_name},\n\n'
            'you have {quota} half-price guest list spots for {event_name}.\n\n'
            'Share this link with your guests:\n{link}\n\n'
            'Your guests can register themselves and will receive their ticket via e-mail.\n\n'
            'Best regards,\nThe {event_name} Team'
        ),
        verbose_name=_('E-Mail template'),
    )
    registration_text = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Registration page text'),
    )

    class Meta:
        app_label = 'pretix_guestlist'
        verbose_name = _('Guest list settings')

    def __str__(self):
        return f'GuestListSettings for {self.event}'

    def get_product_for_ticket_type(self, ticket_type):
        """Return the product matching the given ticket type."""
        return {
            Guest.TICKET_FULL: self.product_full,
            Guest.TICKET_HALF: self.product_half,
            Guest.TICKET_FREE: self.product_free,
        }.get(ticket_type)


def _generate_token():
    return get_random_string(32)


class DJ(models.Model):
    event = models.ForeignKey(
        'pretixbase.Event',
        on_delete=models.CASCADE,
        related_name='guestlist_djs',
    )
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    email = models.EmailField(verbose_name=_('E-Mail'))
    half_price_quota = models.PositiveIntegerField(default=5, verbose_name=_('Half-Price Quota'))
    free_quota = models.PositiveIntegerField(default=10, verbose_name=_('Free Quota'))
    token = models.CharField(
        max_length=64,
        unique=True,
        default=_generate_token,
        verbose_name=_('Token'),
    )
    invitation_sent = models.BooleanField(default=False, verbose_name=_('Invitation sent'))
    invitation_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Invitation sent at'),
    )
    notes = models.TextField(blank=True, default='', verbose_name=_('Notes'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))

    class Meta:
        app_label = 'pretix_guestlist'
        verbose_name = _('DJ')
        verbose_name_plural = _('DJs')
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def used_half_price_slots(self):
        """Count half-price guests that have been invited (and not canceled)."""
        return self.guests.filter(
            ticket_type=Guest.TICKET_HALF,
        ).exclude(status=Guest.STATUS_INVITED).count()

    @property
    def half_price_free_slots(self):
        return max(0, self.half_price_quota - self.used_half_price_slots)

    @property
    def half_price_invited_count(self):
        """Count all half-price guests (including just invited)."""
        return self.guests.filter(ticket_type=Guest.TICKET_HALF).count()

    @property
    def free_invited_count(self):
        """Count all free guests (including just invited)."""
        return self.guests.filter(ticket_type=Guest.TICKET_FREE).count()

    @property
    def free_free_slots(self):
        return max(0, self.free_quota - self.free_invited_count)


class Guest(models.Model):
    TICKET_FULL = 'full_price'
    TICKET_HALF = 'half_price'
    TICKET_FREE = 'free'
    TICKET_CHOICES = [
        (TICKET_FULL, _('Full Price')),
        (TICKET_HALF, _('Half Price')),
        (TICKET_FREE, _('Free')),
    ]

    STATUS_INVITED = 'invited'
    STATUS_REGISTERED = 'registered'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_CHOICES = [
        (STATUS_INVITED, _('Invited')),
        (STATUS_REGISTERED, _('Registered')),
        (STATUS_CHECKED_IN, _('Checked in')),
    ]

    dj = models.ForeignKey(
        DJ,
        on_delete=models.CASCADE,
        related_name='guests',
    )
    first_name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, blank=True, default='', verbose_name=_('Last name'))
    email = models.EmailField(verbose_name=_('E-Mail'))
    ticket_type = models.CharField(
        max_length=20,
        choices=TICKET_CHOICES,
        default=TICKET_FREE,
        verbose_name=_('Ticket type'),
    )
    guest_token = models.CharField(
        max_length=64,
        unique=True,
        default=_generate_token,
        verbose_name=_('Guest token'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_INVITED,
        verbose_name=_('Status'),
    )
    voucher = models.ForeignKey(
        'pretixbase.Voucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Voucher'),
    )
    order = models.ForeignKey(
        'pretixbase.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    order_position = models.ForeignKey(
        'pretixbase.OrderPosition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reminder_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Reminders sent'),
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Registered at'))

    class Meta:
        app_label = 'pretix_guestlist'
        verbose_name = _('Guest')
        verbose_name_plural = _('Guests')

    def __str__(self):
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'.strip()
        return self.email
