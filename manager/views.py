from datetime import date
import io
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db.models import Q
import qrcode
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
import requests

from account.models import Activity, AddressVerification, BannedIp, CopiedTrader, CopyRequest, Currency, Deposit, KYCVerification, Notification, PaymentGateway, Plan, PlanCategory, Trade, Trader, TraderApplication, TraderBenefit, User, UserPaymentMethod, UserPlan, Withdraw
from manager.forms import TraderForm
from utils.decorators import allowed_users

# Create your views here.

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def dashboard(request):
    total_users = User.objects.count()
    users_growth = 12  # or compute dynamically

    pending_kyc = KYCVerification.objects.filter(status="pending").count()

    pending_deposits_amount = Deposit.objects.filter(status="pending").aggregate(Sum("amount"))["amount__sum"] or 0
    pending_deposits_count = Deposit.objects.filter(status="pending").count()

    pending_withdrawals_amount = Withdraw.objects.filter(status="pending").aggregate(Sum("amount"))["amount__sum"] or 0
    pending_withdrawals_count = Withdraw.objects.filter(status="pending").count()

    activities = Activity.objects.all()[:20]

    context = {
        'header_title': 'Admin Dashboard',
        'body_class': 'page-admin-dashboard',
        "total_users": total_users,
        "users_growth": users_growth,
        "pending_kyc": pending_kyc,
        "pending_deposits_amount": pending_deposits_amount,
        "pending_deposits_count": pending_deposits_count,
        "pending_withdrawals_amount": pending_withdrawals_amount,
        "pending_withdrawals_count": pending_withdrawals_count,
        "activities": activities,
    }
    return render(request, 'manager/dashboard.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def user_list(request):
    users = User.objects.filter(groups__name='trader')
    if request.method == 'POST':
        print("phase 1")
        name = request.POST.get('username')
        print(name)
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            messages.error(request, 'No such user')
            return redirect('admin_user_list')
        user.ban = not user.ban
        user.save(update_fields=['ban'])

        messages.success(request, f"User {'suspended' if user.ban else 'unsuspended'} successfully.")
        return redirect('admin_user_list')
    context = {
        'header_title': 'Users Management',
        'body_class': 'page-admin-users',
        'users':users,
    }
    return render(request, 'manager/user_list.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def user_detail(request, username):
    user = User.objects.get(username=username)
    traders = CopiedTrader.objects.filter(user=user)
    trades = Trade.objects.filter(user=user)
    kyc = KYCVerification.objects.get(user=user)
    address = AddressVerification.objects.get(user=user)

    deposits = Deposit.objects.filter(user=user)
    withdraws = Withdraw.objects.filter(user=user)

    total_deposit = 0
    total_withdraw = 0
    total_trade = 0
    win_rate = 0
    active_plan = 0
    referral = 0

    # Normalizing field names for template
    transactions = []

    for d in deposits:
        transactions.append({
            "date": d.date_created,
            "txn_id": d.transaction_no,
            "type": "Deposit",
            "amount": d.amount,
            "status": d.status,
            "method": f"{d.currency.currency if d.currency else ''} ({d.network})",
            "ref": d.ref,
        })

    for w in withdraws:
        transactions.append({
            "date": w.date,
            "txn_id": w.transaction_no,
            "type": "Withdrawal",
            "amount": w.amount,
            "status": w.status,
            "method": w.gateway or "Bank Transfer",
            "ref": w.ref,
        })

    # Sort by date (newest first)
    transactions = sorted(transactions, key=lambda x: x["date"], reverse=True)

    active_trade = Trade.objects.filter(user=user,status='open').count()
    manual_trade = CopiedTrader.objects.filter(user=user).count()

    user_plans = UserPlan.objects.filter(user=user, active=True)

    currencies = Currency.objects.all()
    gateways = PaymentGateway.objects.all()

    user_payment_methods = UserPaymentMethod.objects.filter(user=user)

    print(user_payment_methods)

    if 'user_payment_method' in request.POST:
        payment_ref, payment_type = request.POST.get('paymentType').split('_')

        print(payment_ref, payment_type)

        if payment_type == 'currency':
            payment = Currency.objects.get(ref=payment_ref)
            method_type = 'currency'
        else:
            payment = PaymentGateway.objects.get(ref=payment_ref)
            method_type = 'gateway'

        UserPaymentMethod.objects.create(
            user=user,
            payment=payment,
            active=True,
            method_type=method_type,
        )

        messages.success(request, "payment method add to this user")
        return redirect('admin_user_detail', username)
    
    elif 'reset_password' in request.POST:
        # Generate a secure random password
        import secrets
        import string

        length = 10
        characters = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(characters) for _ in range(length))

        user.set_password(new_password)
        user.save()

        # Prepare email
        subject = "🔐 Your Password Has Been Reset"
        message = (
            f"Dear {user.first_name},\n\n"
            "Your password has been successfully reset.\n"
            f"Your new temporary password is:\n\n"
            f"👉 {new_password}\n\n"
            "Please log in and change this password immediately for security reasons.\n\n"
            "Best regards,\n"
            "The Support Team"
        )

        # Send the email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )

        print("Password changed")
        messages.success(request, "New password sent to user")
        return redirect('admin_user_detail', username),

    elif 'send_mail' in request.POST:

        subject = request.POST.get('emailSubject')
        message = request.POST.get('emailBody')

        # Send the email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )
        
        messages.success(request, "Email sent to user")
        return redirect('admin_user_detail', username)
    
    elif 'send_notification' in request.POST:

        title = request.POST.get('notificationTitle')
        message = request.POST.get('notificationMessage')

        Notification.objects.create(
            user=user,title=title,media_type='text',text=title.slice(2),color='info'
        )

        messages.success(request, 'Notification sent')
        return redirect('admin_user_detail', username)
    
    elif 'suspend_user' in request.POST:

        user.ban = not user.ban
        user.save(update_fields=['ban'])

        messages.success(request, f"User {'suspended' if user.ban else 'unsuspended'} successfully.")
        return redirect('admin_user_detail', username)
    
    elif 'ban_ip' in request.POST:
        BannedIp.objects.create(
            ip=user.ip_address,
            user=user,
        )

        messages.success(request, f"IP banned")
        return redirect("admin_user_detail", username)
    
    elif 'delete_user' in request.POST:
        pass

    elif 'global_switch' in request.POST:

        value = request.POST.get("global_switch")  # "1" or "0"

        user.use_global_settings = True if value == "1" else False
        user.save()

        messages.success(request, "Using global settings updated.")
        return redirect("admin_user_detail", username=username)
    
    elif 'edit_balance' in request.POST:
        trading_balance = request.POST.get('trading_balance')
        holding_balance = request.POST.get('holding_balance')

        user.deposit = trading_balance
        user.holding_deposit = holding_balance

        user.save()

        messages.success(request, "Successful")
        return redirect('admin_user_detail', username=username)
    
    elif 'premium_tick' in request.POST:
        user.is_premium_account = True
        user.use_badge = True

        user.save()

        messages.success(request, "successful")
        return redirect('admin_user_detail', username=username)
    
    elif 'suspend_user' in request.POST:
        user.ban = not user.ban

        user.save()

        messages.success(request, "successful")
        return redirect('admin_user_detail', username=username)
    
    elif 'blue_tick' in request.POST:
        user.is_premium_account = False
        user.use_badge = False

        user.save()

        messages.success(request, "successful")
        return redirect('admin_user_detail', username=username)
    
    elif 'take_trade' in request.POST:
        print("kdfkdfdkhf")

        trader_ref = request.POST.get('tradeTrader')
        market_type = request.POST.get('marketType')
        asset = request.POST.get('tradeAsset')
        direction = request.POST.get('direction')
        amount = float(request.POST.get('tradeAmount'))
        leverage = int(request.POST.get('tradeLeverage'))
        duration = request.POST.get('tradeDuration')
        outcome = request.POST.get('outcome')
        outcome_amount = request.POST.get('outcomeAmount')

        # Clean asset for Binance (e.g. 'BTC/USDT' → 'BTCUSDT')
        api_symbol = asset.replace("/", "")
        api_url = f"https://api.binance.com/api/v3/ticker/price?symbol={api_symbol}"

        entry_price = None

        # ====== FETCH MARKET PRICE FOR CRYPTO ======
        if market_type == 'crypto':
            try:
                response = requests.get(api_url, timeout=5)
                response.raise_for_status()
                data = response.json()

                if "price" not in data:
                    raise Exception("Invalid price response")

                entry_price = float(data["price"])

            except Exception as e:
                messages.error(request, f"Failed to fetch price: {e}")
                return redirect("admin_user_detail", username=username)

        # Safety check
        if entry_price is None:
            messages.error(request, "Entry price missing.")
            return redirect("admin_user_detail", username=username)

        # ====== CALCULATE SIZE ======
        # size = total_value / entry_price
        size = amount / entry_price

        # For now, on open trade PnL is zero
        pnl = 0
        pnl_percent = 0

        # ====== GET TRADER OBJECT ======
        trader = CopiedTrader.objects.get(ref=trader_ref)

        # ====== CHECK MODE ======
        mode = 'leverage' if leverage > 1 else 'spot'

        # ====== CREATE TRADE ======
        trade = Trade.objects.create(
            user=user,
            symbol=asset,
            trade_type=direction,
            mode=mode,
            leverage=leverage,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,   # same when opening
            duration=duration,
            pnl=pnl,
            pnl_percent=pnl_percent,
            asset=asset,
            status='open',
            opened_at=timezone.now(),
            trader=trader
        )

        messages.success(request, "Trade successfully opened.")
        return redirect("admin_user_detail", username=username)
    
    elif 'set_circle' in request.POST:

        trading_circle = request.POST.get('circle')

        user.trading_circle = int(trading_circle)
        user.save()

        messages.success(request, "Successful")
        return redirect('admin_user_detail', username=username)

    context = {
        'header_title': 'User Details',
        'body_class': 'page-admin-userdetails',
        'user':user,
        'traders':traders,
        'trades':trades,
        'kyc':kyc,
        'address':address,
        'transactions': transactions,
        'active_trade':active_trade,
        'manual_trade':manual_trade,
        'user_plans': user_plans,
        'currencies':currencies,
        'gateways':gateways,
        'methods':user_payment_methods,
    }
    return render(request, 'manager/user_detail.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def two_factor_authentication(request, user_id):
    if request.method == "POST":
        # Get the checkbox value (it exists only if checked)
        value = request.POST.get("status")  # "on" if checked, None if unchecked

        try:
           user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("admin_user_detail", username=user.username)
        
        # Update the user's field (example: artisan_accept_booking)
        user.two_factor_authentication_enabled = True if value == "on" else False
        user.save()

        # Redirect back to the same page
        messages.success(request, "Successful")
        return redirect("admin_user_detail", username=user.username)
    
    return redirect("admin_user_detail", username=user.username)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def enable_email_notification(request, user_id):
    if request.method == "POST":
        # Get the checkbox value (it exists only if checked)
        value = request.POST.get("email_notifications")  # "on" if checked, None if unchecked

        try:
           user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("admin_user_detail", username=user.username)
        
        # Update the user's field (example: artisan_accept_booking)
        user.email_notification = True if value == "on" else False
        user.save()

        # Redirect back to the same page
        messages.success(request, "Successful")
        return redirect("admin_user_detail", username=user.username)
    
    return redirect("admin_user_detail", username=user.username)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def enable_trading(request, user_id):
    if request.method == "POST":
        # Get the checkbox value (it exists only if checked)
        value = request.POST.get("trading_enabled")  # "on" if checked, None if unchecked

        try:
           user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("admin_user_detail", username=user.username)
        
        # Update the user's field (example: artisan_accept_booking)
        user.trading_enabled = True if value == "on" else False
        user.save()

        # Redirect back to the same page
        messages.success(request, "Successful")
        return redirect("admin_user_detail", username=user.username)
    
    return redirect("admin_user_detail", username=user.username)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def enable_withdrawal(request, user_id):
    if request.method == "POST":
        # Get the checkbox value (it exists only if checked)
        value = request.POST.get("withdrawal_enabled")  # "on" if checked, None if unchecked

        try:
           user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("admin_user_detail", username=user.username)
        
        # Update the user's field (example: artisan_accept_booking)
        user.withdrawal_enabled = True if value == "on" else False
        user.save()

        # Redirect back to the same page
        messages.success(request, "Successful")
        return redirect("admin_user_detail", username=user.username)
    
    return redirect("admin_user_detail", username=user.username)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def kyc(request):
    kycs = KYCVerification.objects.all()
    today = date.today()

    # --- Compute counts dynamically ---
    pending_count = KYCVerification.objects.filter(status='pending').count()
    approved_today = KYCVerification.objects.filter(status='verified', approved_on__date=today).count()
    rejected_today = KYCVerification.objects.filter(status='unverified', approved_on__date=today).count()
    total_verified_users = KYCVerification.objects.filter(status='verified').count()
    if 'accept' in request.POST:
        # --- Get form values ---
        send_email = request.POST.get('send_email')
        send_inapp = request.POST.get('send_inapp')
        action_ref = request.POST.get('action')

        kyc = KYCVerification.objects.get(ref=action_ref)

        # --- Confirm matching KYC ref ---
        if str(kyc.ref) != action_ref:
            messages.error(request, "Invalid request reference.")
            return redirect('kyc_list')

        # --- Approve the KYC ---
        kyc.status = 'approved'
        kyc.save()

        kyc.user.complete_kyc_verification = True
        kyc.user.verified_email = True
        kyc.user.kyc_verification_status = 'verified'
        kyc.user.kyc_status = 'verified'
        kyc.user.verified_kyc = True
        kyc.user.save()

        # --- Send Email Notification ---
        if send_email:
            subject = "✅ KYC Approved"
            message = (
                f"Dear {kyc.first_name},\n\n"
                "Your KYC verification has been successfully approved.\n"
                "Your account has been upgraded to Level 3 access.\n\n"
                "Thank you for verifying your identity.\n"
                "Best regards,\n"
                "The Support Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [kyc.user.email],
                fail_silently=True
            )

        # --- Send In-App Notification ---
        if send_inapp:
            Notification.objects.create(
                user=kyc.user,
                title="KYC Approved 🎉",
                media_type="text",
                text="KA",
            )

        messages.success(request, f"KYC for {kyc.first_name} {kyc.last_name} has been approved.")
        return redirect('admin_kyc_approvals')
    
    elif 'reject' in request.POST:
        # --- Get form values ---
        send_email = request.POST.get('send_email')
        send_inapp = request.POST.get('send_inapp')
        action_ref = request.POST.get('action')
        reason = request.POST.get('rejection_reason')

        kyc = KYCVerification.objects.get(ref=action_ref)

        # --- Reject the KYC ---
        kyc.status = 'rejected'
        kyc.save()

        # --- Update user verification fields ---
        kyc.user.complete_kyc_verification = False
        kyc.user.verified_email = False
        kyc.user.kyc_verification_status = 'unverified'
        kyc.user.kyc_status = 'unverified'
        kyc.user.save()

        # --- Send Email Notification ---
        if send_email:
            subject = "❌ KYC Rejected"
            message = (
                f"Dear {kyc.first_name},\n\n"
                "We regret to inform you that your KYC verification was rejected after review.\n"
                "Please ensure that the information provided matches your government-issued ID "
                "and that your documents are clear and valid.\n\n"
                "You may re-submit your KYC details for verification by logging into your account.\n\n"
                f"reason: {reason}"
                "Best regards,\n"
                "The Support Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [kyc.user.email],
                fail_silently=True
            )

        # --- Send In-App Notification ---
        if send_inapp:
            Notification.objects.create(
                user=kyc.user,
                title="KYC Rejected ⚠️",
                media_type="text",
                text="KR"
            )

        messages.warning(request, f"KYC for {kyc.first_name} {kyc.last_name} has been rejected.")
        return redirect('admin_kyc_approvals')
    
    context = {
        'header_title': 'KYC Approvals',
        'body_class': 'page-admin-kyc',
        'kycs':kycs,
        'pending_count': pending_count,
        'approved_today': approved_today,
        'rejected_today': rejected_today,
        'total_verified_users': total_verified_users,
    }
    return render(request, 'manager/kyc_approval.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def activity_log(request):
    context = {
        'header_title': 'User Activity Logs',
        'body_class': 'page-user-activity'
    }
    return render(request, 'manager/activity_log.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def deposit_list(request):
    deposits = Deposit.objects.all()

    today = timezone.now().date()

    # --- Stats ---
    total_deposits = deposits.count()
    total_amount_today = deposits.filter(date_created__date=today).aggregate(total=Sum('grand_total'))['total'] or 0
    pending_count = deposits.filter(status='pending').count()
    completed_today = deposits.filter(status='completed', date_created__date=today).count()
    failed_today = deposits.filter(status='failed', date_created__date=today).count()

    if 'approve' in request.POST:
        print('pahss')
        print(request.POST)
        deposit_ref = request.POST.get('deposit_id')
        credit_amount = request.POST.get('credit_amount')

        print(deposit_ref, credit_amount)

        # --- Validate form ---
        if not deposit_ref or not credit_amount:
            messages.error(request, "Invalid form submission.")
            return redirect('admin_deposit_list')
        

        # --- Get Deposit Object ---
        deposit = get_object_or_404(Deposit, ref=deposit_ref)

        # --- Check status ---
        if deposit.status.lower() == 'success':
            messages.warning(request, f"Deposit #{deposit.transaction_no} has already been processed.")
            return redirect('admin_deposit_list')

        # --- Credit the user's wallet ---
        try:
            wallet = User.objects.get(id=deposit.user.id)
            wallet.deposit += float(credit_amount)
            wallet.save()

            # --- Update deposit record ---
            deposit.status = 'success'
            deposit.approved_amount = float(credit_amount)
            deposit.approved_on = timezone.now()
            deposit.save()

            # # --- Send in-app notification ---
            # Notification.objects.create(
            #     user=deposit.user,
            #     title="Deposit Approved 💰",
            #     message=f"Your deposit of ${credit_amount} has been approved and credited to your {deposit.deposit_to.capitalize()} wallet.",
            #     media_type="text",
            #     text="DA",
            # )

            # # --- Send email notification ---
            # send_mail(
            #     subject="✅ Deposit Approved",
            #     message=f"Dear {deposit.user.first_name},\n\nYour deposit of ${credit_amount} has been approved and credited to your wallet.\n\nThank you for using our platform.\n\nBest regards,\nSupport Team",
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[deposit.user.email],
            #     fail_silently=True
            # )

            messages.success(request, f"Deposit #{deposit.transaction_no} successfully approved and credited.")
            return redirect('admin_deposit_list')

        except User.DoesNotExist:
            messages.error(request, "User wallet not found for this deposit.")
            return redirect('admin_deposit_list')
        
    elif 'reject' in request.POST:
        deposit_ref = request.POST.get('deposit_id')
        rejection_reason = request.POST.get('rejection_reason', 'No specific reason provided.')

        if not deposit_ref:
            messages.error(request, "Invalid rejection request.")
            return redirect('admin_deposit_list')
        
        print(request.POST)

        deposit = get_object_or_404(Deposit, ref=deposit_ref)

        if deposit.status.lower() in ['completed', 'rejected']:
            messages.warning(request, f"Deposit #{deposit.transaction_no} has already been processed.")
            return redirect('admin_deposit_list')

        deposit.status = 'rejected'
        deposit.save()

        # --- In-app Notification ---
        Notification.objects.create(
            user=deposit.user,
            title="Deposit Rejected ❌",
            media_type="text",
            text="DR",
        )

        # --- Email Notification ---
        send_mail(
            subject="❌ Deposit Rejected",
            message=(
                f"Dear {deposit.user.first_name},\n\n"
                f"Your deposit of ${deposit.amount} has been rejected.\n"
                f"Reason: {rejection_reason}\n\n"
                f"If you believe this was an error, please contact support.\n\n"
                f"Best regards,\nSupport Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[deposit.user.email],
            fail_silently=True
        )

        messages.success(request, f"Deposit #{deposit.transaction_no} has been rejected.")
        return redirect('admin_deposit_list')

    context = {
        'header_title': 'Deposits Management',
        'body_class': 'page-admin-deposits',
        'deposits': deposits,
        'total_deposits': total_deposits,
        'total_amount_today': total_amount_today,
        'pending_count': pending_count,
        'completed_today': completed_today,
        'failed_today': failed_today,
    }

    return render(request, 'manager/deposit_list.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def withdrawal_list(request):
    # Get all withdrawals
    withdraws = Withdraw.objects.all()

    # Get today's date
    today = timezone.now().date()

    # Filter today's withdrawals
    todays_withdrawals = withdraws.filter(date__date=today)

    # Compute dynamic stats
    total_withdrawals_count = withdraws.count()
    total_withdrawals_today = todays_withdrawals.aggregate(total=Sum('amount'))['total'] or 0
    pending_approval = withdraws.filter(status='pending').count()
    completed_today = todays_withdrawals.filter(status='completed').count()
    rejected_today = todays_withdrawals.filter(status='rejected').count()

    if 'approve' in request.POST:
        ref = request.POST.get('action')

        try:
            withdrawal = Withdraw.objects.get(ref=ref)
        except Withdraw.DoesNotExist:
            messages.error(request, "Withdrawal not found.")
            return redirect('admin_withdrawal_list')

        # --- Update status ---
        withdrawal.status = 'success'
        withdrawal.save()

        withdrawal.user.balance = withdrawal.user.balance - withdrawal.amount
        withdrawal.user.save()

        amount = withdrawal.amount
        user = withdrawal.user

        # --- Send in-app notification ---
        Notification.objects.create(
            user=user,
            title="Withdrawal Approved 💸",
            media_type="text",
            text="WA",
            color="success",
        )

        # --- Send email notification ---
        send_mail(
            subject="✅ Withdrawal Approved",
            message=(
                f"Dear {user.first_name},\n\n"
                f"Your withdrawal request of ${amount} has been approved and processed successfully.\n\n"
                f"Thank you for using our platform.\n\n"
                f"Best regards,\nSupport Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )

        # --- Success message ---
        messages.success(request, f"Withdrawal #{withdrawal.ref} successfully approved and processed.")
        return redirect('admin_withdrawal_list')
    
    elif 'reject' in request.POST:
        ref = request.POST.get('action')

        try:
            withdrawal = Withdraw.objects.get(ref=ref)
        except Withdraw.DoesNotExist:
            messages.error(request, "Withdrawal not found.")
            return redirect('admin_withdrawal_list')

        withdrawal.status = 'rejected'
        withdrawal.save()

        amount = withdrawal.amount
        user = withdrawal.user

        # --- Send in-app notification ---
        Notification.objects.create(
            user=user,
            title="Withdrawal Rejected ❌",
            media_type="text",
            text="WR",
            color="danger",
        )

        # --- Send email notification ---
        send_mail(
            subject="❌ Withdrawal Rejected",
            message=(
                f"Dear {user.first_name},\n\n"
                f"Your withdrawal request of ${amount} has been rejected.\n"
                f"If you believe this was an error, please contact support.\n\n"
                f"Best regards,\nSupport Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )

        messages.warning(request, f"Withdrawal #{withdrawal.ref} has been rejected.")
        return redirect('admin_withdrawal_list')

    context = {
        'header_title': 'Withdrawals Management',
        'body_class': 'page-admin-withdrawals',
        'withdraws': withdraws,
        'total_withdrawals_count': total_withdrawals_count,
        'total_withdrawals_today': total_withdrawals_today,
        'pending_approval': pending_approval,
        'completed_today': completed_today,
        'rejected_today': rejected_today,
    }
    return render(request, 'manager/withdrawal_list.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def payment_method(request):
    currencies = Currency.objects.all()
    gateways = PaymentGateway.objects.all()
    if "switch" in request.POST:

        crypto_id = request.POST.get("crypto_id")
        
        currency = Currency.objects.filter(ref=crypto_id).first()
        if not currency:
            messages.error(request, 'Currency not found.')
            return redirect('admin_payment_methods')
        
        currency.status = not currency.status
        currency.save()

        messages.success(request, f'{currency.abbr} status updated successfully.')
        return redirect('admin_payment_methods')
    
    elif 'update' in request.POST:
        name = request.POST.get('crypto_name')
        symbol = request.POST.get('crypto_symbol')
        network = request.POST.get('crypto_network')
        memo = request.POST.get('crypto_memo')
        address = request.POST.get('crypto_address')
        fee = request.POST.get('crypto_fee')
        min_deposit = request.POST.get('crypto_min_deposit')
        crypto_id = request.POST.get("crypto_id")

        currency = Currency.objects.filter(ref=crypto_id).first()
        if not currency:
            messages.error(request, 'Currency not found.')
            return redirect('admin_payment_methods')

        # Update fields
        currency.currency = name
        currency.abbr = symbol
        currency.network = network
        currency.instructions = memo
        currency.address = address
        currency.transaction_fee = fee
        currency.minimum_deposit = min_deposit

        qr = qrcode.make(address)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"{symbol.lower()}_{network.lower()}_qr.png"
        currency.qrcode.save(filename, ContentFile(buffer.getvalue()), save=False)

        currency.save()
        messages.success(request, f"{symbol} updated successfully.")
        return redirect('admin_payment_methods')

    elif 'delete' in request.POST:
        crypto_id = request.POST.get("crypto_id")
        
        currency = Currency.objects.filter(ref=crypto_id).first()
        if not currency:
            messages.error(request, 'Currency not found.')
            return redirect('admin_payment_methods')
        
        currency.delete()

        messages.success(request, 'Successful.')
        return redirect('admin_payment_methods')
    
    elif 'add' in request.POST:
        name = request.POST.get('crypto_name')
        symbol = request.POST.get('crypto_symbol')
        network = request.POST.get('crypto_network')
        memo = request.POST.get('crypto_memo')
        address = request.POST.get('crypto_address')
        fee = request.POST.get('crypto_fee')
        min_deposit = request.POST.get('crypto_min_deposit')

        qr = qrcode.make(address)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"{symbol.lower()}_{network.lower()}_qr.png"

        crypto = Currency.objects.create(
            currency=name,
            abbr=symbol,
            network=network,
            transaction_fee=fee,
            minimum_deposit=min_deposit,
            address=address,
            instructions=memo,
        )
        crypto.qrcode.save(filename, ContentFile(buffer.getvalue()), save=True)

        messages.success(request, "Added")
        return redirect('admin_payment_methods')
    
    elif 'add_gateway' in request.POST:
        name = request.POST.get('gateway_name')
        email = request.POST.get('gateway_email')
        memo = request.POST.get('gateway_memo')
        fee = request.POST.get('gateway_fee')
        min_amount = request.POST.get('gateway_min_amount')

        PaymentGateway.objects.create(
            name=name,
            email=email,
            min_amount=min_amount,
            transaction_fee=fee,
        )

        messages.success(request, 'Added')
        return redirect('admin_payment_methods')
    
    elif 'update_gateway' in request.POST:
        crypto_id = request.POST.get("gateway_id")
        name = request.POST.get('gateway_name')
        email = request.POST.get('gateway_email')
        memo = request.POST.get('gateway_memo')
        fee = request.POST.get('gateway_fee')
        min_amount = request.POST.get('gateway_min_amount')

        gateway = PaymentGateway.objects.filter(ref=crypto_id).first()
        if not gateway:
            messages.error(request, 'Gateway not found.')
            return redirect('admin_payment_methods')

        gateway.name = name
        gateway.email = email
        gateway.instructions = memo
        gateway.transaction_fee = fee
        gateway.min_amount = min_amount
        gateway.save()

        messages.success(request, f"{name} updated successfully.")
        return redirect('admin_payment_methods')
    
    elif "gateway_switch" in request.POST:

        crypto_id = request.POST.get("gateway_id")

        print(crypto_id)
        
        currency = PaymentGateway.objects.filter(ref=crypto_id).first()
        if not currency:
            messages.error(request, 'Currency not found.')
            return redirect('admin_payment_methods')
        
        currency.status = not currency.status
        currency.save()

        messages.success(request, f'status updated successfully.')
        return redirect('admin_payment_methods')
    
    elif 'gateway_delete' in request.POST:
        crypto_id = request.POST.get("gateway_id")

        print(crypto_id)
        
        currency = PaymentGateway.objects.filter(ref=crypto_id).first()
        if not currency:
            messages.error(request, 'Currency not found.')
            return redirect('admin_payment_methods')
        
        currency.delete()

        messages.success(request, 'Successful.')
        return redirect('admin_payment_methods')
    context = {
        'header_title': 'Payment Methods Management',
        'body_class': 'page-admin-payments',
        'currencies': currencies,
        'gateways': gateways,
    }
    return render(request, 'manager/payment_method.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def plan_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # === Create new plan ===
        if action == 'create_plan':
            plan_type = request.POST.get('plan_type')
            tier = request.POST.get('plan_tier')
            price = request.POST.get('plan_price')
            features = request.POST.get('plan_features')

            try:
                category, _ = PlanCategory.objects.get_or_create(name=plan_type.capitalize())
                Plan.objects.create(
                    category=category,
                    tier=tier,
                    price=price,
                    features=features,
                    has_currency_select=(plan_type.lower() == 'mining')
                )
                messages.success(request, f"{tier} plan added successfully under {plan_type.capitalize()}.")
            except Exception as e:
                messages.error(request, f"Error creating plan: {e}")

            return redirect('admin_plan_management')

        # === Update plan ===
        elif action == 'save_plan':
            plan_id = request.POST.get('plan_id')
            try:
                plan = Plan.objects.get(id=plan_id)
                plan.price = request.POST.get('price', plan.price)
                plan.features = "\n".join(request.POST.getlist('features[]'))
                plan.save()
                messages.success(request, f"{plan.tier} plan updated successfully.")
            except Plan.DoesNotExist:
                messages.error(request, "Plan not found.")
            return redirect('admin_plan_management')

        # === Delete plan ===
        elif action == 'delete_plan':
            plan_id = request.POST.get('plan_id')
            Plan.objects.filter(id=plan_id).delete()
            messages.success(request, "Plan deleted successfully.")
            return redirect('admin_plan_management')

    # === Fetch all categories ===
    categories = PlanCategory.objects.prefetch_related('plans').all()

    context = {
        'header_title': 'Plans Management',
        'body_class': 'page-admin-plans',
        'categories': categories,
    }
    return render(request, 'manager/plan_management.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def trader_list(request):
    traders = Trader.objects.all()
    if request.method == 'POST':
        ref = request.POST.get('ref')

        trader = Trader.objects.get(ref=ref)
        trader.delete()

        messages.success(request, 'Done')
        return redirect('admin_trader_list')
    context = {
        'header_title': 'Traders Management',
        'body_class': 'page-admin-traders',
        'traders':traders,
    }
    return render(request, 'manager/trader_list.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def trader_edit(request, ref):
    trader = get_object_or_404(Trader, ref=ref)

    if request.method == 'POST':
        form = TraderForm(request.POST, request.FILES, instance=trader)
        if form.is_valid():
            form.save()
            # Optional: add success message
            from django.contrib import messages
            messages.success(request, 'Trader updated successfully!')
            return redirect('admin_trader_list')  # Redirect to list page after saving
    else:
        form = TraderForm(instance=trader)

    context = {
        'header_title': 'Edit Trader',
        'body_class': 'page-admin-trader-edit',
        'form': form,
        'trader': trader,
    }
    return render(request, 'manager/trader_edit.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def trader_add(request):
    if request.method == 'POST':
        full_name = request.POST.get('trader_name')
        username = request.POST.get('username')
        profit_share = request.POST.get('profit_share') or 0
        min_balance = request.POST.get('min_balance') or 0
        copy_mode = request.POST.get('copy_mode') or 'flexible'
        require_approval = request.POST.get('require_approval') == '1'
        badge = request.POST.get('badge') or 'none'
        bio = request.POST.get('bio')
        win = request.POST.get('total_wins') or 0
        lose = request.POST.get('total_losses') or 0
        win_rate = request.POST.get('win_rate') or 0
        is_active = request.POST.get('is_active') == '1'
        image = request.FILES.get('profile_photo')

        # --- Validation ---
        if not full_name or not username:
            messages.error(request, "Full name and username are required.")
            return redirect('admin_trader_list')

        if Trader.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_trader_list')

        # --- Create trader ---
        trader = Trader.objects.create(
            full_name=full_name,
            username=username,
            profit_share=float(profit_share),
            min_balance=float(min_balance),
            copy_mode=copy_mode,
            require_approval=require_approval,
            badge=badge,
            bio=bio,
            win=int(win),
            lose=int(lose),
            win_rate=float(win_rate),
            is_active=is_active,
            created_by=request.user,
        )

        # Save image if provided
        if image:
            trader.image = image
            trader.save()

        messages.success(request, f"Trader '{full_name}' added successfully.")
        return redirect('admin_trader_list')

    # --- GET request ---
    context = {
        'header_title': 'Add Trader',
        'body_class': 'page-admin-traderadd',
    }
    return render(request, 'manager/trader_add.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def trader_applications(request):
    # --- Handle Approve / Reject Actions ---
    if request.method == "POST":
        action = request.POST.get("action")
        app_id = request.POST.get("application_id")
        try:
            application = TraderApplication.objects.get(id=app_id)
        except TraderApplication.DoesNotExist:
            messages.error(request, "Application not found.")
            return redirect("admin_trader_applications")

        if action == "approve_application":
            # TODO: Add application to trader list
            application.status = "approved"
            messages.success(request, f"{application.full_name}'s application has been approved ✅")
        elif action == "reject_application":
            application.status = "rejected"
            messages.warning(request, f"{application.full_name}'s application has been rejected ❌")
        application.save()
        return redirect("admin_trader_applications")

    # --- Filters ---
    status = request.GET.get("status")
    experience = request.GET.get("experience")
    search = request.GET.get("search")

    applications = TraderApplication.objects.all().order_by("-submitted_at")

    if status:
        applications = applications.filter(status=status)
    if experience:
        applications = applications.filter(experience=experience)
    if search:
        applications = applications.filter(
            Q(full_name__icontains=search) | Q(email__icontains=search)
        )

    # --- Stats ---
    stats = {
        "pending": TraderApplication.objects.filter(status="pending").count(),
        "under_review": TraderApplication.objects.filter(status="under-review").count(),
        "approved": TraderApplication.objects.filter(status="approved").count(),
        "rejected": TraderApplication.objects.filter(status="rejected").count(),
    }

    context = {
        "header_title": "Trader Applications",
        "body_class": "page-admin-traderapps",
        "applications": applications,
        "stats": stats,
    }
    return render(request, "manager/trader_application.html", context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def copy_requests(request):
    # Handle approval/rejection
    if request.method == "POST":
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        copy_request = CopiedTrader.objects.get(id=request_id)

        if action == 'approve':
            copy_request.status = 'approved'

            messages.success(request, f"Copy request from {copy_request.user.username} approved.")
        elif action == 'reject':
            copy_request.status = 'rejected'
            messages.warning(request, f"Copy request from {copy_request.user.username} rejected.")
        copy_request.save()
        return redirect('copy_requests')

    # Fetch all pending requests
    pending_requests = CopiedTrader.objects.filter(status='pending')

    # Calculate summary stats
    today = timezone.now().date()
    approved_today = CopiedTrader.objects.filter(status='approved', created_on__date=today).count()
    rejected_today = CopiedTrader.objects.filter(status='rejected', created_on__date=today).count()
    active_copy_trades = CopiedTrader.objects.filter(status='approved').count()

    context = {
        'header_title': 'Copy Trading Requests',
        'body_class': 'page-admin-copyrequests',
        'pending_requests': pending_requests,
        'stats': {
            'pending': pending_requests.count(),
            'approved_today': approved_today,
            'rejected_today': rejected_today,
            'active': active_copy_trades
        }
    }
    return render(request, 'manager/copy_request.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def take_trade(request):
    context = {
        'header_title': 'Take Trade',
        'body_class': 'page-take-trade'
    }

    if request.method == 'POST' and request.POST.get('action') == 'execute_trade':
        try:
            user_id = request.POST.get('user_id')
            trader_id = request.POST.get('trader_id')
            market_type = request.POST.get('market_type')
            asset = request.POST.get('asset')
            direction = request.POST.get('direction')
            amount = request.POST.get('amount')
            duration = request.POST.get('duration')
            outcome = request.POST.get('outcome')
            outcome_amount = request.POST.get('outcome_amount')

            # --- Get related objects ---
            user = User.objects.get(id=user_id)
            trader = Trader.objects.get(username=trader_id)

            # --- Create trade record ---
            # ManualTrade.objects.create(
            #     user=user,
            #     trader=trader,
            #     market_type=market_type,
            #     asset=asset,
            #     direction=direction,
            #     amount=amount,
            #     duration=duration,
            #     outcome=outcome,
            #     outcome_amount=outcome_amount,
            # )

            # CopiedTrader.objects.create(

            # )

            messages.success(request, f"Trade executed successfully for {user.username}.")
            return redirect('take_trade')  # You can change redirect as needed

        except User.DoesNotExist:
            messages.error(request, "Invalid user selected.")
        except Trader.DoesNotExist:
            messages.error(request, "Invalid trader selected.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    # Load dropdown data
    context['users'] = User.objects.all()
    context['traders'] = Trader.objects.all()

    return render(request, 'manager/take_trade.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def become_trader(request):
    if request.method == "POST":
        card_id = request.POST.get("card_id")

        # DELETE
        if request.POST.get("action") == "delete" and card_id:
            benefit = get_object_or_404(TraderBenefit, id=card_id)
            benefit.delete()
            return redirect("admin_become_trader")

        # ADD or UPDATE
        icon = request.POST.get("card_icon")
        title = request.POST.get("card_title")
        description = request.POST.get("card_description")

        if card_id:
            # UPDATE
            benefit = get_object_or_404(TraderBenefit, id=card_id)
            benefit.icon = icon
            benefit.title = title
            benefit.description = description
            benefit.save()
        else:
            # CREATE
            TraderBenefit.objects.create(
                icon=icon,
                title=title,
                description=description,
                order=TraderBenefit.objects.count() + 1
            )

        return redirect("admin_become_trader")

    # List all benefits
    benefits = TraderBenefit.objects.all()
    context = {
        'header_title': 'Manage Trader Benefits',
        'body_class': 'page-admin-becometrader',
        "benefits": benefits,
    }
    return render(request, 'manager/become_trader.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def send_notification(request):
    context = {
        'header_title': 'Send Notification',
        'body_class': 'page-admin-notifications'
    }
    return render(request, 'manager/notifications.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def email_template(request):
    context = {
        'header_title': 'Email Templates',
        'body_class': 'page-email-templates'
    }
    return render(request, 'manager/email_template.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def frontpage_manager(request):
    context = {
        'header_title': 'Page Manager',
        'body_class': 'page-admin-frontendpages'
    }
    return render(request, 'manager/frontpage_manager.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def platform_setting(request):
    context = {
        'header_title': 'Platform Settings',
        'body_class': 'page-admin-platformsettings'
    }
    return render(request, 'manager/platform_setting.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def verification_setting(request):
    context = {
        'header_title': 'Verification Settings',
        'body_class': 'page-admin-verifysettings'
    }
    return render(request, 'manager/verification_setting.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def page_content(request):
    context = {
        'header_title': 'Page Content Management',
        'body_class': 'page-admin-pagecontent'
    }
    return render(request, 'manager/page_content.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def admin_profile(request):
    context = {
        'header_title': 'Admin Profile',
        'body_class': 'page-admin-profile'
    }
    return render(request, 'manager/admin_profile.html', context)

@login_required(login_url='admin_login')
@allowed_users(allowed_roles=['admin'])
def reports(request):
    context = {
        'header_title': 'Reports & Analytics',
        'body_class': 'page-admin-reports'
    }
    return render(request, 'manager/report.html', context)

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_qs = User.objects.filter(username=username).first()
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.password_reset:
                return redirect('password_reset', username=user.username)

            return redirect('admin_home')

        else:
            if user_qs and not user_qs.is_active:
                messages.error(request, 'Your account is not active.')
            else:
                messages.error(request, 'Incorrect email or password.')

            return redirect('admin_login')
    context = {
        
    }
    return render(request, 'manager/login.html', context)