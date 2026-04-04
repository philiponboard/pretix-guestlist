import logging

from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from pretix.base.signals import order_canceled, order_paid, periodic_task, register_data_exporters
from pretix.control.signals import nav_event

logger = logging.getLogger(__name__)


@receiver(nav_event, dispatch_uid='guestlist_nav_event')
def navbar_info(sender, request, **kwargs):
    url = resolve(request.path_info)
    return [{
        'label': _('Guest List'),
        'url': reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
        }),
        'active': url.namespace == 'plugins:pretix_guestlist',
        'icon': 'users',
    }]


@receiver(register_data_exporters, dispatch_uid='guestlist_exporters')
def register_exporter(sender, **kwargs):
    from .exporters import GuestListExporter
    return GuestListExporter


@receiver(order_paid, dispatch_uid='guestlist_order_paid')
def on_order_paid(sender, order, **kwargs):
    """When an order is paid, update matching guest status to 'registered'."""
    from .models import Guest

    if not order.email:
        return

    guests = Guest.objects.filter(
        dj__event=sender,
        email__iexact=order.email,
        status=Guest.STATUS_INVITED,
    )
    updated = guests.update(status=Guest.STATUS_REGISTERED, order=order)
    if updated:
        position = order.positions.first()
        if position:
            Guest.objects.filter(
                dj__event=sender,
                email__iexact=order.email,
                status=Guest.STATUS_REGISTERED,
                order=order,
                order_position__isnull=True,
            ).update(order_position=position)
        logger.info('Guest status updated to registered for order %s (%d guests)', order.code, updated)


@receiver(order_canceled, dispatch_uid='guestlist_order_canceled')
def on_order_canceled(sender, order, **kwargs):
    """When an order is canceled, reset guest status."""
    from .models import Guest

    guests = Guest.objects.filter(order=order)
    updated = guests.update(status=Guest.STATUS_INVITED, order=None, order_position=None)
    if updated:
        logger.info('Guest status reset for canceled order %s (%d guests)', order.code, updated)


@receiver(periodic_task, dispatch_uid='guestlist_periodic_reminders')
def send_periodic_reminders(sender, **kwargs):
    """Periodically check for events and send reminder emails to unregistered guests."""
    from .tasks import process_reminder_emails

    try:
        process_reminder_emails()
    except Exception as e:
        logger.warning('Failed to process reminder emails: %s', e)


try:
    from pretix.base.signals import checkin_created

    @receiver(checkin_created, dispatch_uid='guestlist_checkin_created')
    def on_checkin_created(sender, checkin, **kwargs):
        """When a check-in happens, update guest status to 'checked_in'."""
        from .models import Guest

        position = checkin.position
        guests = Guest.objects.filter(order_position=position)
        updated = guests.update(status=Guest.STATUS_CHECKED_IN)
        if updated:
            logger.info('Guest checked in for position %s (%d guests)', position.pk, updated)
except ImportError:
    pass
