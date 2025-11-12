from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.timezone import now

from datetime import timedelta
import uuid

# Create your models here.

class User(AbstractUser):
    image = models.ImageField(upload_to='image', default='default.png')
    password_reset = models.BooleanField(default=False)
    complete_kyc_verification = models.BooleanField(default=False)
    deposit = models.FloatField(default=0.00)
    profit = models.FloatField(default=0.00)
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
    email_verification_status = models.CharField(max_length=20, default='pending')
    verified_phone = models.BooleanField(default=False)
    mobile_verification_status = models.CharField(max_length=20, default='pending')
    verified_kyc = models.BooleanField(default=False)
    kyc_verification_status = models.CharField(max_length=20, default='pending')
    verified_address = models.BooleanField(default=False)
    address_verification_status = models.CharField(max_length=20, default='pending')
    currency_preference = models.CharField(max_length=10, blank=True, null=True)
    risk_tolerance = models.CharField(max_length=50, blank=True, null=True)
    investment_goal = models.CharField(max_length=255, blank=True, null=True)
    experience = models.CharField(max_length=255, blank=True, null=True)
    traders_copied = models.PositiveIntegerField(default=0)
    total_trades = models.PositiveIntegerField(default=0)
    success_rate = models.PositiveIntegerField(default=0)
    trading_experience = models.PositiveIntegerField(default=0, help_text='value in month, e.g 4, 6')
    is_premium_account = models.BooleanField(default=False)
    use_badge = models.BooleanField(default=False)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    residential_address = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    last_username_changed = models.DateTimeField(blank=True,null=True)
    display_name = models.CharField(max_length=50, blank=True, null=True)
    street_address = models.CharField(max_length=50,blank=True,null=True)
    apartment_number = models.CharField(max_length=50,blank=True,null=True)
    city = models.CharField(max_length=50,blank=True,null=True)
    state = models.CharField(max_length=50,blank=True,null=True)
    postal = models.CharField(max_length=10,blank=True,null=True)
    leverage = models.PositiveIntegerField(default=1)
    auto_copy_new_trader = models.BooleanField(default=False)
    stop_loss_protection = models.BooleanField(default=False)
    email_notification = models.BooleanField(default=False)
    trade_notification = models.BooleanField(default=False)
    deposit_withdrawal_alert = models.BooleanField(default=False)
    weekly_performance_report = models.BooleanField(default=False)
    marketing_communication = models.BooleanField(default=False)
    language = models.CharField(max_length=2, blank=True, null=True)
    timezone = models.CharField(max_length=3, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    login_notification = models.BooleanField(default=False)
    withdrawal_whitlist = models.BooleanField(default=False)
    kyc_status = models.CharField(default='unverified', max_length=15)
    holding_deposit = models.FloatField(default=0.0)
    holding_profit = models.FloatField(default=0.0)

    def __str__(self):
        return self.username
    
    @property
    def time_label(self):
        """Generates a human-friendly time label like 'Today at 10:30 AM'."""
        delta = now() - self.date_joined
        if delta.days == 0:
            return self.date_joined.strftime("Today at %I:%M %p")
        elif delta.days == 1:
            return self.date_joined.strftime("Yesterday at %I:%M %p")
        else:
            return timesince(self.date_joined).split(",")[0] + " ago"
        
    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.first_name + " " + self.last_name

        if not self.last_username_changed:
            self.last_username_changed = self.date_joined

        super().save(*args, **kwargs)

class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_histories')
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, null=True)  # e.g., "Password reset" or "Manual change"

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.user.username} - changed on {self.changed_at.strftime('%Y-%m-%d %H:%M:%S')}"

class Activity(models.Model):
    ICON_CHOICES = [
        ('arrow_downward', 'Deposit'),
        ('arrow_upward', 'Withdrawal'),
        ('trending_up', 'Trade Closed'),
        ('content_copy', 'Copy Trade'),
        ('settings', 'Security Setting'),
        ('default', 'Other'),
    ]

    TYPE_CHOICES = [
        ('success', 'Success'),
        ('info', 'Info'),
        ('danger', 'Danger'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='default')
    activity_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='info')
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    is_positive = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    @property
    def formatted_amount(self):
        if self.amount is None:
            return ""
        sign = "+" if self.is_positive else "-"
        return f"{sign}${abs(self.amount):,.2f}"

    @property
    def time_label(self):
        """Generates a human-friendly time label like 'Today at 10:30 AM'."""
        delta = now() - self.timestamp
        if delta.days == 0:
            return self.timestamp.strftime("Today at %I:%M %p")
        elif delta.days == 1:
            return self.timestamp.strftime("Yesterday at %I:%M %p")
        else:
            return timesince(self.timestamp).split(",")[0] + " ago"
    
class Currency(models.Model):
    abbr = models.CharField(max_length=50)
    currency = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    network = models.CharField(max_length=100, blank=True, null=True)
    qrcode = models.ImageField(upload_to='qrcode', blank=True, null=True)
    minimum_deposit = models.FloatField(default=0.00)
    transaction_fee = models.FloatField(default=0.00)
    instructions = models.TextField(blank=True, null=True, max_length=2000)
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
    instructions = models.TextField(blank=True, null=True, max_length=2000)
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
    equivalent = models.FloatField(default=0.0)

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

        if not self.expire_time:
            self.expire_time = timezone.now() + timedelta(minutes=30)

        super().save(*args, **kwargs)

class Withdraw(models.Model):
    STATUS_CHIOICES = [
        ('pending', 'pending'),
        ('success', 'success'),
        ('expired', 'expired'),
    ]
    withdraw_from = models.CharField(max_length=20)
    currency = models.CharField(max_length=50, blank=True, null=True)
    network = models.CharField(max_length=30, blank=True, null=True)
    wallet_address = models.CharField(max_length=100)
    amount = models.FloatField(default=0.00)
    gateway = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(30)
    transaction_no = models.CharField(max_length=20, blank=True, null=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    equivalent = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, choices=STATUS_CHIOICES, default='pending')

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        if not self.transaction_no:
            today = timezone.now().strftime("%Y%m%d")

            # Count transactions created today
            count_today = Withdraw.objects.filter(
                date__date=timezone.now().date()
            ).count() + 1

            serial = str(count_today).zfill(4)  # 0001, 0002, ...
            self.transaction_no = f"{today}{serial}"

        super().save(*args, **kwargs)

class PlanCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g. Trading, Signals, Mining, Staking

    def __str__(self):
        return self.name

class Plan(models.Model):
    category = models.ForeignKey(PlanCategory, on_delete=models.CASCADE, related_name='plans')
    tier = models.CharField(max_length=100)  # e.g. Gold, Silver, Bronze
    price = models.DecimalField(max_digits=12, decimal_places=2)
    features = models.TextField(help_text="Enter one feature per line.")
    button_text = models.CharField(max_length=100, default="PURCHASE PLAN")

    # Only used for Mining (optional)
    has_currency_select = models.BooleanField(default=False)

    def get_features(self):
        """Return features as a list."""
        return [f.strip() for f in self.features.split('\n') if f.strip()]

    def __str__(self):
        return f"{self.category.name} - {self.tier}"
    
class KYCVerification(models.Model):
    STATUS_CHOICES = [
        ('not_submitted', 'Not Submitted'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    id_type = models.CharField(max_length=50)

    # Files will be stored in "media/kyc/"
    id_front = models.FileField(upload_to='kyc/')
    id_back = models.FileField(upload_to='kyc/')
    selfie = models.FileField(upload_to='kyc/')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(auto_now=True, blank=True, null=True)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.user.username} - {self.status}"

class Trader(models.Model):
    COPY_MODE_CHOICES = [
        ('flexible', 'Flexible'),
        ('full', 'Full Balance'),
    ]

    BADGE_CHOICES = [
        ('none', 'No Badge'),
        ('blue', 'Blue Badge'),
        ('gold', 'Gold Badge'),
    ]

    full_name = models.CharField(max_length=50)
    image = models.ImageField(upload_to="trader", default='default.png')
    username = models.CharField(max_length=50, unique=True)
    min_balance = models.FloatField(default=0)
    profit_share = models.FloatField(default=0)

    # Extra fields from form
    bio = models.TextField(blank=True, null=True)
    copy_mode = models.CharField(max_length=20, choices=COPY_MODE_CHOICES, default='flexible')
    require_approval = models.BooleanField(default=False)
    badge = models.CharField(max_length=10, choices=BADGE_CHOICES, default='none')

    # Stats
    win = models.PositiveIntegerField(default=0)
    lose = models.PositiveIntegerField(default=0)
    win_rate = models.FloatField(default=0)
    copier = models.PositiveIntegerField(default=0)

    ref = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name

class CopiedTrader(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='copied_trades'
    )
    trader = models.ForeignKey(
        'Trader',
        on_delete=models.CASCADE,
        related_name='copied_by_users'
    )
    total_profit = models.FloatField(default=0.0)
    last_24h_profit_loss = models.FloatField(default=0.0)
    ref = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} copied {self.trader.name if hasattr(self.trader, 'name') else 'a trader'}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Copied Trader'
        verbose_name_plural = 'Copied Traders'

class Notification(models.Model):
    title = models.CharField(max_length=100)
    message = models.CharField(max_length=100)
    created_on = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ref = models.UUIDField(default=uuid.uuid4, editable=False)
    read = models.BooleanField(default=False)
    read_on = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title
    
class TraderApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    country = models.CharField(max_length=100)
    experience = models.CharField(max_length=50)
    markets = models.TextField()
    volume = models.CharField(max_length=50)
    certifications = models.TextField(blank=True, null=True)
    trading_style = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=100)
    strategy = models.TextField()
    win_rate = models.FloatField()
    trading_statements = models.FileField(upload_to='traders/statements/')
    government_id = models.FileField(upload_to='traders/id/')
    proof_account = models.FileField(upload_to='traders/proof/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
class CopyRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='copy_requests')
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='requests')
    allocation = models.FloatField(default=0.0)
    percentage = models.PositiveIntegerField(default=0)
    user_balance = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} → {self.trader.full_name} ({self.status})"
    
class ManualTrade(models.Model):
    MARKET_CHOICES = [
        ('crypto', 'Crypto'),
        ('stocks', 'Stocks'),
    ]
    DIRECTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    OUTCOME_CHOICES = [
        ('profit', 'Profit'),
        ('loss', 'Loss'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_trades')
    trader = models.ForeignKey(Trader, on_delete=models.SET_NULL, null=True, blank=True, related_name='copied_trades')

    market_type = models.CharField(max_length=20, choices=MARKET_CHOICES)
    asset = models.CharField(max_length=50)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    outcome = models.CharField(max_length=10, choices=OUTCOME_CHOICES)
    outcome_amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.asset} ({self.direction.upper()})"

    @property
    def result_summary(self):
        return f"{self.outcome.capitalize()} of ${self.outcome_amount}"