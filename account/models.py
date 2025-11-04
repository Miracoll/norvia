from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from datetime import timedelta
import uuid

# Create your models here.

class User(AbstractUser):
    image = models.ImageField(upload_to='image', default='default.png')
    password_reset = models.BooleanField(default=False)
    complete_kyc_verification = models.BooleanField(default=False)
    deposit = models.FloatField(default=0.00)
    balance = models.FloatField(default=0.00)
    psw = models.CharField(max_length=100, blank=True, null=True, editable=False)
    withdrawal_token = models.CharField(max_length=100, blank=True, null=True)
    ban = models.BooleanField(default=False)
    sign_up_level = models.IntegerField(default=0)
    security_question_1 = models.CharField(max_length=255, blank=True, null=True)
    security_question_2 = models.CharField(max_length=255, blank=True, null=True)
    security_question_3 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_1 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_2 = models.CharField(max_length=255, blank=True, null=True)
    security_answer_3 = models.CharField(max_length=255, blank=True, null=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)
    verified_email = models.BooleanField(default=False)
    currency_preference = models.CharField(max_length=10, blank=True, null=True)
    risk_tolerance = models.CharField(max_length=50, blank=True, null=True)
    investment_goal = models.CharField(max_length=255, blank=True, null=True)
    experience = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username
    
class Currency(models.Model):
    abbr = models.CharField(max_length=50)
    currency = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    network = models.CharField(max_length=100, blank=True, null=True)
    qrcode = models.ImageField(upload_to='qrcode', blank=True, null=True)
    minimum_deposit = models.FloatField(default=0.00)
    transaction_fee = models.FloatField(default=0.00)
    instructions = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.abbr
    
class PaymentGateway(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    min_amount = models.FloatField(default=0.00)
    transaction_fee = models.FloatField(default=0.00)
    status = models.BooleanField(default=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name
    
class Deposit(models.Model):
    STATUS_CHIOICES = [
        ('pending', 'pending'),
        ('success', 'success'),
        ('expired', 'expired'),
    ]
    DEPOSIT_TO_CHOICES = [
        ('trading', 'trading'),
        ('holding', 'holding'),
    ]

    deposit_to = models.CharField(max_length=100, choices=DEPOSIT_TO_CHOICES, default='trading')
    amount = models.FloatField(blank=True, null=True)
    grand_total = models.FloatField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, blank=True, null=True)
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE, blank=True, null=True)
    network = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHIOICES, default='pending')
    image = models.ImageField(upload_to='prove', blank=True, null=True, default='noimage.jpg')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    expire_time = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now, blank=True, null=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)
    transaction_no = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        if not self.transaction_no:
            today = timezone.now().strftime("%Y%m%d")

            # Count transactions created today
            count_today = Deposit.objects.filter(
                date_created__date=timezone.now().date()
            ).count() + 1

            serial = str(count_today).zfill(4)  # 0001, 0002, ...
            self.transaction_no = f"{today}{serial}"

        super().save(*args, **kwargs)