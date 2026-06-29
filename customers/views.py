from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import Customer
from .forms import CustomerForm, CustomerEmailFormSet
from django.http import JsonResponse
import json


@method_decorator(login_required, name='dispatch')
class CustomerListView(View):
    def get(self, request):
        q = request.GET.get('q', '')
        customers = Customer.objects.prefetch_related('cars').all()
        if q:
            from cars.models import Car
            car_customer_ids = Car.objects.filter(make__icontains=q).values_list('customer_id', flat=True)
            customers = customers.filter(name__icontains=q) | customers.filter(company__icontains=q) | customers.filter(id__in=car_customer_ids)
            customers = customers.distinct()
        from django.core.paginator import Paginator
        paginator = Paginator(customers, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return render(request, 'customers/customer_list.html', {
            'customers': page_obj,
            'page_obj': page_obj,
            'q': q,
        })


@method_decorator(login_required, name='dispatch')
class CustomerCreateView(View):
    def get(self, request):
        if request.user.role != 'owner':
            messages.error(request, 'Access denied')
            return redirect('customer_list')
        form = CustomerForm()
        email_formset = CustomerEmailFormSet()
        return render(request, 'customers/customer_form.html', {
            'form': form,
            'email_formset': email_formset,
            'title': 'Create Customer',
        })

    def post(self, request):
        if request.user.role != 'owner':
            messages.error(request, 'Access denied')
            return redirect('customer_list')
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
        if request.user.role != 'owner':
            messages.error(request, 'Access denied')
            return redirect('customer_list')
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
        if request.user.role != 'owner':
            messages.error(request, 'Access denied')
            return redirect('customer_list')
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
        if request.user.role != 'owner':
            messages.error(request, 'Access denied')
            return redirect('customer_list')
        customer = get_object_or_404(Customer, pk=pk)
        if customer.invoices.exists():
            messages.error(request, f'Cannot delete "{customer.name}" — this customer has existing invoices. Please remove the invoices first.')
            return redirect('customer_detail', pk=pk)
        name = customer.name
        customer.delete()
        messages.success(request, f'Customer {name} deleted successfully.')
        next_url = request.POST.get('next', '')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('customer_list')


@method_decorator(login_required, name='dispatch')
class CustomerQuickCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            phone = data.get('phone', '').strip()

            if not name:
                return JsonResponse({'error': 'Name is required'}, status=400)
            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            if Customer.objects.filter(name__iexact=name).exists():
                return JsonResponse({'error': f'Customer "{name}" already exists'}, status=400)

            customer = Customer.objects.create(name=name, phone=phone)
            from .models import CustomerEmail
            CustomerEmail.objects.create(customer=customer, email=email, is_primary=True)

            return JsonResponse({'success': True, 'name': customer.name, 'id': customer.pk})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class CustomerAddEmailView(View):
    def post(self, request, pk):
        from .models import CustomerEmail
        customer = get_object_or_404(Customer, pk=pk)
        email = request.POST.get('email', '').strip()
        if email:
            if not CustomerEmail.objects.filter(customer=customer, email=email).exists():
                CustomerEmail.objects.create(customer=customer, email=email, is_primary=False)
                from django.http import JsonResponse
                return JsonResponse({'success': True})
        from django.http import JsonResponse
        return JsonResponse({'error': 'Invalid or duplicate email'}, status=400)
