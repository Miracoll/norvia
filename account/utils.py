import requests

from account.models import Activity

def telegram(message):
    TOKEN = "7659033307:AAHgJ-38RaKx5Xo1piwxAgjrvqBYh7qMbSY"
    chat_id = ['1322959136']

    for i in chat_id:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={i}&text={message}"
        requests.get(url)

def add_activity(user, title, description, icon, activity_type, amount, is_positive):
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