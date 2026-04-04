import pytest
from pretix_guestlist.forms import DJAddGuestForm, GuestRegistrationForm
from pretix_guestlist.models import Guest


class TestDJAddGuestForm:
    def test_valid(self):
        form = DJAddGuestForm(data={
            'email': 'test@example.com',
            'ticket_type': Guest.TICKET_FREE,
        })
        assert form.is_valid()

    def test_missing_email(self):
        form = DJAddGuestForm(data={
            'email': '',
            'ticket_type': Guest.TICKET_FREE,
        })
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_invalid_ticket_type(self):
        form = DJAddGuestForm(data={
            'email': 'test@example.com',
            'ticket_type': 'invalid',
        })
        assert not form.is_valid()
        assert 'ticket_type' in form.errors


class TestGuestRegistrationForm:
    def test_valid(self):
        form = GuestRegistrationForm(data={
            'first_name': 'Max',
            'last_name': 'Muster',
            'email': 'max@example.com',
        })
        assert form.is_valid()

    def test_missing_first_name(self):
        form = GuestRegistrationForm(data={
            'first_name': '',
            'last_name': 'Muster',
            'email': 'max@example.com',
        })
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_missing_email(self):
        form = GuestRegistrationForm(data={
            'first_name': 'Max',
            'last_name': 'Muster',
            'email': '',
        })
        assert not form.is_valid()
        assert 'email' in form.errors
