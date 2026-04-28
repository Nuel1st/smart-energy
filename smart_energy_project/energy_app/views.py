from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Sum
from uuid import UUID
import json
import random
from datetime import timedelta

from .models import Device, EnergyReading, UserThreshold
from .serializers import DeviceSerializer, EnergyReadingSerializer
from django.core.cache import cache


# ================= AUTH =================
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
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'energy_app/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ================= DASHBOARD =================
@login_required
def dashboard(request):
    devices = Device.objects.filter(user=request.user)

    today = timezone.now().date()
    readings = EnergyReading.objects.filter(
        device__user=request.user,
        timestamp__date=today
    )

    total_wh = readings.aggregate(total=Sum('energy_consumed'))['total'] or 0

    return render(request, 'energy_app/dashboard.html', {
        'devices': devices,
        'total_daily': round(total_wh / 1000, 2),
    })


@login_required
def devices_view(request):
    devices = Device.objects.filter(user=request.user)
    return render(request, 'energy_app/devices.html', {'devices': devices})


# ================= API =================

@login_required
@require_http_methods(["GET", "POST"])
def api_devices(request):
    if request.method == 'GET':
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)
        return JsonResponse({'devices': serializer.data})

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
    try:
        device = Device.objects.get(id=UUID(device_id), user=request.user)

        device.status = not device.status
        device.save()

        return JsonResponse({'status': device.status})

    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)


# ================= ENERGY ENGINE =================

# def generate_live_data(user):
#     """
#     Only generate energy when device is ON
#     """
#     devices = Device.objects.filter(user=user, status=True)  # ✅ ONLY ON DEVICES

#     for device in devices:
#         simulate_reading(device)


def simulate_reading(device):
    """
    Realistic energy simulation based on time
    """
    if not device.status:
        return

    # Simulate real fluctuation
    power = device.power_rating * random.uniform(0.85, 1.15)

    # Assume 3-second interval
    duration_hours = 3 / 3600

    energy_wh = power * duration_hours

    EnergyReading.objects.create(
        device=device,
        power_usage=round(power, 2),
        energy_consumed=round(energy_wh, 4)
    )

def generate_live_data(user):
    key = f"last_generated_{user.id}"
    last_time = cache.get(key)

    now = timezone.now()

    # only generate every 3 seconds
    if last_time and (now - last_time).total_seconds() < 3:
        return

    devices = Device.objects.filter(user=user, status=True)

    for device in devices:
        simulate_reading(device)

    cache.set(key, now, timeout=5)


# ================= API DATA =================

@login_required
def api_energy_data(request):
    generate_live_data(request.user)

    readings = EnergyReading.objects.filter(
        device__user=request.user
    ).order_by('-timestamp')[:20]

    serializer = EnergyReadingSerializer(readings, many=True)
    return JsonResponse({'readings': serializer.data})


# @login_required
# def api_total_usage(request):
#     # generate_live_data(request.user)
#     start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

#     devices_on = Device.objects.filter(user=request.user, status=True)

#     readings = EnergyReading.objects.filter(
#         device__in=devices_on,
#         timestamp__gte=start
#     ) 

#     # readings = EnergyReading.objects.filter(
#     #     device__user=request.user,
#     #     timestamp__gte=start
#     # )

#     total_wh = readings.aggregate(total=Sum('energy_consumed'))['total'] or 0

#     return JsonResponse({
#         'total_kwh': round(total_wh / 1000, 3),
#     })


@login_required
def api_total_usage(request):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    readings = EnergyReading.objects.filter(
        device__user=request.user,
        timestamp__gte=start
    )

    total_wh = readings.aggregate(total=Sum('energy_consumed'))['total'] or 0
    total_kwh = total_wh / 1000

    threshold, _ = UserThreshold.objects.get_or_create(user=request.user)

    alert = None
    if total_kwh > threshold.daily_threshold:
        alert = "🚨 High energy usage detected!"

    return JsonResponse({
        'total_kwh': round(total_kwh, 3),
        'alert': alert
    })

