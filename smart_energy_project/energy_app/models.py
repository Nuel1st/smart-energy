from django.db import models

from django.contrib.auth.models import User
import uuid

class Device(models.Model):
    DEVICE_TYPES = [
        ('AC', 'Air Conditioner'),
        ('FRIDGE', 'Refrigerator'),
        ('LIGHT', 'Lighting'),
        ('FAN', 'Fan'),
        ('TV', 'Television'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    power_rating = models.FloatField(help_text="Power rating in Watts")
    status = models.BooleanField(default=False)  # on/off
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

class EnergyReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    power_usage = models.FloatField(help_text="Watts used")
    energy_consumed = models.FloatField(help_text="Wh consumed")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.device.name}: {self.energy_consumed}Wh at {self.timestamp}"

class UserThreshold(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_threshold = models.FloatField(default=10.0, help_text="kWh per day")
    weekly_threshold = models.FloatField(default=70.0, help_text="kWh per week")



