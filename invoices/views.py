from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse
from django.utils import timezone
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from .pdf import generate_invoice_pdf, generate_monthly_report_pdf
from customers.models import Customer
from cars.models import Car


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        user = request.user
        context = {}
        if user.role in ['owner', 'accountant', 'staff']:
            context['total_invoices'] = Invoice.objects.count()
            context['total_customers'] = Customer.objects.count()
            context['recent_invoices'] = Invoice.objects.select_related('customer', 'car').order_by('-created_at')[:5]
        elif user.role == 'client':
            context['my_invoices'] = Invoice.objects.filter(
                customer__email=user.email
            ).select_related('customer', 'car').order_by('-created_at')[:10]
        return render(request, 'invoices/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class InvoiceListView(View):
    def get(self, request):
        user = request.user
        if user.role == 'client':
            invoices = Invoice.objects.filter(customer__email=user.email).select_related('customer', 'car')
        else:
            invoices = Invoice.objects.all().select_related('customer', 'car', 'created_by')

        # Filters
        customer_id = request.GET.get('customer')
        month = request.GET.get('month')
        year = request.GET.get('year')

        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year:
            invoices = invoices.filter(invoice_date__year=year)

        customers = Customer.objects.all()
        return render(request, 'invoices/invoice_list.html', {
            'invoices': invoices,
            'customers': customers,
        })


@method_decorator(login_required, name='dispatch')
class InvoiceCreateView(View):
    def get(self, request):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Invoice'
        })

    def post(self, request):
        if request.user.role not in ['owner', 'staff']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, f'Invoice #{invoice.invoice_number} created!')
            return redirect('invoice_detail', pk=invoice.pk)
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Invoice'
        })


@method_decorator(login_required, name='dispatch')
class InvoiceDetailView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if request.user.role == 'client' and invoice.customer.email != request.user.email:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@method_decorator(login_required, name='dispatch')
class InvoicePDFView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if request.user.role == 'client' and invoice.customer.email != request.user.email:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        generate_invoice_pdf(response, invoice)
        return response


@method_decorator(login_required, name='dispatch')
class InvoiceDeleteView(View):
    def post(self, request, pk):
        if request.user.role not in ['owner']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice.delete()
        messages.success(request, 'Invoice deleted')
        return redirect('invoice_list')


@method_decorator(login_required, name='dispatch')
class MonthlyReportView(View):
    def get(self, request):
        if request.user.role not in ['owner', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        customers = Customer.objects.all()
        customer_id = request.GET.get('customer')
        month = request.GET.get('month', timezone.now().month)
        year = request.GET.get('year', timezone.now().year)
        invoices = []
        selected_customer = None

        if customer_id:
            selected_customer = get_object_or_404(Customer, pk=customer_id)
            invoices = Invoice.objects.filter(
                customer=selected_customer,
                invoice_date__month=month,
                invoice_date__year=year
            ).prefetch_related('items')

        return render(request, 'invoices/monthly_report.html', {
            'customers': customers,
            'invoices': invoices,
            'selected_customer': selected_customer,
            'month': month,
            'year': year,
            'total': sum(inv.total for inv in invoices),
        })


@method_decorator(login_required, name='dispatch')
class MonthlyReportPDFView(View):
    def get(self, request):
        if request.user.role not in ['owner', 'accountant']:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        customer_id = request.GET.get('customer')
        month = request.GET.get('month', timezone.now().month)
        year = request.GET.get('year', timezone.now().year)
        customer = get_object_or_404(Customer, pk=customer_id)
        invoices = Invoice.objects.filter(
            customer=customer,
            invoice_date__month=month,
            invoice_date__year=year
        ).prefetch_related('items')

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{customer.name}_{month}_{year}.pdf"'
        generate_monthly_report_pdf(response, customer, invoices, month, year)
        return response