import logging

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def send_dj_invitation(dj_id):
    """Send invitation email to a single DJ with guest list links per ticket type."""
    from django_scopes import scopes_disabled

    with scopes_disabled():
        from .models import DJ, Guest, GuestListSettings

        dj = DJ.objects.select_related('event', 'event__organizer').get(pk=dj_id)
        event = dj.event
        settings = GuestListSettings.objects.filter(event=event).first()

        if not settings:
            logger.warning('No GuestListSettings for event %s, cannot send invitation to DJ %s', event.slug, dj.name)
            return

        from django.conf import settings as django_settings
        base_url = django_settings.SITE_URL.rstrip('/')

        dashboard_link = '{base}/{organizer}/{event}/gl/{token}/'.format(
            base=base_url,
            organizer=event.organizer.slug,
            event=event.slug,
            token=dj.token,
        )

        # Build guest self-add links for each configured ticket type
        guest_links = []
        link_configs = [
            (Guest.TICKET_FULL, settings.product_full, str(_('Full Price')), None),
            (Guest.TICKET_HALF, settings.product_half, str(_('Half Price')), dj.half_price_quota),
            (Guest.TICKET_FREE, settings.product_free, str(_('Free')), dj.free_quota),
        ]
        for ticket_type, product, label, quota in link_configs:
            if product:
                link = '{base}/{organizer}/{event}/gl/{token}/add/{ticket_type}/'.format(
                    base=base_url,
                    organizer=event.organizer.slug,
                    event=event.slug,
                    token=dj.token,
                    ticket_type=ticket_type,
                )
                if quota is not None:
                    guest_links.append('{label} ({quota} {spots}): {link}'.format(
                        label=label, quota=quota, spots=str(_('spots')), link=link,
                    ))
                else:
                    guest_links.append('{label}: {link}'.format(label=label, link=link))

        guest_links_text = '\n'.join(guest_links)

        context = {
            'dj_name': dj.name,
            'quota': str(dj.half_price_quota),
            'link': dashboard_link,
            'event_name': str(event.name),
            'guest_links': guest_links_text,
            'dashboard_link': dashboard_link,
        }

        subject = str(settings.mail_subject).format(**context)
        body = str(settings.mail_template).format(**context)

        sender = event.settings.get('mail_from', default='noreply@example.com')

        from pretix.base.services.mail import mail_send
        mail_send(
            to=[dj.email],
            subject=subject,
            body=body,
            html=None,
            sender=sender,
            event=event,
        )

        dj.invitation_sent = True
        dj.invitation_sent_at = now()
        dj.save(update_fields=['invitation_sent', 'invitation_sent_at'])

        logger.info('Invitation sent to DJ "%s" (%s) for event %s', dj.name, dj.email, event.slug)


def send_guest_invitation(guest_id):
    """Send invitation email to a guest added by a DJ."""
    from django_scopes import scopes_disabled

    with scopes_disabled():
        from .models import Guest, GuestListSettings

        guest = Guest.objects.select_related('dj', 'dj__event', 'dj__event__organizer').get(pk=guest_id)
        dj = guest.dj
        event = dj.event

        from django.conf import settings as django_settings
        base_url = django_settings.SITE_URL.rstrip('/')
        link = '{base}/{organizer}/{event}/gl/{dj_token}/r/{guest_token}/'.format(
            base=base_url,
            organizer=event.organizer.slug,
            event=event.slug,
            dj_token=dj.token,
            guest_token=guest.guest_token,
        )

        context = {
            'guest_email': guest.email,
            'dj_name': dj.name,
            'event_name': str(event.name),
            'link': link,
            'ticket_type': guest.get_ticket_type_display(),
        }

        subject = str(_('You are on the guest list for {event_name}')).format(**context)
        body = str(_(
            'Hello,\n\n'
            '{dj_name} has put you on the guest list for {event_name}.\n'
            'Ticket type: {ticket_type}\n\n'
            'Please complete your registration here:\n{link}\n\n'
            'Best regards,\nThe {event_name} Team'
        )).format(**context)

        sender = event.settings.get('mail_from', default='noreply@example.com')

        from pretix.base.services.mail import mail_send
        mail_send(
            to=[guest.email],
            subject=subject,
            body=body,
            html=None,
            sender=sender,
            event=event,
        )

        logger.info('Guest invitation sent to "%s" for DJ "%s"', guest.email, dj.name)


def send_guest_reminder(guest_id):
    """Send a reminder email to a guest who has not yet registered."""
    from django_scopes import scopes_disabled

    with scopes_disabled():
        from .models import Guest, GuestListSettings

        guest = Guest.objects.select_related('dj', 'dj__event', 'dj__event__organizer').get(pk=guest_id)
        dj = guest.dj
        event = dj.event

        from django.conf import settings as django_settings
        base_url = django_settings.SITE_URL.rstrip('/')
        link = '{base}/{organizer}/{event}/gl/{dj_token}/r/{guest_token}/'.format(
            base=base_url,
            organizer=event.organizer.slug,
            event=event.slug,
            dj_token=dj.token,
            guest_token=guest.guest_token,
        )

        context = {
            'guest_email': guest.email,
            'dj_name': dj.name,
            'event_name': str(event.name),
            'link': link,
            'ticket_type': guest.get_ticket_type_display(),
        }

        subject = str(_('Reminder: You are on the guest list for {event_name}')).format(**context)
        body = str(_(
            'Hello,\n\n'
            'This is a friendly reminder that {dj_name} has put you on the guest list '
            'for {event_name}, but you have not yet completed your registration.\n\n'
            'Ticket type: {ticket_type}\n\n'
            'Please complete your registration here:\n{link}\n\n'
            'Best regards,\nThe {event_name} Team'
        )).format(**context)

        sender = event.settings.get('mail_from', default='noreply@example.com')

        from pretix.base.services.mail import mail_send
        mail_send(
            to=[guest.email],
            subject=subject,
            body=body,
            html=None,
            sender=sender,
            event=event,
        )

        logger.info('Reminder sent to guest "%s" for event %s', guest.email, event.slug)


def process_reminder_emails():
    """Check all events and send reminders 7 and 2 days before the event."""
    from django_scopes import scopes_disabled

    with scopes_disabled():
        from datetime import timedelta
        from pretix.base.models import Event
        from .models import Guest, GuestListSettings

        today = now().date()

        events = Event.objects.filter(
            date_from__gt=now(),
            live=True,
        ).select_related('organizer')

        for event in events:
            # Check if reminders are enabled
            settings = GuestListSettings.objects.filter(event=event).first()
            if not settings or not settings.send_reminders:
                continue

            event_date = event.date_from.date()
            days_until = (event_date - today).days

            if days_until not in (7, 2):
                continue

            guests = Guest.objects.filter(
                dj__event=event,
                status=Guest.STATUS_INVITED,
                reminder_count__lt=2,
            )

            sent_count = 0
            for guest in guests:
                try:
                    send_guest_reminder(guest.pk)
                    guest.reminder_count += 1
                    guest.save(update_fields=['reminder_count'])
                    sent_count += 1
                except Exception as e:
                    logger.warning('Failed to send reminder to %s: %s', guest.email, e)

            if sent_count:
                logger.info(
                    'Sent %d reminder emails for event %s (%d days before)',
                    sent_count, event.slug, days_until,
                )
