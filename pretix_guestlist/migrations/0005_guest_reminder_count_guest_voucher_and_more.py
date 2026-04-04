import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretix_guestlist', '0004_alter_guest_guest_token_alter_guest_status_and_more'),
        ('pretixbase', '__latest__'),
    ]

    operations = [
        migrations.AddField(
            model_name='guest',
            name='reminder_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='guest',
            name='voucher',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='pretixbase.voucher',
            ),
        ),
        migrations.AddField(
            model_name='guestlistsettings',
            name='hide_products',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='guestlistsettings',
            name='send_reminders',
            field=models.BooleanField(default=True),
        ),
    ]
