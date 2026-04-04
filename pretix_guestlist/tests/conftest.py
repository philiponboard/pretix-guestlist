import pytest
from decimal import Decimal


@pytest.fixture(autouse=True)
def _staticfiles_settings(settings):
    """Use simple static file storage in tests to avoid manifest errors."""
    settings.STORAGES = {
        **getattr(settings, 'STORAGES', {}),
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_OFFLINE = False


@pytest.fixture(autouse=True)
def _scopes_disabled():
    """Disable django-scopes for all tests."""
    from django_scopes import scopes_disabled
    with scopes_disabled():
        yield


@pytest.fixture
def organizer(db):
    from pretix.base.models import Organizer
    return Organizer.objects.create(name='Test Organizer', slug='test')


@pytest.fixture
def event(organizer):
    from pretix.base.models import Event
    from django.utils.timezone import now, timedelta
    event = Event.objects.create(
        organizer=organizer,
        name='Test Event',
        slug='testevent',
        date_from=now() + timedelta(days=30),
        live=True,
    )
    event.settings.locale = 'en'
    event.plugins = 'pretix_guestlist'
    event.save(update_fields=['plugins'])
    return event


@pytest.fixture
def sales_channel(organizer):
    from pretix.base.models import SalesChannel
    sc, _ = SalesChannel.objects.get_or_create(
        organizer=organizer,
        identifier='web',
        defaults={'name': 'Web', 'type': 'web'},
    )
    return sc


@pytest.fixture
def product_full(event):
    from pretix.base.models import Item
    return Item.objects.create(
        event=event, name='Full Price', default_price=Decimal('100.00'), active=True,
    )


@pytest.fixture
def product_half(event):
    from pretix.base.models import Item
    return Item.objects.create(
        event=event, name='Half Price', default_price=Decimal('50.00'), active=True,
    )


@pytest.fixture
def product_free(event):
    from pretix.base.models import Item
    return Item.objects.create(
        event=event, name='Free', default_price=Decimal('0.00'), active=True,
    )


@pytest.fixture
def guestlist_settings(event, product_full, product_half, product_free):
    from pretix_guestlist.models import GuestListSettings
    return GuestListSettings.objects.create(
        event=event,
        product_full=product_full,
        product_half=product_half,
        product_free=product_free,
    )


@pytest.fixture
def dj(event):
    from pretix_guestlist.models import DJ
    return DJ.objects.create(
        event=event,
        name='Test DJ',
        email='dj@example.com',
        half_price_quota=3,
        free_quota=5,
    )


@pytest.fixture
def guest(dj):
    from pretix_guestlist.models import Guest
    return Guest.objects.create(
        dj=dj,
        email='guest@example.com',
        ticket_type=Guest.TICKET_FREE,
        status=Guest.STATUS_INVITED,
    )
