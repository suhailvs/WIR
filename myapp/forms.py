from django.contrib.auth import get_user_model
from django import forms
User = get_user_model()
class TransactionForm(forms.Form):
    receiver = forms.CharField(min_length=10,max_length=10,label="Send money to:")
    amount = forms.IntegerField()
    description = forms.CharField(required=False,max_length=50)    

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned = super().clean()
        if not self.request_user.can_spend(cleaned.get('amount')):
            raise forms.ValidationError("Credit limit exceeded")
        if self.request_user.username == cleaned.get('receiver'):
            raise forms.ValidationError("You cannot send funds to your own account.")
        return cleaned
    