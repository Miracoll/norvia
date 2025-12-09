import requests
from account.models import Activity, AdminNotification, Notification, Trade, User
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def telegram(message):
    TOKEN = "7659033307:AAHgJ-38RaKx5Xo1piwxAgjrvqBYh7qMbSY"
    chat_id = ['1322959136']

    for i in chat_id:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={i}&text={message}"
        requests.get(url)

def add_activity(user, title, description, icon, activity_type, amount, is_positive):
    """
    Icon: arrow_downward, arrow_upward, trending_up, content_copy, settings, default
    """
    activity = Activity.objects.create(
        user=user,
        title=title,
        description=description,
        icon=icon,
        activity_type=activity_type,
        amount=amount,
        is_positive=is_positive,
    )
    return activity

def add_notification(user,title,text,color):

    """
    Color: info, success, danger, primary, warning
    """
    notification = Notification.objects.create(
        user=user,title=title,media_type='text',text=text,color=color
    )

    return notification

def add_addmin_notification(user,title,message):
    
    notification = AdminNotification.objects.create(
        user=user,title=title,message=message,
    )

    return notification

# def usd_to_btc(amount_usd):
#     url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"

#     response = requests.get(url)
#     response.raise_for_status()

#     data = response.json()
#     btc_price = float(data["result"]["XXBTZUSD"]["c"][0])  # last trade price

#     return amount_usd / btc_price

def usd_to_btc(amount_usd):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    btc_price = float(data["bitcoin"]["usd"])  # BTC price in USD

    return amount_usd / btc_price

def check_expired_trades(user:User):
    trades = Trade.objects.filter(user=user, status='open')

    for trade in trades:
        if trade.is_expired():
            trade.close_trade()

def get_24hr_pnl_and_percentage(user):
    now = timezone.now()
    last_24hrs = now - timedelta(hours=24)
    previous_24hrs = last_24hrs - timedelta(hours=24)

    # Current 24 hrs trades
    trades_today = Trade.objects.filter(
        user=user,
        closed_at__gte=last_24hrs,
        closed_at__lte=now,
        status='closed'
    )

    # Previous 24 hrs trades
    trades_yesterday = Trade.objects.filter(
        user=user,
        closed_at__gte=previous_24hrs,
        closed_at__lt=last_24hrs,
        status='closed'
    )

    today_pnl = sum(t.pnl for t in trades_today)
    yesterday_pnl = sum(t.pnl for t in trades_yesterday)

    # Percentage change calculation
    if yesterday_pnl == 0:
        percentage_change = 100 if today_pnl > 0 else -100 if today_pnl < 0 else 0
    else:
        percentage_change = ((today_pnl - yesterday_pnl) / abs(yesterday_pnl)) * 100

    return today_pnl, percentage_change

def send_verification_email(user, verification_url):
    subject = "Verify Your Email Address"

    html_content = render_to_string("email-templates/verify_email.html", {
        "first_name": user.first_name,
        "verification_url": verification_url,
    })

    email = EmailMultiAlternatives(
        subject=subject,
        body="Please verify your email.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
