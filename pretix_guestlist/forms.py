from django import forms
from django.utils.translation import gettext_lazy as _

from .models import DJ, Guest, GuestListSettings


class DJForm(forms.ModelForm):
    class Meta:
        model = DJ
        fields = ['name', 'email', 'half_price_quota', 'free_quota', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SettingsForm(forms.ModelForm):
    product_full = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Full Price Product'),
    )
    product_half = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Half Price Product'),
    )
    product_free = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Free Product'),
    )

    class Meta:
        model = GuestListSettings
        fields = [
            'product_full', 'product_half', 'product_free',
            'hide_products', 'send_reminders',
            'mail_subject', 'mail_template', 'registration_text',
        ]
        widgets = {
            'mail_template': forms.Textarea(attrs={'rows': 10}),
            'registration_text': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, event=None, **kwargs):
        self._event = event
        super().__init__(*args, **kwargs)
        if event:
            qs = event.items.all()
            self.fields['product_full'].queryset = qs
            self.fields['product_half'].queryset = qs
            self.fields['product_free'].queryset = qs

    def save(self, commit=True):
        instance = super().save(commit=commit)

        # Auto-set hide_without_voucher + require_voucher on selected products
        if instance.hide_products:
            for product in [instance.product_full, instance.product_half, instance.product_free]:
                if product and (not product.hide_without_voucher or not product.require_voucher):
                    product.hide_without_voucher = True
                    product.require_voucher = True
                    product.save(update_fields=['hide_without_voucher', 'require_voucher'])

        return instance


class DJAddGuestForm(forms.Form):
    email = forms.EmailField(
        label=_('E-Mail'),
        widget=forms.EmailInput(attrs={'class': 'gl-input', 'placeholder': _('guest@example.com')}),
    )
    ticket_type = forms.ChoiceField(
        choices=Guest.TICKET_CHOICES,
        label=_('Ticket type'),
        widget=forms.Select(attrs={'class': 'gl-input'}),
    )


class GuestRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=255,
        label=_('First name'),
        widget=forms.TextInput(attrs={'class': 'gl-input', 'placeholder': _('First name')}),
    )
    last_name = forms.CharField(
        max_length=255,
        label=_('Last name'),
        widget=forms.TextInput(attrs={'class': 'gl-input', 'placeholder': _('Last name')}),
    )
    email = forms.EmailField(
        label=_('E-Mail'),
        widget=forms.EmailInput(attrs={'class': 'gl-input', 'placeholder': _('E-Mail')}),
    )
