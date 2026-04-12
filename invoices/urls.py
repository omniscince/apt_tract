from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceEditView.as_view(), name='invoice_edit'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('reports/monthly/', views.MonthlyReportView.as_view(), name='monthly_report'),
    path('reports/monthly/pdf/', views.MonthlyReportPDFView.as_view(), name='monthly_report_pdf'),
    path('api/customers/search/', views.CustomerSearchView.as_view(), name='customer_search'),
    path('api/customers/<int:customer_id>/cars/', views.CarsByCustomerView.as_view(), name='cars_by_customer'),
]