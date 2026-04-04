import pytest
from pretix_guestlist.models import DJ, Guest, GuestListSettings


@pytest.mark.django_db
class TestDJQuotas:
    def test_half_price_invited_count_empty(self, dj):
        assert dj.half_price_invited_count == 0

    def test_half_price_invited_count(self, dj):
        Guest.objects.create(dj=dj, email='a@x.com', ticket_type=Guest.TICKET_HALF)
        Guest.objects.create(dj=dj, email='b@x.com', ticket_type=Guest.TICKET_HALF)
        Guest.objects.create(dj=dj, email='c@x.com', ticket_type=Guest.TICKET_FREE)
        assert dj.half_price_invited_count == 2

    def test_half_price_free_slots(self, dj):
        assert dj.half_price_free_slots == 3  # quota=3, used=0
        # used_half_price_slots excludes STATUS_INVITED, so need registered guest
        Guest.objects.create(dj=dj, email='a@x.com', ticket_type=Guest.TICKET_HALF,
                             status=Guest.STATUS_REGISTERED)
        dj.refresh_from_db()
        assert dj.half_price_free_slots == 2

    def test_free_invited_count(self, dj):
        Guest.objects.create(dj=dj, email='a@x.com', ticket_type=Guest.TICKET_FREE)
        Guest.objects.create(dj=dj, email='b@x.com', ticket_type=Guest.TICKET_FREE)
        assert dj.free_invited_count == 2

    def test_free_free_slots(self, dj):
        assert dj.free_free_slots == 5  # quota=5, used=0
        for i in range(5):
            Guest.objects.create(dj=dj, email=f'{i}@x.com', ticket_type=Guest.TICKET_FREE)
        dj.refresh_from_db()
        assert dj.free_free_slots == 0


@pytest.mark.django_db
class TestGuest:
    def test_str_with_name(self, dj):
        g = Guest.objects.create(dj=dj, email='a@x.com', first_name='Max', last_name='Muster')
        assert str(g) == 'Max Muster'

    def test_str_without_name(self, dj):
        g = Guest.objects.create(dj=dj, email='a@x.com')
        assert str(g) == 'a@x.com'

    def test_default_status(self, dj):
        g = Guest.objects.create(dj=dj, email='a@x.com')
        assert g.status == Guest.STATUS_INVITED

    def test_guest_token_generated(self, dj):
        g = Guest.objects.create(dj=dj, email='a@x.com')
        assert len(g.guest_token) == 32

    def test_guest_tokens_unique(self, dj):
        g1 = Guest.objects.create(dj=dj, email='a@x.com')
        g2 = Guest.objects.create(dj=dj, email='b@x.com')
        assert g1.guest_token != g2.guest_token


@pytest.mark.django_db
class TestGuestListSettings:
    def test_get_product_for_ticket_type(self, guestlist_settings, product_full, product_half, product_free):
        assert guestlist_settings.get_product_for_ticket_type(Guest.TICKET_FULL) == product_full
        assert guestlist_settings.get_product_for_ticket_type(Guest.TICKET_HALF) == product_half
        assert guestlist_settings.get_product_for_ticket_type(Guest.TICKET_FREE) == product_free
        assert guestlist_settings.get_product_for_ticket_type('invalid') is None
