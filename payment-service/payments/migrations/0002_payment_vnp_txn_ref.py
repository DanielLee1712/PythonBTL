from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='vnp_txn_ref',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
