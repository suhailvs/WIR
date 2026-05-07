from functools import wraps
from django.shortcuts import render, redirect
from django.db import transaction as db_transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.core.cache import cache

from .models import Transaction
from .forms import TransactionForm
User = get_user_model()
LIMIT = 30 # number of requests
WINDOW = 60 # total seconds

def rate_limit(limit, window, prefix): # limit = number of requests, window = total seconds
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            key = f"{prefix}:{request.user.id}"
            current = cache.get(key, 0)
            if current >= limit:
                response = JsonResponse({"error": f"Too many requests. Retry after {window} seconds."}, status=429)
                return response
            if current == 0:
                cache.set(key, 1, timeout=window)
            else:
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, timeout=window)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


@login_required
@rate_limit(limit=LIMIT, window=WINDOW, prefix="rl:create_tx") 
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
@rate_limit(limit=LIMIT, window=WINDOW, prefix="rl:list_tx")
def transactions(request):
    object_list = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related("receiver", "sender").order_by('-id')
    paginator = Paginator(object_list, 5)
    page_number = request.GET.get('page')
    return render(request,"transactions.html",{"page_obj": paginator.get_page(page_number)})

@require_POST
@login_required
@rate_limit(limit=LIMIT, window=WINDOW, prefix="rl:ajax")
def ajax(request):
    user = User.objects.filter(username=request.POST.get('username', '')).first()
    if user:
        return JsonResponse({"first_name": user.first_name}) #[:2] + "***"})
    return JsonResponse({"error": "User not found"}, status=404)
