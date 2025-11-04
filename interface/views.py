from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'interface/index.html')

def about(request):
    return render(request, 'interface/about.html')

def copy_expert_trading(request):
    return render(request, 'interface/copy_expert_trading.html')

def options_trading(request):
    return render(request, 'interface/options_trading.html')

def crypto_trading(request):
    return render(request, 'interface/crypto_trading.html')

def stocks_trading(request):
    return render(request, 'interface/stocks_trading.html')

def forex_trading(request):
    return render(request, 'interface/forex_trading.html')

def contact(request):
    return render(request, 'interface/contact.html')

def privacy_policy(request):
    return render(request, 'interface/privacy_policy.html')

def cookie_policy(request):
    return render(request, 'interface/cookie_policy.html')

def terms_of_service(request):
    return render(request, 'interface/terms_of_service.html')

def general_risk_disclosure(request):
    return render(request, 'interface/general_risk_disclosure.html')

def responsible_trading(request):
    return render(request, 'interface/responsible_trading.html')

def what_is_leverage(request):
    return render(request, 'interface/what_is_leverage.html')