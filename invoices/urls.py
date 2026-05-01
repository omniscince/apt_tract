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
    path('invoices/<int:pk>/action/', views.InvoiceActionView.as_view(), name='invoice_action'),
    path('reports/', views.MonthlyReportView.as_view(), name='monthly_report'),
    path('reports/pdf/', views.MonthlyReportPDFView.as_view(), name='monthly_report_pdf'),
    path('reports/send-statement/', views.SendStatementView.as_view(), name='send_statement'),
    path('api/customers/search/', views.CustomerSearchView.as_view(), name='customer_search'),
    path('invoices/statement-preview/', views.StatementPreviewView.as_view(), name='statement_preview'),
    path('reports/invoice-history/', views.InvoiceHistoryReportView.as_view(), name='invoice_history_report'),
    path('reports/crew/', views.CrewReportView.as_view(), name='crew_report'),
    path('reports/customers/', views.CustomerReportView.as_view(), name='customer_report'),
]
