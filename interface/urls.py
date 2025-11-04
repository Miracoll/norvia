from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='interface_home'),
    path('about/', views.about, name='interface_about'),
    path('copy_expert_trading/', views.copy_expert_trading, name='interface_copy_expert_trading'),
    path('options_trading/', views.options_trading, name='interface_options_trading'),
    path('crypto_trading/', views.crypto_trading, name='interface_crypto_trading'),
    path('stocks_trading/', views.stocks_trading, name='interface_stocks_trading'),
    path('forex_trading/', views.forex_trading, name='interface_forex_trading'),
    path('contact/', views.contact, name='interface_contact'),
    path('privacy_policy/', views.privacy_policy, name='interface_privacy_policy'),
    path('cookie_policy/', views.cookie_policy, name='interface_cookie_policy'),
    path('terms_of_service/', views.terms_of_service, name='interface_terms_of_service'),
    path('general_risk_disclosure/', views.general_risk_disclosure, name='interface_general_risk_disclosure'),
    path('responsible_trading/', views.responsible_trading, name='interface_responsible_trading'),
    path('what_is_leverage/', views.what_is_leverage, name='interface_what_is_leverage'),
]