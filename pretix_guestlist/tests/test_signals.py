import pytest
from decimal import Decimal
from pretix_guestlist.models import Guest


@pytest.mark.django_db
class TestOrderPaidSignal:
    def test_order_paid_updates_guest(self, dj, guest, event, sales_channel):
        from pretix.base.models import Order, OrderPosition
        from pretix_guestlist.signals import on_order_paid

        order = Order.objects.create(
            event=event, email='guest@example.com',
            status=Order.STATUS_PAID, total=Decimal('0.00'),
            sales_channel=sales_channel,
        )
        on_order_paid(sender=event, order=order)

        guest.refresh_from_db()
        assert guest.status == Guest.STATUS_REGISTERED
        assert guest.order == order

    def test_order_paid_no_match(self, dj, guest, event, sales_channel):
        from pretix.base.models import Order
        from pretix_guestlist.signals import on_order_paid

        order = Order.objects.create(
            event=event, email='other@example.com',
            status=Order.STATUS_PAID, total=Decimal('0.00'),
            sales_channel=sales_channel,
        )
        on_order_paid(sender=event, order=order)

        guest.refresh_from_db()
        assert guest.status == Guest.STATUS_INVITED


@pytest.mark.django_db
class TestOrderCanceledSignal:
    def test_order_canceled_resets_guest(self, dj, guest, event, sales_channel):
        from pretix.base.models import Order
        from pretix_guestlist.signals import on_order_canceled

        order = Order.objects.create(
            event=event, email='guest@example.com',
            status=Order.STATUS_PAID, total=Decimal('0.00'),
            sales_channel=sales_channel,
        )
        guest.status = Guest.STATUS_REGISTERED
        guest.order = order
        guest.save()

        on_order_canceled(sender=event, order=order)

        guest.refresh_from_db()
        assert guest.status == Guest.STATUS_INVITED
        assert guest.order is None
