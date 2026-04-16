from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Device, EnergyReading, UserThreshold

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

# class EnergyReadingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EnergyReading
#         fields = '__all__'

class EnergyReadingSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    energy_consumed = serializers.FloatField()

    class Meta:
        model = EnergyReading
        fields = ['id', 'timestamp', 'energy_consumed']

class UserThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserThreshold
        fields = '__all__'