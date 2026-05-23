from django.urls import path
from . import views

urlpatterns = [
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerEditView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    path('api/customers/quick-create/', views.CustomerQuickCreateView.as_view(), name='customer_quick_create'),
    path('customers/<int:pk>/add-email/', views.CustomerAddEmailView.as_view(), name='customer_add_email'),
]