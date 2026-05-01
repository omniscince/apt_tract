from django.db import models
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
import threading
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from .pdf import generate_invoice_pdf, generate_monthly_report_pdf
from customers.models import Customer
from cars.models import Car


def get_or_create_customer_and_car(form, invoice):
    customer_name = form.cleaned_data.get('customer_name', '').strip()
    car_make = form.cleaned_data.get('car_make', '').strip()
    car_model = form.cleaned_data.get('car_model', '').strip()
    car_vin = form.cleaned_data.get('car_vin', '').strip()
    car_stock = form.cleaned_data.get('car_stock', '').strip()

    customer = Customer.objects.filter(name__iexact=customer_name).first()
    if not customer:
        invoice.customer_name = customer_name
        invoice.customer = None
    else:
        invoice.customer = customer
        invoice.customer_name = ''

    if customer and car_vin:
        car = Car.objects.filter(customer=customer, vin__iexact=car_vin).first()
        if not car:
            car = Car.objects.create(
                customer=customer,
                make=car_make,
                model=car_model,
                vin=car_vin,
                stock_number=car_stock,
            )
        else:
            # Update car make/model if changed
            car.make = car_make
            car.model = car_model
            car.stock_number = car_stock
            car.save()
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
                vin=car_vin,
                stock_number=car_stock,
            )
        else:
            car.make = car_make
            car.model = car_model
            car.stock_number = car_stock
            car.save()
        invoice.car = car
        invoice.car_info = ''
    else:
        invoice.car = None
        parts = [car_make]
        if car_model:
            parts.append(car_model)
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
        if user.role == 'staff':
            invoices_qs = Invoice.objects.filter(created_by=user)
        else:
            invoices_qs = Invoice.objects.all()

        context = {
            'total_invoices': invoices_qs.count(),
            'total_customers': Customer.objects.count(),
            'recent_invoices': invoices_qs.select_related(
                'customer', 'car', 'created_by'
            ).order_by('-created_at')[:10],
        }
        return render(request, 'invoices/dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class InvoiceListView(View):
    def get(self, request):
        user = request.user
        if user.role == 'staff':
            invoices = Invoice.objects.filter(
                models.Q(created_by=user) | models.Q(work_completed_by=user)
            ).distinct().select_related('customer', 'car', 'created_by')
        else:
            invoices = Invoice.objects.all().select_related('customer', 'car', 'created_by')

        q = request.GET.get('q', '')
        customer_id = request.GET.get('customer')
        staff_id = request.GET.get('staff')
        month = request.GET.get('month')
        year = request.GET.get('year')
        vin = request.GET.get('vin')
        status = request.GET.get('status')

        if q:
            invoices = invoices.filter(invoice_number__icontains=q)
        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if staff_id and user.role != 'staff':
            invoices = invoices.filter(created_by_id=staff_id)
        if month:
            invoices = invoices.filter(invoice_date__month=month)
        if year:
            invoices = invoices.filter(invoice_date__year=year)
        if vin:
            invoices = invoices.filter(car__vin__icontains=vin)
        if status:
            invoices = invoices.filter(status=status)

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
        form = InvoiceForm(user=request.user)
        formset = InvoiceItemFormSet()
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Create Invoice',
        })

    def post(self, request):
        form = InvoiceForm(request.POST, user=request.user)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.status = 'final'
            if request.user.role == 'owner':
                num = form.cleaned_data.get('invoice_number_override', '').strip()
                if num:
                    if Invoice.objects.filter(invoice_number=num).exists():
                        messages.error(request, f'Invoice #{num} already exists. Choose a different number.')
                        return render(request, 'invoices/invoice_form.html', {'form': form, 'formset': formset, 'title': 'Create Invoice'})
                    invoice.invoice_number = num
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
        if request.user.role == 'staff' and invoice.created_by != request.user and invoice.work_completed_by != request.user:
            messages.error(request, 'Access denied')
            return redirect('invoice_list')
        initial = {
            'customer_name': invoice.get_customer_display(),
            'invoice_number_override': invoice.invoice_number,
        }
        if invoice.car:
            initial['car_make'] = invoice.car.make
            initial['car_model'] = invoice.car.model
            initial['car_vin'] = invoice.car.vin
            initial['car_stock'] = invoice.car.stock_number
        elif invoice.car_info:
            initial['car_make'] = invoice.car_info
        form = InvoiceForm(instance=invoice, user=request.user, initial=initial)
        formset = InvoiceItemFormSet(instance=invoice)
        return render(request, 'invoices/invoice_form.html', {
            'form': form,
            'formset': formset,
            'title': 'Edit Invoice',
            'invoice': invoice,
        })

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        if request.user.role == 'staff' and invoice.created_by != request.user and invoice.work_completed_by != request.user:
            messages.error(request, 'Access denied')
            return redirect('invoice_list')
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            if request.user.role == 'owner':
                num = form.cleaned_data.get('invoice_number_override', '').strip()
                if num:
                    invoice.invoice_number = num
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
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        action = request.POST.get('action')

        if action == 'send':
            emails = request.POST.getlist('emails')
            if not emails:
                if invoice.customer:
                    emails = invoice.customer.get_all_emails()
            if not emails:
                messages.error(request, 'No email address found')
                return redirect('invoice_detail', pk=pk)

            buffer = io.BytesIO()
            generate_invoice_pdf(buffer, invoice)
            buffer.seek(0)

            customer_name = invoice.get_customer_display()
            email_msg = EmailMessage(
                subject=f'Your Invoice from AutoProTinting — #{invoice.invoice_number}',
                body=(
                    f'Dear {customer_name},\n\n'
                    f'Here\'s your invoice! We appreciate your prompt payment. Thanks for your business!\n\n'
                    f'To view and print the attached invoice, double-click on the invoice icon, '
                    f'and then choose File, Print when the invoice is displayed. '
                    f'To save the invoice, copy it from this e-mail to another folder on your computer.\n\n'
                    f'If you have any questions regarding this invoice, please contact Accounting at (647) 771-1112\n\n'
                    f'Regards,\n'
                    f'Accounting Department, Autoprotinting'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=emails,
            )
            email_msg.attach(
                f'invoice_{invoice.invoice_number}.pdf',
                buffer.read(),
                'application/pdf'
            )
            def send_email():
                try:
                    email_msg.send()
                except Exception:
                    pass

            threading.Thread(target=send_email, daemon=True).start()
            invoice.status = 'final'
            invoice.save()
            messages.success(request, f'Invoice sent to {", ".join(emails)}')

        elif action == 'cancel':
            invoice.status = 'cancelled'
            invoice.save()
            messages.success(request, 'Invoice cancelled')

        elif action == 'final':
            invoice.status = 'final'
            invoice.save()
            messages.success(request, 'Invoice marked as final')

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
        if request.user.role == 'staff':
            messages.error(request, 'Access denied — staff cannot delete invoices')
            return redirect('invoice_list')
        invoice.delete()
        messages.success(request, 'Invoice deleted')
        return redirect('invoice_list')


@method_decorator(login_required, name='dispatch')
class CustomerSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '')
        if len(q) >= 1:
            customers = Customer.objects.filter(name__icontains=q)[:10]
            data = [{
                'id': c.id,
                'name': c.name,
                'company': c.company or '',
                'phone': c.phone or '',
                'cars': [{'id': car.id, 'display': car.get_display_with_details(),
                          'make': car.make, 'model': car.model,
                          'vin': car.vin,
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

        customer_id = request.GET.get('customer')
        staff_id = request.GET.get('staff')
        month = request.GET.get('month')
        year = request.GET.get('year', '')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        vin = request.GET.get('vin')

        if customer_id:
            invoices = invoices.filter(customer_id=customer_id)
        if staff_id:
            invoices = invoices.filter(created_by_id=staff_id)
        if month:
            try:
                invoices = invoices.filter(invoice_date__month=int(month))
            except (ValueError, TypeError):
                pass
        if year and not date_from:
            try:
                invoices = invoices.filter(invoice_date__year=int(year))
            except (ValueError, TypeError):
                pass
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
            try:
                invoices = invoices.filter(invoice_date__month=int(month))
            except (ValueError, TypeError):
                pass
        if year and not date_from:
            try:
                invoices = invoices.filter(invoice_date__year=int(year))
            except (ValueError, TypeError):
                pass
        if date_from:
            invoices = invoices.filter(invoice_date__gte=date_from)
        if date_to:
            invoices = invoices.filter(invoice_date__lte=date_to)
        if vin:
            invoices = invoices.filter(car__vin__icontains=vin)

        customer = None
        if customer_id:
            from customers.models import Customer as C
            customer = C.objects.filter(pk=customer_id).first()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Invoice_Statement.pdf"'
        generate_monthly_report_pdf(response, invoices, customer=customer)
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
        generate_monthly_report_pdf(buffer, invoices, customer=customer)
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
        def send_statement():
            try:
                email_msg.send()
            except Exception:
                pass

        threading.Thread(target=send_statement, daemon=True).start()
        messages.success(request, f'Statement sent to {", ".join(emails)}')
        return redirect('monthly_report')