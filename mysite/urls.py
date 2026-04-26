from django.contrib import admin
from django.urls import path
from myapp import views
urlpatterns = [
    path('',views.home, name='home'),
    path('transactions/',views.transactions, name='transactions'),
    path('ajax/',views.ajax, name='ajax'),
    path('admin/', admin.site.urls),
]
