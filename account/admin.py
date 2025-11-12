from django.contrib import admin
from account.models import CopiedTrader, CopyRequest, Currency, PaymentGateway, Plan, PlanCategory, Trader, TraderApplication, User, Withdraw, PasswordHistory, Activity, Deposit, KYCVerification, Notification

# Register your models here.

admin.site.register(User)
admin.site.register(Currency)
admin.site.register(PaymentGateway)
admin.site.register(Plan)
admin.site.register(Withdraw)
admin.site.register(PlanCategory)
admin.site.register(PasswordHistory)
admin.site.register(Activity)
admin.site.register(Deposit)
admin.site.register(KYCVerification)
admin.site.register(Trader)
admin.site.register(CopiedTrader)
admin.site.register(Notification)
admin.site.register(TraderApplication)
admin.site.register(CopyRequest)