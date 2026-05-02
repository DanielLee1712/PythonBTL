# Generated manually for stock tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmodel',
            name='stock_quantity',
            field=models.PositiveIntegerField(
                default=100,
                help_text='Sellable stock; decreases when items are reserved in carts / orders.',
            ),
        ),
    ]
