from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import Car
from .forms import CarForm
from customers.models import Customer


@method_decorator(login_required, name='dispatch')
class CarListView(View):
    def get(self, request):
        cars = Car.objects.all().select_related('customer')
        q = request.GET.get('q', '')
        vin = request.GET.get('vin', '')
        customer_id = request.GET.get('customer')

        if q:
            cars = cars.filter(make__icontains=q) | cars.filter(model__icontains=q)
        if vin:
            cars = cars.filter(vin__icontains=vin)
        if customer_id:
            cars = cars.filter(customer_id=customer_id)

        customers = Customer.objects.all()
        return render(request, 'cars/car_list.html', {
            'cars': cars,
            'customers': customers,
            'q': q,
            'vin': vin,
        })


@method_decorator(login_required, name='dispatch')
class CarDetailView(View):
    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        invoices = car.invoices.order_by('-invoice_date')
        return render(request, 'cars/car_detail.html', {
            'car': car,
            'invoices': invoices,
        })


@method_decorator(login_required, name='dispatch')
class CarCreateView(View):
    def get(self, request):
        form = CarForm()
        return render(request, 'cars/car_form.html', {
            'form': form,
            'title': 'Add Car',
        })

    def post(self, request):
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save()
            messages.success(request, f'Car {car} added!')
            return redirect('car_detail', pk=car.pk)
        return render(request, 'cars/car_form.html', {
            'form': form,
            'title': 'Add Car',
        })


@method_decorator(login_required, name='dispatch')
class CarEditView(View):
    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        form = CarForm(instance=car)
        return render(request, 'cars/car_form.html', {
            'form': form,
            'title': 'Edit Car',
            'car': car,
        })

    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, f'Car {car} updated!')
            return redirect('car_detail', pk=car.pk)
        return render(request, 'cars/car_form.html', {
            'form': form,
            'title': 'Edit Car',
            'car': car,
        })


@method_decorator(login_required, name='dispatch')
class CarDeleteView(View):
    def post(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        car.delete()
        messages.success(request, 'Car deleted')
        return redirect('car_list')