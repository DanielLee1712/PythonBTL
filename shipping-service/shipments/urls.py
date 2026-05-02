from django.urls import path

from .views import ShipmentCreateView

urlpatterns = [
    path('shipments/', ShipmentCreateView.as_view(), name='shipment-create'),
]
