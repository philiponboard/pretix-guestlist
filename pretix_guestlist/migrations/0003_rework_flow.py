from django.db import migrations, models
import django.db.models.deletion
from django.utils.crypto import get_random_string


def migrate_data(apps, schema_editor):
    """Migrate existing data to new schema."""
    GuestListSettings = apps.get_model('pretix_guestlist', 'GuestListSettings')
    DJ = apps.get_model('pretix_guestlist', 'DJ')
    Guest = apps.get_model('pretix_guestlist', 'Guest')

    # Copy old product to product_free
    for s in GuestListSettings.objects.all():
        if s.product_id:
            s.product_free_id = s.product_id
            s.save(update_fields=['product_free_id'])

    # Copy quota to half_price_quota
    for dj in DJ.objects.all():
        dj.half_price_quota = dj.quota
        dj.save(update_fields=['half_price_quota'])

    # Give existing guests a guest_token and ticket_type
    for guest in Guest.objects.all():
        guest.guest_token = get_random_string(32)
        guest.ticket_type = 'free'
        # Map old statuses to new
        if guest.status == 'paid':
            guest.status = 'registered'
        elif guest.status not in ('invited', 'registered', 'checked_in'):
            guest.status = 'registered'
        guest.save(update_fields=['guest_token', 'ticket_type', 'status'])


class Migration(migrations.Migration):

    dependencies = [
        ('pretixbase', '__latest__'),
        ('pretix_guestlist', '0002_guest_invited_by_dj_guest_status'),
    ]

    operations = [
        # --- GuestListSettings: add 3 product fields ---
        migrations.AddField(
            model_name='guestlistsettings',
            name='product_full',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='guestlist_full', to='pretixbase.item',
                verbose_name='Full Price Product',
            ),
        ),
        migrations.AddField(
            model_name='guestlistsettings',
            name='product_half',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='guestlist_half', to='pretixbase.item',
                verbose_name='Half Price Product',
            ),
        ),
        migrations.AddField(
            model_name='guestlistsettings',
            name='product_free',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='guestlist_free', to='pretixbase.item',
                verbose_name='Free Product',
            ),
        ),

        # --- DJ: add half_price_quota ---
        migrations.AddField(
            model_name='dj',
            name='half_price_quota',
            field=models.PositiveIntegerField(default=5, verbose_name='Half-Price Quota'),
        ),

        # --- Guest: add ticket_type and guest_token ---
        migrations.AddField(
            model_name='guest',
            name='ticket_type',
            field=models.CharField(default='free', max_length=20, verbose_name='Ticket type'),
        ),
        migrations.AddField(
            model_name='guest',
            name='guest_token',
            field=models.CharField(default='temp', max_length=64, verbose_name='Guest token'),
        ),

        # --- Allow blank first_name/last_name ---
        migrations.AlterField(
            model_name='guest',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='First name'),
        ),
        migrations.AlterField(
            model_name='guest',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Last name'),
        ),

        # --- Make email required (not blank) ---
        migrations.AlterField(
            model_name='guest',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='E-Mail'),
        ),

        # --- Data migration ---
        migrations.RunPython(migrate_data, migrations.RunPython.noop),

        # --- Make guest_token unique after data migration ---
        migrations.AlterField(
            model_name='guest',
            name='guest_token',
            field=models.CharField(default='temp', max_length=64, unique=True, verbose_name='Guest token'),
        ),

        # --- Remove old fields ---
        migrations.RemoveField(model_name='guestlistsettings', name='product'),
        migrations.RemoveField(model_name='guestlistsettings', name='require_email'),
        migrations.RemoveField(model_name='dj', name='quota'),
        migrations.RemoveField(model_name='guest', name='invited_by_dj'),
    ]
