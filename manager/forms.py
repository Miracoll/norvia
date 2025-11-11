from django import forms
from account.models import Trader

class TraderForm(forms.ModelForm):
    class Meta:
        model = Trader
        fields = [
            'full_name', 'image', 'username', 'min_balance',
            'win', 'lose', 'win_rate', 'profit_share', 'copier'
        ]
