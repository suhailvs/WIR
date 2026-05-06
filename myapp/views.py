from django.shortcuts import render, redirect
from django.db import transaction as db_transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Transaction
from .forms import TransactionForm
User = get_user_model()

@login_required
def home(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request_user=request.user)
        if form.is_valid():
            receiver = form.cleaned_data["receiver"]
            amount    = form.cleaned_data["amount"]
            description   = form.cleaned_data["description"]
            sender = request.user
            with db_transaction.atomic():
                if not sender.can_spend(amount):
                    form.add_error(None, "Credit limit exceeded")
                    return render(request,"home.html",{"transaction_form": form, "total":0})
                sender.balance -= amount
                receiver.balance += amount
                sender.save(update_fields=["balance"])
                receiver.save(update_fields=["balance"])
                txn = Transaction.objects.create(sender=sender, receiver=receiver, amount=amount, description=description)
            messages.success(request, f"Success! txnId:{txn.id}")
            return redirect("home")
    else:
        form = TransactionForm(request_user=request.user)
    total = 0 #User.objects.aggregate(t=Sum('balance'))['t']
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
@require_POST
def ajax(request):
    user = User.objects.filter(username=request.POST.get('username', '')).first()
    if user:
        return JsonResponse({"first_name": user.first_name})
    return JsonResponse({"error": "Resource not found"}, status=404)
