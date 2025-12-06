import requests
import yfinance as yf
from account.models import Activity, Notification, Trade, User

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

# def usd_to_btc(amount_usd):
#     url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"

#     response = requests.get(url)
#     response.raise_for_status()

#     data = response.json()
#     btc_price = float(data["result"]["XXBTZUSD"]["c"][0])  # last trade price

#     return amount_usd / btc_price

def usd_to_btc(amount_usd):
    btc = yf.Ticker("BTC-USD")
    data = btc.history(period="1d")   # ALWAYS works

    if data.empty:
        raise Exception("Failed to fetch BTC price")

    btc_price = data["Close"].iloc[-1]   # last available price
    return amount_usd / btc_price

def check_expired_trades(user:User):
    trades = Trade.objects.filter(user=user, status='open')

    for trade in trades:
        if trade.is_expired():
            trade.close_trade()
