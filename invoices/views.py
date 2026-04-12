from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
import io
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from .pdf import generate_invoice_pdf, generate_monthly_report_pdf
from customers.models import Customer
from cars.models import Car


def get_or_create_customer_and_car(form, invoice):
    """Helper: find or create customer and car from form data"""
    customer_name = form.cleaned_data.get('customer_name', '').strip()
    car_make = form.cleaned_data.get('car_make', '').strip()
    car_model = form.cleaned_data.get('car_model', '').strip()
    car_year = form.cleaned_data.get('car_year')
    car_vin = form.cleaned_data.get('car_vin', '').strip()
    car_stock = form.cleaned_data.get('car_stock', '').strip()

    # Find existing customer by name (case-insensitive)
    customer = Customer.objects.filter(name__iexact=customer_name).first()
    if not customer:
        invoice.customer_name = customer_name
        invoice.customer = None
    else:
        invoice.customer = customer
        invoice.customer_name = ''

    # Find or create car
    if customer and car_vin:
        car = Car.objects.filter(customer=customer, vin__iexact=car_vin).first()
        if not car:
            car = Car.objects.create(
                customer=customer,
                make=car_make,
                model=car_model,
                year=car_year,
                vin=car_vin,
                stock_number=car_stock,
            )
        invoice.car = car
        invoice.car_info = ''
    elif customer and car_make:
        car = Car.objects.filter(
            customer=customer,
            make__iexact=car_make,
            model__iexact=car_model
        ).first()
        if not car:
            car = Car.objects.create(
                customer=customer,
                make=car_make,
                model=car_model,
                year=car_year,
                vin=car_vin,
                stock_number=car_stock,
            )
        invoice.car = car
        invoice.car_info = ''
    else:
        invoice.car = None
        parts = [car_make]
        if car_model:
            parts.append(car_model)
        if car_year:
            parts.append(str(car_year))
        if car_vin:
            parts.append(f'VIN: {car_vin}')
        if car_stock:
            parts.append(f'Stock#: {car_stock}')
        invoice.car_info = ' '.join(parts)

    return invoice


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        user = request.user
        context = {
            'total_invoices': Invoice.objects.count(),
            'total_customers': Customer.objects.count(),
            'recent_invoices': Invoice.objects.select_related(
                'customer', 'car', 'created_by'
            ).order_by('-created_at')[:10],
        }
        return render(request, 'invoices/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class InvoiceListView(View):
    def get(self, request):
        invoices = Invoice.objects.all().select_related('customer', 'car', 'created_by')

        # Filters
        q = request.GET.get('q', '')
        customer_id = request.GET.get('customer')
        staff_id = request.GET.get('staff')
        month = request.GET.get('month')
        year = request.GET.get('year')
        vin = request.GET.get('vin')

        if q:
            invoices = invoices.filter(invoice_number__icontains=q)
        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if staff_id:
            invoices = invoices.filter(created_by_id=staff_id)
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year:
            invoices = invoices.filter(invoice_date__year=year)
        if vin:
            invoices = invoices.filter(car__vin__icontains=vin)

        from users.models import User
        customers = Customer.objects.all()
        staff_list = User.objects.all()
        return render(request, 'invoices/invoice_list.html', {
            'invoices': invoices,
            'customers': customers,
            'staff_list': staff_list,
        })


@method_decorator(login_required, name='dispatch')
class InvoiceCreateView(View):
    def get(self, request):
        form = InvoiceForm()
        formset = InvoiceItemFormSet()
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Invoice',
        })

    def post(self, request):
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.status = 'draft'
            invoice = get_or_create_customer_and_car(form, invoice)
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, f'Invoice #{invoice.invoice_number} created!')
            return redirect('invoice_detail', pk=invoice.pk)
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Invoice',
        })


@method_decorator(login_required, name='dispatch')
class InvoiceEditView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Edit Invoice',
            'invoice': invoice,
        })

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice = get_or_create_customer_and_car(form, invoice)
            invoice.save()
            formset.save()
            messages.success(request, f'Invoice #{invoice.invoice_number} updated!')
            return redirect('invoice_detail', pk=invoice.pk)
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Edit Invoice',
            'invoice': invoice,
        })


@method_decorator(login_required, name='dispatch')
class InvoiceDetailView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@method_decorator(login_required, name='dispatch')
class InvoiceActionView(View):
    """Handles send, decline, draft actions"""
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        action = request.POST.get('action')

        if action == 'send':
            emails = []
            if invoice.customer:
                emails = invoice.customer.get_all_emails()
            if not emails:
                messages.error(request, 'No email address found for this customer')
                return redirect('invoice_detail', pk=pk)

            # Generate PDF in memory
            buffer = io.BytesIO()
            generate_invoice_pdf(buffer, invoice)
            buffer.seek(0)

            customer_name = invoice.get_customer_display()
            email_msg = EmailMessage(
                subject=f'Your Invoice from AutoProTinting — #{invoice.invoice_number}',
                body=(
                    f'Dear {customer_name},\n\n'
                    f'Please find your invoice attached.\n\n'
                    f'We kindly ask you to complete the payment according to our agreement '
                    f'at your earliest convenience.\n\n'
                    f'If you have any questions or need any clarification, feel free to reach out '
                    f'— we\'re always happy to help.\n\n'
                    f'Thank you for choosing AutoProTinting. We truly appreciate your business '
                    f'and look forward to working with you again.\n\n'
                    f'Best regards,\n'
                    f'AutoProTinting Team'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=emails,
            )
            email_msg.attach(
                f'invoice_{invoice.invoice_number}.pdf',
                buffer.read(),
                'application/pdf'
            )
            email_msg.send()
            invoice.status = 'sent'
            invoice.save()
            messages.success(request, f'Invoice sent to {", ".join(emails)}')

        elif action == 'decline':
            invoice.status = 'declined'
            invoice.save()
            messages.success(request, 'Invoice declined')

        elif action == 'draft':
            invoice.status = 'draft'
            invoice.save()
            messages.success(request, 'Invoice saved as draft')

        return redirect('invoice_detail', pk=pk)


@method_decorator(login_required, name='dispatch')
class InvoicePDFView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        generate_invoice_pdf(response, invoice)
        return response


@method_decorator(login_required, name='dispatch')
class InvoiceDeleteView(View):
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice.delete()
        messages.success(request, 'Invoice deleted')
        return redirect('invoice_list')


@method_decorator(login_required, name='dispatch')
class CustomerSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '')
        if len(q) >= 2:
            customers = Customer.objects.filter(name__icontains=q)[:10]
            data = [{
                'id': c.id,
                'name': c.name,
                'company': c.company or '',
                'phone': c.phone or '',
                'cars': [{'id': car.id, 'display': car.get_display_with_details(),
                          'make': car.make, 'model': car.model,
                          'year': car.year, 'vin': car.vin,
                          'stock': car.stock_number}
                         for car in c.cars.all()[:5]]
            } for c in customers]
        else:
            data = []
        return JsonResponse({'results': data})


@method_decorator(login_required, name='dispatch')
class MonthlyReportView(View):
    def get(self, request):
        invoices = Invoice.objects.all().select_related('customer', 'car', 'created_by')

        # Filters
        customer_id = request.GET.get('customer')
        staff_id = request.GET.get('staff')
        month = request.GET.get('month')
        year = request.GET.get('year', timezone.now().year)
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        vin = request.GET.get('vin')

        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if staff_id:
            invoices = invoices.filter(created_by_id=staff_id)
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year and not date_from:
            invoices = invoices.filter(invoice_date__year=year)
        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)
        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)
        if vin:
            invoices = invoices.filter(car__vin__icontains=vin)

        from users.models import User
        customers = Customer.objects.all()
        staff_list = User.objects.all()

        return render(request, 'invoices/monthly_report.html', {
            'invoices': invoices,
            'customers': customers,
            'staff_list': staff_list,
            'total': sum(inv.total for inv in invoices),
            'month': month,
            'year': year,
        })


@method_decorator(login_required, name='dispatch')
class MonthlyReportPDFView(View):
    def get(self, request):
        invoices = Invoice.objects.all().select_related('customer', 'car', 'created_by')

        customer_id = request.GET.get('customer')
        staff_id = request.GET.get('staff')
        month = request.GET.get('month')
        year = request.GET.get('year')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        vin = request.GET.get('vin')

        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if staff_id:
            invoices = invoices.filter(created_by_id=staff_id)
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year and not date_from:
            invoices = invoices.filter(invoice_date__year=year)
        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)
        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)
        if vin:
            invoices = invoices.filter(car__vin__icontains=vin)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report.pdf"'
        generate_monthly_report_pdf(response, invoices)
        return response


@method_decorator(login_required, name='dispatch')
class SendStatementView(View):
    def post(self, request):
        customer_id = request.POST.get('customer_id')
        customer = get_object_or_404(Customer, pk=customer_id)
        emails = customer.get_all_emails()

        if not emails:
            messages.error(request, 'No email address found for this customer')
            return redirect('monthly_report')

        invoices = Invoice.objects.filter(customer=customer)
        month = request.POST.get('month')
        year = request.POST.get('year')
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year:
            invoices = invoices.filter(invoice_date__year=year)

        buffer = io.BytesIO()
        generate_monthly_report_pdf(buffer, invoices)
        buffer.seek(0)

        email_msg = EmailMessage(
            subject='Statement from AUTOPROTINTING INC',
            body=(
                f'Dear {customer.name},\n\n'
                f'Your statement is attached. Please remit payment at your earliest convenience.\n'
                f'Thank you for your business - we appreciate it very much.\n\n'
                f'Have a great day!\n'
                f'AUTOPROTINTING INC'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emails,
        )
        email_msg.attach('statement.pdf', buffer.read(), 'application/pdf')
        email_msg.send()
        messages.success(request, f'Statement sent to {", ".join(emails)}')
        return redirect('monthly_report')