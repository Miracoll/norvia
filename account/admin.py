from django.contrib import admin
from account.models import Currency, PaymentGateway, User

# Register your models here.

admin.site.register(User)
admin.site.register(Currency)
admin.site.register(PaymentGateway)