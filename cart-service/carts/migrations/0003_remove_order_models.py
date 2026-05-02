from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('carts', '0002_order_orderitem'),
    ]

    operations = [
        migrations.DeleteModel(name='OrderItem'),
        migrations.DeleteModel(name='Order'),
    ]
