from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import Customer
from .forms import CustomerForm


@method_decorator(login_required, name='dispatch')
class CustomerListView(View):
    def get(self, request):
        customers = Customer.objects.all()
        return render(request, 'customers/customer_list.html', {'customers': customers})


@method_decorator(login_required, name='dispatch')
class CustomerCreateView(View):
    def get(self, request):
        if request.user.role not in ['owner', 'staff', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = CustomerForm()
        return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Add Customer'})

    def post(self, request):
        if request.user.role not in ['owner', 'staff', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.name} created!')
            return redirect('customer_detail', pk=customer.pk)
        return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Add Customer'})


@method_decorator(login_required, name='dispatch')
class CustomerDetailView(View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        return render(request, 'customers/customer_detail.html', {'customer': customer})


@method_decorator(login_required, name='dispatch')
class CustomerEditView(View):
    def get(self, request, pk):
        if request.user.role not in ['owner', 'staff', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(instance=customer)
        return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Edit Customer'})

    def post(self, request, pk):
        if request.user.role not in ['owner', 'staff', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated!')
            return redirect('customer_detail', pk=pk)
        return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@method_decorator(login_required, name='dispatch')
class CustomerDeleteView(View):
    def post(self, request, pk):
        if not request.user.is_owner:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        messages.success(request, 'Customer deleted')
        return redirect('customer_list')