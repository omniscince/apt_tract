from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import Customer
from .forms import CustomerForm, CustomerEmailFormSet


@method_decorator(login_required, name='dispatch')
class CustomerListView(View):
    def get(self, request):
        customers = Customer.objects.all()
        q = request.GET.get('q', '')
        if q:
            customers = customers.filter(name__icontains=q)
        return render(request, 'customers/customer_list.html', {
            'customers': customers,
            'q': q,
        })


@method_decorator(login_required, name='dispatch')
class CustomerCreateView(View):
    def get(self, request):
        form = CustomerForm()
        email_formset = CustomerEmailFormSet()
        return render(request, 'customers/customer_form.html', {
            'form': form,
            'email_formset': email_formset,
            'title': 'Create Customer',
        })

    def post(self, request):
        form = CustomerForm(request.POST)
        email_formset = CustomerEmailFormSet(request.POST)
        if form.is_valid() and email_formset.is_valid():
            customer = form.save()
            email_formset.instance = customer
            email_formset.save()
            messages.success(request, f'Customer {customer.name} created!')
            return redirect('customer_detail', pk=customer.pk)
        return render(request, 'customers/customer_form.html', {
            'form': form,
            'email_formset': email_formset,
            'title': 'Create Customer',
        })


@method_decorator(login_required, name='dispatch')
class CustomerDetailView(View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        invoices = customer.invoices.select_related('car', 'created_by').order_by('-invoice_date')
        cars = customer.cars.all()
        return render(request, 'customers/customer_detail.html', {
            'customer': customer,
            'invoices': invoices,
            'cars': cars,
        })


@method_decorator(login_required, name='dispatch')
class CustomerEditView(View):
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(instance=customer)
        email_formset = CustomerEmailFormSet(instance=customer)
        return render(request, 'customers/customer_form.html', {
            'form': form,
            'email_formset': email_formset,
            'title': 'Edit Customer',
            'customer': customer,
        })

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(request.POST, instance=customer)
        email_formset = CustomerEmailFormSet(request.POST, instance=customer)
        if form.is_valid() and email_formset.is_valid():
            form.save()
            email_formset.instance = customer
            email_formset.save()
            messages.success(request, f'Customer {customer.name} updated!')
            return redirect('customer_detail', pk=customer.pk)
        return render(request, 'customers/customer_form.html', {
            'form': form,
            'email_formset': email_formset,
            'title': 'Edit Customer',
            'customer': customer,
        })


@method_decorator(login_required, name='dispatch')
class CustomerDeleteView(View):
    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        messages.success(request, 'Customer deleted')
        return redirect('customer_list')