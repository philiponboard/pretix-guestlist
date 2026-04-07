from django.urls import re_path

from . import views
from .registration_views import DJDashboardView, GuestRegistrationView, GuestSelfAddView

# Control Panel URLs – loaded via urlpatterns (full path with /control/event/...)
urlpatterns = [
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/$',
            views.DJListView.as_view(), name='index'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/settings/$',
            views.GuestListSettingsView.as_view(), name='settings'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/create/$',
            views.DJCreateView.as_view(), name='dj.create'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/(?P<pk>[0-9]+)/$',
            views.DJDetailView.as_view(), name='dj.detail'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/(?P<pk>[0-9]+)/edit/$',
            views.DJUpdateView.as_view(), name='dj.edit'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/(?P<pk>[0-9]+)/delete/$',
            views.DJDeleteView.as_view(), name='dj.delete'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/(?P<pk>[0-9]+)/send/$',
            views.SendInvitationView.as_view(), name='dj.send'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/send-all/$',
            views.SendAllInvitationsView.as_view(), name='send_all'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/(?P<pk>[0-9]+)/guest/(?P<guest_pk>[0-9]+)/resend/$',
            views.ResendGuestInvitationView.as_view(), name='guest.resend'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/csv-template/$',
            views.CSVTemplateDownloadView.as_view(), name='csv_template'),
    re_path(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/guestlist/csv-upload/$',
            views.CSVUploadView.as_view(), name='csv_upload'),
]

# Public (Presale) URLs – loaded via event_patterns
event_patterns = [
    re_path(r'^gl/(?P<token>[a-zA-Z0-9]+)/$',
            DJDashboardView.as_view(), name='dj_dashboard'),
    re_path(r'^gl/(?P<dj_token>[a-zA-Z0-9]+)/r/(?P<guest_token>[a-zA-Z0-9]+)/$',
            GuestRegistrationView.as_view(), name='guest_register'),
    re_path(r'^gl/(?P<token>[a-zA-Z0-9]+)/add/(?P<ticket_type>full_price|half_price|free)/$',
            GuestSelfAddView.as_view(), name='guest_self_add'),
]
