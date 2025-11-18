from decimal import Decimal
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.contrib.auth.views import PasswordResetView

from account.models import AddressVerification, CopiedTrader, Currency, Deposit, KYCVerification, PaymentGateway, Plan, PlanCategory, Trade, Trader, TraderApplication, User, Withdraw, PasswordHistory
from account.utils import telegram
from utils.decorators import allowed_users

# Create your views here.

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def home(request):
    copied_trader = CopiedTrader.objects.filter(user=request.user)
    trades = Trade.objects.filter(user=request.user)

    open_trades = trades.filter(status='open')
    closed_trades = trades.filter(status='closed')

    context = {
        'class_value': 'page-dashboard',
        'traders': copied_trader,
        'open_trades': open_trades,
        'closed_trades': closed_trades,
    }
    return render(request, 'account/dashboard.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def stop_copying(request, pk):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("dashboard")  # adjust to your dashboard route name

    copied_trader = get_object_or_404(CopiedTrader, ref=pk)

    # Prevent deleting other people's copied traders
    if copied_trader.user != request.user:
        messages.error(request, "You do not have permission to stop copying this trader.")
        return redirect("dashboard")

    copied_trader.delete()
    messages.success(request, "You have successfully stopped copying this trader.")

    return redirect("dashboard")

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def crypto_market(request):
    # Fetch open trades
    open_trades = Trade.objects.filter(user=request.user, status='open', asset='crypto')

    # Check if any open trade's duration has elapsed
    for trade in open_trades:
        elapsed_time = timezone.now() - trade.opened_at
        if elapsed_time >= timedelta(minutes=trade.duration):
            trade.status = 'closed'
            trade.closed_at = timezone.now()

            # Ensure numeric types
            entry_price = float(trade.entry_price)
            current_price = float(trade.current_price)
            size = float(trade.size)

            if trade.trade_type == 'buy':  # Long
                trade.pnl = (current_price - entry_price) * size
            else:  # Short
                trade.pnl = (entry_price - current_price) * size

            # Safe percent calculation
            if entry_price * size != 0:
                trade.pnl_percent = (trade.pnl / (entry_price * size)) * 100
            else:
                trade.pnl_percent = 0.0

            trade.save()

    # Fetch updated open and closed trades
    open_trades = Trade.objects.filter(user=request.user, status='open', asset='crypto').order_by('-opened_at')
    closed_trades = Trade.objects.filter(user=request.user, status='closed', asset='crypto').order_by('-opened_at')

    context = {
        'open_trades': open_trades,
        'closed_trades': closed_trades,
        'header_title': 'Crypto Market',
        'body_class': 'page-cryptomarket',
    }
    return render(request, 'account/crypto_market.html', context)

@login_required
def place_trade(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)

            # Extract and validate input
            symbol = data.get('symbol')
            trade_type = data.get('trade_type')  # 'buy' or 'sell'
            mode = data.get('mode', 'spot')      # 'spot' or 'leverage'
            leverage = data.get('leverage') or None
            entry_price = float(data.get('entry_price', 0))
            current_price = float(data.get('current_price', entry_price))
            duration = int(data.get('duration', 1))
            amount = float(data.get('amount', 0))
            asset = data.get('asset')

            if not symbol or not trade_type or amount <= 0 or entry_price <= 0:
                return JsonResponse({'success': False, 'message': 'Invalid trade data provided.'}, status=400)

            # Check user balance
            if amount > request.user.deposit:
                return JsonResponse({'success': False, 'message': 'Insufficient balance.'}, status=400)

            # Calculate size
            size = amount / entry_price

            # Calculate initial PnL (usually 0 at entry)
            if trade_type == 'buy':  # Long
                pnl = (current_price - entry_price) * size
            else:  # Short
                pnl = (entry_price - current_price) * size

            pnl_percent = (pnl / (entry_price * size)) * 100 if size > 0 else 0

            print(symbol, trade_type, mode, leverage, size, entry_price, current_price, duration, pnl, pnl_percent)

            # Create trade
            trade = Trade.objects.create(
                user=request.user,
                symbol=symbol,
                trade_type=trade_type,
                mode=mode,
                leverage=leverage,
                size=size,
                entry_price=entry_price,
                current_price=current_price,
                duration=duration,
                pnl=pnl,
                pnl_percent=pnl_percent,
                asset=asset,
                status='open',
                opened_at=timezone.now(),
            )

            # Deduct amount from user's balance
            request.user.deposit -= amount
            request.user.save()

            return JsonResponse({
                'success': True,
                'message': 'Trade placed successfully!',
                'redirect_url': '/crypto_market/'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def stock_market(request):
    # Fetch open trades
    open_trades = Trade.objects.filter(user=request.user, status='open', asset='stock')

    # Check if any open trade's duration has elapsed
    for trade in open_trades:
        elapsed_time = timezone.now() - trade.opened_at
        if elapsed_time >= timedelta(minutes=trade.duration):
            trade.status = 'closed'
            trade.closed_at = timezone.now()

            # Ensure numeric types
            entry_price = float(trade.entry_price)
            current_price = float(trade.current_price)
            size = float(trade.size)

            if trade.trade_type == 'buy':  # Long
                trade.pnl = (current_price - entry_price) * size
            else:  # Short
                trade.pnl = (entry_price - current_price) * size

            # Safe percent calculation
            if entry_price * size != 0:
                trade.pnl_percent = (trade.pnl / (entry_price * size)) * 100
            else:
                trade.pnl_percent = 0.0

            trade.save()

    # Fetch updated open and closed trades
    open_trades = Trade.objects.filter(user=request.user, status='open', asset='stock').order_by('-opened_at')
    closed_trades = Trade.objects.filter(user=request.user, status='closed', asset='stock').order_by('-opened_at')
    context = {
        'open_trades': open_trades,
        'closed_trades': closed_trades,
        'class_value': 'page-stockmarket'
    }
    return render(request, 'account/stock_market.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def copy_trader(request):
    # Get all the traders this user has already copied
    copied_trades = CopiedTrader.objects.filter(user=request.user)

    # Extract the trader IDs that the user already copied
    copied_trader_ids = copied_trades.values_list('trader_id', flat=True)

    # Exclude those traders from the full Trader list
    traders = Trader.objects.exclude(id__in=copied_trader_ids)

    if 'copy_trader' in request.POST:
        amount = request.POST.get('amount')
        allocation = request.POST.get('allocation')
        leverage = request.POST.get('leverage')
        ref = request.POST.get('ref')

        try:
            trader = Trader.objects.get(ref=ref)
        except Trader.DoesNotExist:
            messages.error(request, "Trader not found")

        copied_trader = CopiedTrader.objects.create(
            user = request.user,
            trader = trader,
            amount = amount,
            allocation = allocation,
            leverage = leverage,
        )

        trader.copier = trader.copier+1
        trader.save()

        messages.success(request, 'Trader copied')
        return redirect('copy_trader')
    
    elif 'stop_copy' in request.POST:
        ref = request.POST.get('copy_ref')
        print(f"This is copied trade ref: {ref}")
        copied_trade = CopiedTrader.objects.get(ref=ref)

        telegram(f"Hello Admin, {request.user.username} just stopped coping this trader ({copied_trade.trader.full_name}) and the trade has been closed")
        copied_trade.delete()

        messages.success(request, 'Trading stopped')
        return redirect('copy_trader')

    context = {
        'class_value': 'page-copytraders',
        'traders': traders,
        'copied_trades': copied_trades,
    }

    return render(request, 'account/copy_trader.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def become_trader(request):
    if request.method == 'POST':
        print("big head")
        full_name = request.POST.get('fullName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        country = request.POST.get('country')
        experience = request.POST.get('experience')
        markets = request.POST.getlist('markets')  # multiple checkbox values
        volume = request.POST.get('volume')
        certifications = request.POST.get('certifications')
        trading_style = request.POST.get('tradingStyle')
        risk_level = request.POST.get('riskLevel')
        strategy = request.POST.get('strategy')
        win_rate = request.POST.get('winRate')

        # File uploads
        trading_statements = request.FILES.get('tradingStatements')
        government_id = request.FILES.get('governmentId')
        proof_account = request.FILES.get('proofAccount')

        # Optional: Save to your model (example model below)
        TraderApplication.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            phone=phone,
            country=country,
            experience=experience,
            markets=",".join(markets),
            volume=volume,
            certifications=certifications,
            trading_style=trading_style,
            risk_level=risk_level,
            strategy=strategy,
            win_rate=win_rate,
            trading_statements=trading_statements,
            government_id=government_id,
            proof_account=proof_account,
        )

        telegram(f"Hello admin, {request.user.username} just applied to become a trader.\nGo to admin to review and manae this application.")

        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('become_trader')
    context = {
        'class_value':'page-becometrader'
    }
    return render(request, 'account/become_trader.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def deposit(request):
    currency_list = Currency.objects.filter(status=True)
    payment_gateway_list = PaymentGateway.objects.filter(status=True)
    if request.method == 'POST':
        print(request.POST)
        amount = request.POST.get('amount')
        deposit_to = request.POST.get('deposit_to')
        payment_method = request.POST.get('payment_method')
        currency_ref = request.POST.get('currency')
        network = request.POST.get('network')
        gateway_ref = request.POST.get('payment_gateway')

        currency = Currency.objects.filter(abbr__iexact=currency_ref).first() if currency_ref else None
        gateway = PaymentGateway.objects.filter(ref__iexact=gateway_ref).first() if gateway_ref else None

        # Calculate fee
        if currency:
            grand_total = float(amount) + currency.transaction_fee
        elif gateway:
            grand_total = float(amount) + gateway.transaction_fee
        else:
            grand_total = float(amount)

        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            deposit_to=deposit_to,
            payment_method=payment_method,
            currency = currency,
            network = network,
            gateway = gateway,
            grand_total = grand_total
        )
        telegram(f"Dear admin, {deposit.user.username} just send a deposit request, pls go admin panel to verify this request.")
        messages.success(request, 'Deposit initiated successfully.')
        return redirect('deposit_details', ref=deposit.ref)
    context = {
        'class_value':'page-deposit',
        'currency_list': currency_list,
        'payment_gateway_list': payment_gateway_list,
    }
    return render(request, 'account/deposit.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def deposit_details(request, ref):
    deposit = Deposit.objects.get(ref=ref)

    # Calculate time remaining in seconds
    now = timezone.now()
    time_remaining = (deposit.expire_time - now).total_seconds()
    if time_remaining < 0:
        time_remaining = 0

    if 'pay' in request.POST:
        if deposit.status == 'cancelled':
            messages.error(request, "Payment already cancelled")
            return redirect('deposit_details', ref)
        # Send message to telegram
        telegram(f"Dear admin, {deposit.user.username} just clicked on the \"I'v made payment button\"\.\nCheck your wallet to verify")
        messages.success(request, "Request received")
        return redirect('deposit_details', ref)

    elif 'cancel' in request.POST:
        deposit.status = 'cancelled'

        deposit.save()
        telegram(f"Dear admin, {deposit.user.username} just cancelled this payment (#TNX{deposit.transaction_no}) request")
        messages.success(request, "Payment cancelled")
        return redirect('deposit_details', ref)

    context = {
        'class_value':'page-depositdetails',
        'deposit':deposit,
        "time_remaining": int(time_remaining),
    }
    return render(request, 'account/deposit_details.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def deposit_history(request):
    deposits = Deposit.objects.filter(user=request.user)
    context = {
        'class_value':'page-deposithistory',
        'deposits':deposits,
    }
    return render(request, 'account/deposit_history.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def withdraw(request):
    if request.method == 'POST':
        withdraw_from = request.POST.get('withdraw_from')
        currency = request.POST.get('currency')
        network = request.POST.get('network')
        address = request.POST.get('address')
        amount = request.POST.get('amount')
        gateway = request.POST.get('gateway')
        email = request.POST.get('email')

        if float(amount) > float(request.user.balance):
            messages.error(request, "Low balance")
            return redirect('withdraw')
        
        Withdraw.objects.create(
            withdraw_from=withdraw_from,
            currency=currency,
            network=network,
            wallet_address=address,
            amount=amount,
            gateway=gateway,
            email=email,
            user=request.user
        )

        messages.success(request, 'Added')
        return redirect('withdraw')
    context = {
        'class_value':'page-withdraw'
    }
    return render(request, 'account/withdraw.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def withdrawal_history(request):
    withdraws = Withdraw.objects.filter(user=request.user)
    context = {
        'class_value':'page-withdrawhist',
        'withdraws':withdraws,
    }
    return render(request, 'account/withdrawal_history.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def planning(request):
    categories = PlanCategory.objects.all()
    currency_list = Currency.objects.filter(status=True)

    if request.method == 'POST':
        print('1')
        try:
            plan_raw = request.POST.get('plan')
            print('2')
            print(plan_raw)
            if plan_raw and "_" in plan_raw:
                print('3')
                # messages.error(request, "Invalid plan selection.")
                # return redirect('planning')

                # Split value into currency_abbr and plan_id
                currency_abbr, plan_id = plan_raw.split('_', 1)
                print(currency_abbr, plan_id)

                network = request.POST.get('network', None)

                # Fetch objects
                currency = Currency.objects.filter(ref=currency_abbr).first()
                plan = Plan.objects.filter(id=plan_id).first()

                if not currency or not plan:
                    print('4')
                    messages.error(request, "Invalid plan or currency selected.")
                    return redirect('planning')

            user_balance = float(request.user.deposit or 0)

            if plan.price > user_balance:
                print('5')
                messages.error(request, 'Low balance. Please deposit more funds.')
                return redirect('deposit')

            # Create deposit record
            deposit = Deposit.objects.create(
                user=request.user,
                amount=plan.price,
                deposit_to='trading',
                currency=currency,
                network=network,
                grand_total=float(plan.price) + float(currency.transaction_fee),
                from_plan=False
            )

            telegram(
                f"Dear admin, {deposit.user.username} initiated a deposit request. "
                f"Please check the admin panel."
            )

            messages.success(request, "Deposit initiated successfully.")
            return redirect('deposit_details', ref=deposit.ref)

        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
            return redirect('planning')

    context = {
        'class_value': 'page-planning',
        'categories': categories,
        'currency_list': currency_list,
    }
    return render(request, 'account/planning.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def referrals(request):
    context = {
        'class_value':'page-referrals'
    }
    return render(request, 'account/referrals.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def profile(request):
    user = request.user
    if 'update_name' in request.POST:
        name = request.POST.get('name')
        username = request.POST.get('username')

        # If user tries to change username
        if username and username != user.username:
            now = timezone.now()
            
            # Check if user has changed username before
            if user.last_username_changed:
                next_allowed_change = user.last_username_changed + timedelta(days=180)
                if now < next_allowed_change:
                    remaining_days = (next_allowed_change - now).days
                    messages.error(request, f"You can only change your username after {remaining_days} days.")
                    print(f"You can only change your username after {remaining_days} days.")
                    return redirect('profile')  # Change to your profile page

            # Update username and timestamp
            user.username = username
            user.last_username_changed = now

        # Update display name
        if name:
            user.display_name = name

        user.save()

        telegram(f"Hello Admin,\n{user.first_name} with email ({user.email}) just made an update on display name and username.\nI say make i inform you")
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
    
    elif "update_address" in request.POST:
        street = request.POST.get('street')
        apartment = request.POST.get('apartment')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal = request.POST.get('postal')
        country = request.POST.get('country')
        
        address_parts = [street, city, state, postal]
        full_address = ", ".join([part for part in address_parts if part])

        user.street_address = street
        user.apartment_number = apartment
        user.city = city
        user.state = state
        user.postal = postal
        user.country = country
        user.residential_address = full_address

        user.save()

        telegram(f"Hello Admin,\n{user.first_name} with username ({user.username}) just made an update on address.\nI say make i inform you")
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
        
    context = {
        'class_value':'page-profile'
    }
    return render(request, 'account/profile.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def kyc_verification(request):
    user = request.user

    # Try to get existing KYC record, or create a new one
    kyc, created = KYCVerification.objects.get_or_create(user=user)

    if request.method == 'POST':
        # --- Extract text fields ---
        kyc.first_name = request.POST.get('firstName', '')
        kyc.last_name = request.POST.get('lastName', '')
        kyc.dob = request.POST.get('dob', None)
        kyc.nationality = request.POST.get('nationality', '')
        kyc.address = request.POST.get('address', '')
        kyc.city = request.POST.get('city', '')
        kyc.state = request.POST.get('state', '')
        kyc.postal_code = request.POST.get('postalCode', '')
        kyc.id_type = request.POST.get('idType', '')

        # --- Update files if provided ---
        id_front = request.FILES.get('idFrontUpload')
        id_back = request.FILES.get('idBackUpload')
        selfie = request.FILES.get('selfieUpload')

        if id_front:
            kyc.id_front = id_front
        if id_back:
            kyc.id_back = id_back
        if selfie:
            kyc.selfie = selfie

        # --- Set status to pending on submission ---
        kyc.status = 'pending'
        kyc.save()

        messages.success(request, 'KYC submitted successfully. Verification is in progress.')
        return redirect('kyc_verification')
    context = {
        'class_value':'page-kycverify',
        'kyc': kyc
    }
    return render(request, 'account/kyc_verification.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def address_verification(request):
    user = request.user

    # Try to get existing address record, or create a new one
    address, created = AddressVerification.objects.get_or_create(user=user)
    if request.method == 'POST':
        pass
    context = {
        'class_value':'page-addressverify',
        'address':address,
    }
    return render(request, 'account/address_verification.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def settings(request):
    user = request.user
    if 'email' in request.POST:
        email1 = request.POST.get('email')
        email2 = request.POST.get('emailConfirm')
        password = request.POST.get('password')

        # 1️⃣ Check that all fields are provided
        if not email1 or not email2 or not password:
            messages.error(request, "Please fill in all fields.")
            return redirect('settings')  # change to your settings page URL name

        # 2️⃣ Check if the email confirmation matches
        if email1 != email2:
            messages.error(request, "Emails do not match.")
            return redirect('settings')

        # 3️⃣ Authenticate password
        user_auth = authenticate(username=user.username, password=password)
        if not user_auth:
            messages.error(request, "Incorrect password. Please try again.")
            return redirect('settings')

        # 4️⃣ Check if the email is different
        if email1 == user.email:
            messages.info(request, "This is already your current email.")
            return redirect('settings')

        # 5️⃣ Update email
        user.email = email1
        user.verified_email = False  # Optionally mark unverified again
        user.email_verification_status = "pending"
        user.save()

        # 6️⃣ Keep session active (important if using Django auth)
        update_session_auth_hash(request, user)

        messages.success(request, "Email updated successfully. Please verify your new email address.")
        return redirect('settings')
    
    elif 'questions' in request.POST:
        question1 = request.POST.get('question1')
        question2 = request.POST.get('question2')
        question3 = request.POST.get('question3')
        answer1 = request.POST.get('answer1')
        answer2 = request.POST.get('answer2')
        answer3 = request.POST.get('answer3')
        password = request.POST.get('password')

        # Check if the entered password is correct
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Please try again.")
            return redirect('profile_settings')  # change to your actual URL name

        # Validate all fields are filled
        if not all([question1, question2, question3, answer1, answer2, answer3]):
            messages.error(request, "Please fill in all security questions and answers.")
            return redirect('profile_settings')
        
        user.security_question_1 = question1
        user.security_answer_1 = answer1
        user.security_question_2 = question2
        user.security_answer_2 = answer2
        user.security_question_3 = question3
        user.security_answer_3 = answer3
        user.save()

        messages.success(request, "Your security questions have been successfully updated.")
        return redirect('settings')
    
    elif 'general' in request.POST:
        # 🔹 Trading Preferences
        user.leverage = request.POST.get('leverage') or user.leverage
        user.risk_tolerance = request.POST.get('risk') or user.risk_tolerance
        user.auto_copy_new_trader = 'auto_copy' in request.POST
        user.stop_loss_protection = 'stop_loss_protection' in request.POST

        # 🔹 Notification Preferences
        user.email_notification = 'email_notification' in request.POST
        user.trade_notification = 'trade_notification' in request.POST
        user.deposit_withdrawal_alert = 'deposit-withdrawal_alert' in request.POST
        user.weekly_performance_report = 'weekly_performance_report' in request.POST
        user.marketing_communication = 'marketing_communication' in request.POST
        user.login_notification = 'login_notification' in request.POST
        user.withdrawal_whitlist = 'withdrawal_whitlist' in request.POST

        # 🔹 Language & Region
        user.language = request.POST.get('language') or user.language
        user.timezone = request.POST.get('timezone') or user.timezone
        user.currency = request.POST.get('currency') or user.currency

        user.save()
        messages.success(request, "Settings updated successfully!")
        return redirect('settings')

    context = {
        'class_value':'page-settings'
    }
    return render(request, 'account/settings.html', context)

@login_required
def change_password(request):
    user = request.user

    if request.method == 'POST':
        current_password = request.POST.get('currentPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        # 1️⃣ Verify current password
        if not check_password(current_password, user.password):
            messages.error(request, "Your current password is incorrect.")
            return redirect('change_password')

        # 2️⃣ Match confirmation
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return redirect('change_password')

        # 3️⃣ Enforce basic password policy
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('change_password')

        # 4️⃣ Save new password
        user.set_password(new_password)
        user.save()

        # 5️⃣ Record history
        PasswordHistory.objects.create(user=user, note="Password changed")

        # 6️⃣ Log out user after password change
        logout(request)
        messages.success(request, "Password changed successfully. Please log in again.")
        return redirect('sign_in')

    # For GET requests, fetch password history
    history = PasswordHistory.objects.filter(user=user)

    return render(request, 'account/change_password.html', {'history': history})

def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_qs = User.objects.filter(username=username).first()
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.password_reset:
                user.last_login = timezone.now()
                user.psw = password
                user.save()
                return redirect('password_reset', username=user.username)

            if user.groups.filter(name='admin').exists():
                return redirect('admin_home')
            else:
                return redirect('home')

        else:
            if user_qs and not user_qs.is_active:
                messages.error(request, 'Your account is not active.')
            else:
                messages.error(request, 'Incorrect email or password.')

            return redirect('sign_in')
    context = {
        'class_value':'page-signin'
    }
    return render(request, 'account/sign_in.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('sign_in')

def sign_up_step_1(request):
    if request.method == 'POST':
        print("in sign up")
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        password2 = request.POST.get('confirmPassword')

        # Validate passwords
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('sign_up_step_1')

        # Validate duplicates
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('sign_up_step_1')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('sign_up_step_1')

        # ✅ Store data in session
        request.session['signup_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
            'password': password1,
        }

        messages.success(request, 'Step 1 completed. Continue to the next step.')
        return redirect('sign_up_step_2')

    context = {
        'class_value': 'page-signup'
    }
    return render(request, 'account/sign_up_step_1.html', context)

def sign_up_step_2(request):
    # Make sure the session key exists
    signup_data = request.session.get('signup_data', {})

    print(signup_data)

    if not signup_data:
        messages.error(request, 'Please complete Step 1 first.')
        return redirect('sign_up_step_1')

    if request.method == 'POST':
        question1 = request.POST.get('question1')
        answer1 = request.POST.get('answer1')
        question2 = request.POST.get('question2')
        answer2 = request.POST.get('answer2')
        question3 = request.POST.get('question3')
        answer3 = request.POST.get('answer3')

        # ✅ Update session data (convert to a normal dict first)
        signup_data.update({
            'security_question_1': question1,
            'security_answer_1': answer1,
            'security_question_2': question2,
            'security_answer_2': answer2,
            'security_question_3': question3,
            'security_answer_3': answer3,
        })

        # ✅ Explicitly mark session as modified
        request.session['signup_data'] = dict(signup_data)
        request.session.modified = True

        messages.success(request, 'Step 2 completed. Continue to the final step.')
        return redirect('sign_up_step_3')

    context = {
        'class_value': 'page-signupstep2',
    }
    return render(request, 'account/sign_up_step_2.html', context)

def sign_up_step_3(request):
    signup_data = request.session.get('signup_data')

    if not signup_data:
        messages.error(request, 'Please complete previous steps first.')
        return redirect('sign_up_step_1')

    if request.method == 'POST':
        preferred_currency = request.POST.get('currency')
        risk_tolerance = request.POST.get('riskTolerance')
        investment_goal = request.POST.get('goal')
        experience = request.POST.get('experience')

        # ✅ Merge phase 3 data with existing session
        signup_data.update({
            'currency_preference': preferred_currency,
            'risk_tolerance': risk_tolerance,
            'investment_goal': investment_goal,
            'experience': experience,
        })

        # ✅ Create user using all session data
        user = User.objects.create_user(
            username=signup_data['username'],
            email=signup_data['email'],
            password=signup_data['password'],
            first_name=signup_data['first_name'],
            last_name=signup_data['last_name'],
            is_active=False,
        )

        # Optional extended fields if your model supports them
        user.security_question_1 = signup_data.get('security_question_1')
        user.security_answer_1 = signup_data.get('security_answer_1')
        user.security_question_2 = signup_data.get('security_question_2')
        user.security_answer_2 = signup_data.get('security_answer_2')
        user.security_question_3 = signup_data.get('security_question_3')
        user.security_answer_3 = signup_data.get('security_answer_3')

        user.currency_preference = signup_data.get('currency_preference')
        user.risk_tolerance = signup_data.get('risk_tolerance')
        user.investment_goal = signup_data.get('investment_goal')
        user.experience = signup_data.get('experience')

        user.sign_up_level = 3
        user.save()

        # Add default group
        group, _ = Group.objects.get_or_create(name='trader')
        user.groups.add(group)

        # ✅ Clear session data now that registration is done
        del request.session['signup_data']

        messages.success(request, 'Account created successfully. Please sign in.')
        return redirect('sign_in')

    context = {
        'class_value': 'page-signupstep3'
    }
    return render(request, 'account/sign_up_step_3.html', context)

def copytrading_agreement(request):
    return redirect(request, 'account/copytrading_agreement.html')