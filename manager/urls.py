from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_home'),
    path('user/list/', views.user_list, name='admin_user_list'),
    path('user/detail/', views.user_detail, name='admin_user_detail'),
    path('kyc/approvals/', views.kyc, name='admin_kyc_approvals'),
    path('user/activity/', views.activity_log, name='admin_user_activity'),
    path('deposits/list/', views.deposit_list, name='admin_deposit_list'),
    path('withdrawals/list/', views.withdrawal_list, name='admin_withdrawal_list'),
    path('payment/methods/', views.payment_method, name='admin_payment_methods'),
    path('plans/manage/', views.plan_management, name='admin_plan_management'),
    path('traders/list/', views.trader_list, name='admin_trader_list'),
    path('traders/add/', views.trader_add, name='admin_trader_add'),
    path('trader/applications/', views.trader_applications, name='admin_trader_applications'),
    path('copy/requests/', views.copy_requests, name='admin_copy_requests'),
    path('take/trade/', views.take_trade, name='admin_take_trade'),
    path('become/trader/', views.become_trader, name='admin_become_trader'),
    path('notifications/', views.send_notification, name='admin_notifications'),
    path('email/templates/', views.email_template, name='admin_email_templates'),
    path('frontpage/manager/', views.frontpage_manager, name='admin_frontpage_manager'),
    path('platform/settings/', views.platform_setting, name='admin_platform_settings'),
    path('verification/settings/', views.verification_setting, name='admin_verification_settings'),
    path('page/content/', views.page_content, name='admin_page_content'),
    path('admin/profile/', views.admin_profile, name='admin_profile'),
    path('reports/analytics/', views.reports, name='admin_reports'),
    path('add/payment/method/', views.admin_payment_methods, name='admin_add_payment_method'),
]