from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from myapp import views
urlpatterns = [
    path('',views.home, name='home'),
    path('pay/success/<int:txn_id>/', views.pay_success, name='pay_success'),
    path('transactions/',views.transactions, name='transactions'),
    path('ajax/',views.ajax, name='ajax'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('admin/', admin.site.urls),
    path("pg/", include("paymentgateway.urls")),
]
