from django.shortcuts import render, redirect
from django.db import transaction as db_transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

from .models import Transaction
from .forms import TransactionForm
User = get_user_model()

@login_required
def home(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request_user=request.user)
        if form.is_valid():
            receiver = User.objects.get(username=form.cleaned_data["receiver"])
            amount    = form.cleaned_data["amount"]
            description   = form.cleaned_data["description"]
            sender = request.user
            with db_transaction.atomic():
                sender.balance -= amount
                receiver.balance += amount
                sender.save(update_fields=["balance"])
                receiver.save(update_fields=["balance"])
                txn = Transaction.objects.create(sender=sender, receiver=receiver, amount=amount, description=description)
            messages.success(request, f"Success! txnId:{txn.id}")
            return redirect("home")
    else:
        form = TransactionForm(request_user=request.user)
    total = User.objects.aggregate(t=Sum('balance'))['t']
    return render(request,"home.html",{"transaction_form": form, "total":total})

@login_required
def transactions(request):
    object_list = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related("receiver", "sender").order_by("-created_at")    
    paginator = Paginator(object_list, 5)
    page_number = request.GET.get('page')
    return render(request,"transactions.html",{"page_obj": paginator.get_page(page_number)})

@login_required
@csrf_exempt
def ajax(request):
    if request.method == "POST":
        user = User.objects.filter(username=request.POST['username']).first()
        if user: return HttpResponse(user.first_name)
        return HttpResponse("Resource not found", status=404)