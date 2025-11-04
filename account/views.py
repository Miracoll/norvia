from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import Group

from account.models import Currency, Deposit, PaymentGateway, User
from utils.decorators import allowed_users

# Create your views here.

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def home(request):
    context = {
        'class_value': 'page-dashboard'
    }
    return render(request, 'account/dashboard.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def crypto_market(request):
    context = {
        'class_value': 'page-cryptomarket'
    }
    return render(request, 'account/crypto_market.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def stock_market(request):
    context = {
        'class_value': 'page-stockmarket'
    }
    return render(request, 'account/stock_market.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def copy_trader(request):
    context = {
        'class_value':'page-copytraders'
    }
    return render(request, 'account/copy_trader.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def become_trader(request):
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

        if currency_ref:
            currency = Currency.objects.get(ref=currency_ref)
        else:
            currency = None

        if gateway_ref:
            gateway = PaymentGateway.objects.get(ref=gateway_ref)
        else:
            gateway = None

        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            deposit_to=deposit_to,
            payment_method=payment_method,
            currency = currency,
            network = network,
            gateway = gateway,
            grand_total = (float(amount)+currency.transaction_fee) or (float(amount)+gateway.transaction_fee)
        )
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
    context = {
        'class_value':'page-depositdetails'
    }
    return render(request, 'account/deposit_details.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def deposit_history(request):
    context = {
        'class_value':'page-deposithistory'
    }
    return render(request, 'account/deposit_history.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def withdraw(request):
    context = {
        'class_value':'page-withdraw'
    }
    return render(request, 'account/withdraw.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def withdrawal_history(request):
    context = {
        'class_value':'page-withdrawhist'
    }
    return render(request, 'account/withdrawal_history.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def planning(request):
    context = {
        'class_value':'page-planning'
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
    context = {
        'class_value':'page-profile'
    }
    return render(request, 'account/profile.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def kyc_verification(request):
    context = {
        'class_value':'page-kycverify'
    }
    return render(request, 'account/kyc_verification.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def address_verification(request):
    context = {
        'class_value':'page-addressverify'
    }
    return render(request, 'account/address_verification.html', context)

@login_required(login_url='sign_in')
@allowed_users(allowed_roles=['admin','trader'])
def settings(request):
    context = {
        'class_value':'page-settings'
    }
    return render(request, 'account/settings.html', context)

def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_qs = User.objects.filter(username=username).first()
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.password_reset:
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

def forget_password(request):
    context = {
        'class_value':'page-forgotpwd'
    }
    return render(request, 'account/forget_password.html', context)

def sign_up_step_1(request):
    if request.method == 'POST':
        print("in sign up")
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('sign_up_step_1')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('sign_up_step_1')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('sign_up_step_1')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
            sign_up_level=1,
        )
        user.save()

        group, _ = Group.objects.get_or_create('trader')
        user.groups.add(group)

        messages.success(request, 'Record saved successfully.')
        return redirect('sign_up_step_2', user.ref)
    context = {
        'class_value':'page-signup'
    }
    return render(request, 'account/sign_up_step_1.html', context)

def sign_up_step_2(request, ref):
    if request.method == 'POST':
        user = User.objects.get(ref=ref)

        question1 = request.POST.get('question1')
        answer1 = request.POST.get('answer1')
        question2 = request.POST.get('question2')
        answer2 = request.POST.get('answer2')
        question3 = request.POST.get('question3')
        answer3 = request.POST.get('answer3')

        # Here you would typically save these security questions and answers
        # to the user's profile in the database.

        user.sign_up_level = 2
        user.security_question_1 = question1
        user.security_answer_1 = answer1
        user.security_question_2 = question2
        user.security_answer_2 = answer2
        user.security_question_3 = question3
        user.security_answer_3 = answer3
        user.save()

        messages.success(request, 'Record saved successfully.')
        return redirect('sign_up_step_3', user.ref)
    context = {
        'class_value':'page-signupstep2'
    }
    return render(request, 'account/sign_up_step_2.html', context)

def sign_up_step_3(request, ref):
    if request.method == 'POST':
        preferred_currency = request.POST.get('currency')
        risk_tolerance = request.POST.get('riskTolerance')
        investment_goal = request.POST.get('goal')
        experience = request.POST.get('experience')
        user = User.objects.get(ref=ref)

        user.sign_up_level = 3
        user.currency_preference = preferred_currency
        user.risk_tolerance = risk_tolerance
        user.investment_goal = investment_goal
        user.experience = experience
        user.save()


        # Here you would typically save these preferences
        # to the user's profile in the database.

        messages.success(request, 'Account created successfully. Please sign in.')
        return redirect('sign_in')
    context = {
        'class_value':'page-signupstep3'
    }
    return render(request, 'account/sign_up_step_3.html', context)