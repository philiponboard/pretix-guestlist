import io

from django.utils.translation import gettext_lazy as _
from pretix.base.exporter import BaseExporter


class GuestListExporter(BaseExporter):
    identifier = 'guestlist'
    verbose_name = _('Guest List (CSV)')

    def render(self, form_data, output_file=None):
        import csv

        buf = output_file or io.StringIO()
        writer = csv.writer(buf)

        writer.writerow([
            str(_('DJ')),
            str(_('First name')),
            str(_('Last name')),
            str(_('E-Mail')),
            str(_('Ticket type')),
            str(_('Status')),
            str(_('Registered')),
            str(_('Order')),
            str(_('Voucher code')),
        ])

        from .models import DJ
        for dj in DJ.objects.filter(event=self.event).prefetch_related(
            'guests', 'guests__order', 'guests__voucher',
        ):
            for guest in dj.guests.all():
                writer.writerow([
                    dj.name,
                    guest.first_name,
                    guest.last_name,
                    guest.email,
                    guest.get_ticket_type_display(),
                    guest.get_status_display(),
                    guest.registered_at.isoformat() if guest.registered_at else '',
                    guest.order.code if guest.order else '',
                    guest.voucher.code if guest.voucher else '',
                ])

        if output_file:
            return self.identifier + '.csv', 'text/csv', buf
        return self.identifier + '.csv', 'text/csv', buf.getvalue()
