import pytest
from pretix_guestlist.models import DJ, Guest, GuestListSettings


@pytest.mark.django_db
class TestDJDashboard:
    def test_dashboard_get(self, client, dj, guestlist_settings):
        url = '/{}/{}/gl/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        response = client.get(url)
        assert response.status_code == 200
        assert dj.name.encode() in response.content

    def test_dashboard_invalid_token(self, client, event):
        url = '/{}/{}/gl/invalidtoken123/'.format(
            event.organizer.slug, event.slug,
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_add_guest_full_price(self, client, dj, guestlist_settings):
        url = '/{}/{}/gl/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        response = client.post(url, {
            'action': 'add_guest',
            'email': 'new@example.com',
            'ticket_type': Guest.TICKET_FULL,
        })
        assert response.status_code == 302
        assert Guest.objects.filter(dj=dj, email='new@example.com', ticket_type=Guest.TICKET_FULL).exists()

    def test_add_guest_half_price_quota(self, client, dj, guestlist_settings):
        url = '/{}/{}/gl/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        for i in range(3):
            client.post(url, {
                'action': 'add_guest',
                'email': f'half{i}@example.com',
                'ticket_type': Guest.TICKET_HALF,
            })
        assert dj.guests.filter(ticket_type=Guest.TICKET_HALF).count() == 3

        # 4th should fail — check error box is shown
        response = client.post(url, {
            'action': 'add_guest',
            'email': 'half4@example.com',
            'ticket_type': Guest.TICKET_HALF,
        })
        assert response.status_code == 200
        assert b'gl-error-box' in response.content
        assert dj.guests.filter(ticket_type=Guest.TICKET_HALF).count() == 3

    def test_add_guest_free_quota(self, client, dj, guestlist_settings):
        url = '/{}/{}/gl/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        for i in range(5):
            client.post(url, {
                'action': 'add_guest',
                'email': f'free{i}@example.com',
                'ticket_type': Guest.TICKET_FREE,
            })
        assert dj.guests.filter(ticket_type=Guest.TICKET_FREE).count() == 5

        # 6th should fail
        response = client.post(url, {
            'action': 'add_guest',
            'email': 'free6@example.com',
            'ticket_type': Guest.TICKET_FREE,
        })
        assert response.status_code == 200
        assert b'gl-error-box' in response.content

    def test_resend(self, client, dj, guest, guestlist_settings):
        url = '/{}/{}/gl/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        response = client.post(url, {
            'action': 'resend',
            'guest_id': guest.pk,
        })
        assert response.status_code == 302


@pytest.mark.django_db
class TestGuestRegistration:
    def test_registration_page_get(self, client, dj, guest, guestlist_settings):
        url = '/{}/{}/gl/{}/r/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token, guest.guest_token,
        )
        response = client.get(url)
        assert response.status_code == 200
        assert b'guest@example.com' in response.content

    def test_registration_page_invalid_token(self, client, dj, guestlist_settings):
        url = '/{}/{}/gl/{}/r/invalidtoken123/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token,
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_register_free_creates_order(self, client, dj, guest, guestlist_settings, sales_channel):
        url = '/{}/{}/gl/{}/r/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token, guest.guest_token,
        )
        response = client.post(url, {
            'first_name': 'Max',
            'last_name': 'Muster',
            'email': 'guest@example.com',
        })
        assert response.status_code == 200
        assert b'gl-result' in response.content

        guest.refresh_from_db()
        assert guest.status == Guest.STATUS_REGISTERED
        assert guest.order is not None
        assert guest.first_name == 'Max'

    def test_register_paid_redirects(self, client, dj, guestlist_settings, sales_channel):
        guest = Guest.objects.create(
            dj=dj, email='paid@example.com',
            ticket_type=Guest.TICKET_HALF, status=Guest.STATUS_INVITED,
        )
        url = '/{}/{}/gl/{}/r/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token, guest.guest_token,
        )
        response = client.post(url, {
            'first_name': 'Paid',
            'last_name': 'Guest',
            'email': 'paid@example.com',
        })
        assert response.status_code == 302
        assert '/redeem' in response.url

    def test_already_registered(self, client, dj, guest, guestlist_settings):
        guest.status = Guest.STATUS_REGISTERED
        guest.save()

        url = '/{}/{}/gl/{}/r/{}/'.format(
            dj.event.organizer.slug, dj.event.slug, dj.token, guest.guest_token,
        )
        response = client.get(url)
        assert response.status_code == 200
        assert b'gl-result' in response.content
