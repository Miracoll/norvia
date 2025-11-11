from datetime import date
import io
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.core.files.base import ContentFile
from django.contrib import messages
import qrcode
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum

from account.models import Currency, Deposit, KYCVerification, Notification, PaymentGateway, Plan, PlanCategory, Trader, User, Withdraw
from manager.forms import TraderForm

# Create your views here.

def dashboard(request):
    context = {
        'header_title': 'Admin Dashboard',
        'body_class': 'page-admin-dashboard'
    }
    return render(request, 'manager/dashboard.html', context)

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

def user_detail(request, username):
    user = User.objects.get(username=username)
    context = {
        'header_title': 'User Details',
        'body_class': 'page-admin-userdetails',
        'user':user,
    }
    return render(request, 'manager/user_detail.html', context)

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
                message="Your KYC verification has been approved and your account has been upgraded.",
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
                message="Your KYC verification has been rejected. Please re-submit valid documents for review.",
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

def activity_log(request):
    context = {
        'header_title': 'User Activity Logs',
        'body_class': 'page-user-activity'
    }
    return render(request, 'manager/activity_log.html', context)

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
            wallet.balance += float(credit_amount)
            wallet.save()

            # --- Update deposit record ---
            deposit.status = 'success'
            deposit.save()

            # --- Send in-app notification ---
            Notification.objects.create(
                user=deposit.user,
                title="Deposit Approved 💰",
                message=f"Your deposit of ${credit_amount} has been approved and credited to your {deposit.deposit_to.capitalize()} wallet."
            )

            # --- Send email notification ---
            send_mail(
                subject="✅ Deposit Approved",
                message=f"Dear {deposit.user.first_name},\n\nYour deposit of ${credit_amount} has been approved and credited to your wallet.\n\nThank you for using our platform.\n\nBest regards,\nSupport Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[deposit.user.email],
                fail_silently=True
            )

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
            message=f"Your deposit of ${deposit.amount} was rejected. Reason: {rejection_reason}"
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

        messages.error(request, f"Deposit #{deposit.transaction_no} has been rejected.")
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
            message=f"Your withdrawal request of ${amount} has been approved. The funds will be transferred to your account shortly."
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
            message=f"Your withdrawal of ${amount} has been rejected."
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

def trader_add(request):
    if request.method == 'POST':
        print(request.POST)
        full_name = request.POST.get('trader_name')
        username = request.POST.get('username')
        profit_share = request.POST.get('profit_share')
        min_balance = request.POST.get('min_balance')
        copy_mode = request.POST.get('copy_mode')
        require_approval = request.POST.get('require_approval') == 'on'
        badge = request.POST.get('badge')
        bio = request.POST.get('bio')
        image = request.FILES.get('profile_photo')

        # --- Validation (optional but recommended) ---
        if not full_name or not username:
            print(1)
            messages.error(request, "Full name and username are required.")
            return redirect('admin_trader_list')

        if Trader.objects.filter(username=username).exists():
            print(2)
            messages.error(request, "Username already exists.")
            return redirect('admin_trader_list')
        
        print(3)

        # --- Create trader ---
        trader = Trader.objects.create(
            full_name=full_name,
            username=username,
            profit_share=profit_share or 0,
            min_balance=min_balance or 0,
            copy_mode=copy_mode or 'flexible',
            require_approval=require_approval,
            badge=badge or 'none',
            bio=bio,
            created_by=request.user,
        )

        # Save image if provided
        if image:
            trader.image = image
            trader.save()

        messages.success(request, f"Trader '{full_name}' added successfully.")
        return redirect('admin_trader_list')  # Change to your trader list URL name

    # --- GET request (show form) ---
    context = {
        'header_title': 'Add Trader',
        'body_class': 'page-admin-traderadd',
    }
    return render(request, 'manager/trader_add.html', context)

def trader_applications(request):
    context = {
        'header_title': 'Trader Applications',
        'body_class': 'page-admin-traderapps'
    }
    return render(request, 'manager/trader_application.html', context)

def copy_requests(request):
    context = {
        'header_title': 'Copy Trading Requests',
        'body_class': 'page-admin-copyrequests'
    }
    return render(request, 'manager/copy_request.html', context)

def take_trade(request):
    context = {
        'header_title': 'Take Trade',
        'body_class': 'page-take-trade'
    }
    return render(request, 'manager/take_trade.html', context)

def become_trader(request):
    context = {
        'header_title': 'Manage Trader Benefits',
        'body_class': 'page-admin-becometrader'
    }
    return render(request, 'manager/become_trader.html', context)

def send_notification(request):
    context = {
        'header_title': 'Send Notification',
        'body_class': 'page-admin-notifications'
    }
    return render(request, 'manager/notifications.html', context)

def email_template(request):
    context = {
        'header_title': 'Email Templates',
        'body_class': 'page-email-templates'
    }
    return render(request, 'manager/email_template.html', context)

def frontpage_manager(request):
    context = {
        'header_title': 'Page Manager',
        'body_class': 'page-admin-frontendpages'
    }
    return render(request, 'manager/frontpage_manager.html', context)

def platform_setting(request):
    context = {
        'header_title': 'Platform Settings',
        'body_class': 'page-admin-platformsettings'
    }
    return render(request, 'manager/platform_setting.html', context)

def verification_setting(request):
    context = {
        'header_title': 'Verification Settings',
        'body_class': 'page-admin-verifysettings'
    }
    return render(request, 'manager/verification_setting.html', context)

def page_content(request):
    context = {
        'header_title': 'Page Content Management',
        'body_class': 'page-admin-pagecontent'
    }
    return render(request, 'manager/page_content.html', context)

def admin_profile(request):
    context = {
        'header_title': 'Admin Profile',
        'body_class': 'page-admin-profile'
    }
    return render(request, 'manager/admin_profile.html', context)

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