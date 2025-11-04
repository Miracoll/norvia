import io
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.contrib import messages
import qrcode

from account.models import Currency, PaymentGateway

# Create your views here.

def dashboard(request):
    context = {
        'header_title': 'Admin Dashboard',
        'body_class': 'page-admin-dashboard'
    }
    return render(request, 'manager/dashboard.html', context)

def user_list(request):
    context = {
        'header_title': 'Users Management',
        'body_class': 'page-admin-users'
    }
    return render(request, 'manager/user_list.html', context)

def user_detail(request):
    context = {
        'header_title': 'User Details',
        'body_class': 'page-admin-userdetails'
    }
    return render(request, 'manager/user_detail.html', context)

def kyc(request):
    context = {
        'header_title': 'KYC Approvals',
        'body_class': 'page-admin-kyc'
    }
    return render(request, 'manager/kyc_approval.html', context)

def activity_log(request):
    context = {
        'header_title': 'User Activity Logs',
        'body_class': 'page-user-activity'
    }
    return render(request, 'manager/activity_log.html', context)

def deposit_list(request):
    context = {
        'header_title': 'Deposits Management',
        'body_class': 'page-admin-deposits'
    }
    return render(request, 'manager/deposit_list.html', context)

def withdrawal_list(request):
    context = {
        'header_title': 'Withdrawals Management',
        'body_class': 'page-admin-withdrawals'
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
        pass

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

        print('Deleted')

        messages.success(request, 'Successful.')
        return redirect('admin_payment_methods')
    context = {
        'header_title': 'Payment Methods Management',
        'body_class': 'page-admin-payments',
        'currencies': currencies,
        'gateways': gateways,
    }
    return render(request, 'manager/payment_method.html', context)

def admin_payment_methods(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        crypto_id = data.get("id")  # ✅ detect edit
        name = data.get("name")
        symbol = data.get("symbol")
        network = data.get("network")
        fee = data.get("fee")
        min_deposit = data.get("min_deposit")
        address = data.get("address")

        if not all([name, symbol, network, fee, min_deposit, address]):
            return JsonResponse({"status": "error", "message": "All fields are required"})

        # ✅ UPDATE existing currency
        if crypto_id:
            try:
                crypto = Currency.objects.get(id=crypto_id)
            except Currency.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Crypto not found"}, status=404)

            qr_changed = (crypto.address != address)

            crypto.currency = name
            crypto.abbr = symbol
            crypto.network = network
            crypto.transaction_fee = fee
            crypto.minimum_deposit = min_deposit
            crypto.address = address
            crypto.save()

            # ✅ regenerate QR only if address changed
            if qr_changed:
                qr = qrcode.make(address)
                buffer = io.BytesIO()
                qr.save(buffer, format="PNG")
                buffer.seek(0)
                filename = f"{symbol.lower()}_{network.lower()}_qr.png"
                crypto.qrcode.save(filename, ContentFile(buffer.getvalue()), save=True)

            return JsonResponse({"status": "success", "message": "Updated successfully!"})
        
        # ✅ If no ID — CREATE NEW entry
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
        )
        crypto.qrcode.save(filename, ContentFile(buffer.getvalue()), save=True)

        return JsonResponse({"status": "success", "message": "Created successfully!"})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


def plan_management(request):
    context = {
        'header_title': 'Plans Management',
        'body_class': 'page-admin-plans'
    }
    return render(request, 'manager/plan_management.html', context)

def trader_list(request):
    context = {
        'header_title': 'Traders Management',
        'body_class': 'page-admin-traders'
    }
    return render(request, 'manager/trader_list.html', context)

def trader_add(request):
    context = {
        'header_title': 'Add New Trader',
        'body_class': 'page-admin-traderadd'
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
