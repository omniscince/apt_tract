from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import Car
from .forms import CarForm


@method_decorator(login_required, name='dispatch')
class CarListView(View):
    def get(self, request):
        cars = Car.objects.select_related('customer').all()
        return render(request, 'cars/car_list.html', {'cars': cars})


@method_decorator(login_required, name='dispatch')
class CarCreateView(View):
    def get(self, request):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = CarForm()
        return render(request, 'cars/car_form.html', {'form': form, 'title': 'Add Car'})

    def post(self, request):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save()
            messages.success(request, f'Car added!')
            return redirect('car_list')
        return render(request, 'cars/car_form.html', {'form': form, 'title': 'Add Car'})


@method_decorator(login_required, name='dispatch')
class CarEditView(View):
    def get(self, request, pk):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        car = get_object_or_404(Car, pk=pk)
        form = CarForm(instance=car)
        return render(request, 'cars/car_form.html', {'form': form, 'title': 'Edit Car'})

    def post(self, request, pk):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        car = get_object_or_404(Car, pk=pk)
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, 'Car updated!')
            return redirect('car_list')
        return render(request, 'cars/car_form.html', {'form': form, 'title': 'Edit Car'})


@method_decorator(login_required, name='dispatch')
class CarDeleteView(View):
    def post(self, request, pk):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        car = get_object_or_404(Car, pk=pk)
        car.delete()
        messages.success(request, 'Car deleted')
        return redirect('car_list')