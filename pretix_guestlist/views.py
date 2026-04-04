from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from pretix.control.permissions import EventPermissionRequiredMixin

from .forms import DJForm, SettingsForm
from .models import DJ, GuestListSettings
from .tasks import send_dj_invitation


class GuestListSettingsView(EventPermissionRequiredMixin, UpdateView):
    permission = 'can_change_event_settings'
    template_name = 'pretix_guestlist/settings.html'
    form_class = SettingsForm

    def get_object(self, queryset=None):
        obj, _ = GuestListSettings.objects.get_or_create(event=self.request.event)
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = self.request.event
        return kwargs

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:settings', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })

    def form_valid(self, form):
        messages.success(self.request, _('Settings saved.'))
        return super().form_valid(form)


class DJListView(EventPermissionRequiredMixin, ListView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_list.html'
    context_object_name = 'djs'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)


class DJCreateView(EventPermissionRequiredMixin, CreateView):
    permission = 'can_change_event_settings'
    model = DJ
    form_class = DJForm
    template_name = 'pretix_guestlist/dj_form.html'

    def form_valid(self, form):
        form.instance.event = self.request.event
        messages.success(self.request, _('DJ created.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class DJUpdateView(EventPermissionRequiredMixin, UpdateView):
    permission = 'can_change_event_settings'
    model = DJ
    form_class = DJForm
    template_name = 'pretix_guestlist/dj_form.html'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_success_url(self):
        return reverse('plugins:pretix_guestlist:dj.detail', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
            'pk': self.object.pk,
        })

    def form_valid(self, form):
        messages.success(self.request, _('DJ updated.'))
        return super().form_valid(form)


class DJDetailView(EventPermissionRequiredMixin, DetailView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_detail.html'
    context_object_name = 'dj'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['guests'] = self.object.guests.select_related('order').all()
        return ctx


class DJDeleteView(EventPermissionRequiredMixin, DeleteView):
    permission = 'can_change_event_settings'
    model = DJ
    template_name = 'pretix_guestlist/dj_delete.html'

    def get_queryset(self):
        return DJ.objects.filter(event=self.request.event)

    def get_success_url(self):
        messages.success(self.request, _('DJ deleted.'))
        return reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': self.request.event.organizer.slug,
            'event': self.request.event.slug,
        })


class SendInvitationView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        dj = get_object_or_404(DJ, pk=kwargs['pk'], event=request.event)
        send_dj_invitation(dj.pk)
        messages.success(request, _('Invitation sent to {name}.').format(name=dj.name))
        return redirect(reverse('plugins:pretix_guestlist:dj.detail', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
            'pk': dj.pk,
        }))


class SendAllInvitationsView(EventPermissionRequiredMixin, View):
    permission = 'can_change_event_settings'

    def post(self, request, *args, **kwargs):
        djs = DJ.objects.filter(event=request.event, invitation_sent=False)
        count = 0
        for dj in djs:
            send_dj_invitation(dj.pk)
            count += 1
        if count:
            messages.success(request, _('Invitations sent to {count} DJs.').format(count=count))
        else:
            messages.info(request, _('All invitations have already been sent.'))
        return redirect(reverse('plugins:pretix_guestlist:index', kwargs={
            'organizer': request.event.organizer.slug,
            'event': request.event.slug,
        }))
