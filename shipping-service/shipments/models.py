from django.db import models


class Shipment(models.Model):
    order_id = models.BigIntegerField(unique=True, db_index=True)
    user_id = models.BigIntegerField()
    status = models.CharField(max_length=32, default='created')
    tracking_code = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
