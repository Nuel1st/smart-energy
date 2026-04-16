
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal
from .models import Device, EnergyReading, UserThreshold
from .serializers import DeviceSerializer, EnergyReadingSerializer
from uuid import UUID
import random
    
from django.db.models import Sum

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserThreshold.objects.get_or_create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'energy_app/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'energy_app/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    devices = Device.objects.filter(user=request.user)

    today = timezone.now().date()
    readings = EnergyReading.objects.filter(
        device__user=request.user,
        timestamp__date=today
    )

    # total_wh = sum(r.energy_consumed for r in readings)

    total_wh = readings.aggregate(total=Sum('energy_consumed'))['total'] or 0
    total_daily = total_wh / 1000.0

    return render(request, 'energy_app/dashboard.html', {
        'devices': devices,
        'total_daily': round(total_daily, 2),
    })

@login_required
def devices_view(request):
    devices = Device.objects.filter(user=request.user)
    return render(request, 'energy_app/devices.html', {'devices': devices})

@login_required
@require_http_methods(["GET", "POST"])
def api_devices(request):
    if request.method == 'GET':
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)
        return JsonResponse({'devices': serializer.data})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        device = Device.objects.create(
            user=request.user,
            name=data['name'],
            device_type=data['device_type'],
            power_rating=data['power_rating'],
            status=data.get('status', False)
        )
        serializer = DeviceSerializer(device)
        return JsonResponse(serializer.data)

@login_required
@require_http_methods(["POST"])
def api_toggle_device(request, device_id):
    """✅ FIXED: Generate REAL data on toggle"""
    try:
        device = Device.objects.get(id=UUID(device_id), user=request.user)
        was_on = device.status
        device.status = not device.status
        device.save()
        
        # ✅ CREATE DATA WHEN TURNED ON
        if device.status and not was_on:  # Just turned ON
            for i in range(5):  # Create 5 readings immediately
                simulate_reading(device)
        
        return JsonResponse({'status': device.status})
    except:
        return JsonResponse({'error': 'Device not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def api_energy_data(request):
    generate_live_data(request.user)

    readings = EnergyReading.objects.filter(
        device__user=request.user
    ).order_by('-timestamp')[:20]

    serializer = EnergyReadingSerializer(readings, many=True)
    return JsonResponse({'readings': serializer.data})

def get_daily_consumption(device):
    today = timezone.now().date()
    readings = EnergyReading.objects.filter(
        device=device,
        timestamp__date=today
    )
    return sum(r.energy_consumed for r in readings) / 1000  # Convert to kWh


def simulate_reading(device):
    if not device.status:
        return
    
    power = device.power_rating * random.uniform(0.7, 1.3)
    duration_hours = random.uniform(0.05, 0.2)
    energy_wh = power * duration_hours

    EnergyReading.objects.create(
        device=device,
        power_usage=round(power, 1),
        energy_consumed=round(energy_wh, 2)
    )

@login_required
@require_http_methods(["GET"])
def api_total_usage(request):
    generate_live_data(request.user)

    start_time = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    readings = EnergyReading.objects.filter(
        device__user=request.user,
        timestamp__gte=start_time
    )

    from django.db.models import Sum
    total_wh = readings.aggregate(total=Sum('energy_consumed'))['total'] or 0

    return JsonResponse({
        'total_kwh': round(total_wh / 1000, 2),
    })

def generate_live_data(user):
    devices = Device.objects.filter(user=user)

    for device in devices:
        # 🔥 FORCE device ON for testing
        device.status = True
        device.save()

        simulate_reading(device)


def simulate_reading(device):
    if not device.status:
        return
    
    power = device.power_rating * random.uniform(0.8, 1.2)
    duration_hours = 0.003  # small interval
    energy_wh = power * duration_hours

    reading = EnergyReading.objects.create(
        device=device,
        power_usage=round(power, 1),
        energy_consumed=round(energy_wh, 3)
    )

    print("✅ CREATED:", reading.energy_consumed)


