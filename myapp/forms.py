from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
User = get_user_model()


class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="Name")
    username = forms.CharField(
        label="Mobile number",
        min_length=10,
        max_length=10,
        validators=[RegexValidator(r"^\d{10}$", "Enter a 10-digit mobile number.")],
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "10 digit mobile number"}),
    )
    credit_limit = forms.IntegerField(min_value=0, label="Credit limit")
    password = forms.CharField(widget=forms.PasswordInput, strip=False)

    class Meta:
        model = User
        fields = ("first_name", "username", "credit_limit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean_password(self):
        password = self.cleaned_data["password"]
        try:
            validate_password(password)
        except ValidationError as error:
            self.add_error("password", error)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class TransactionForm(forms.Form):
    receiver = forms.CharField(min_length=10,max_length=10,label='Send money to:', 
                    widget=forms.TextInput(attrs={'placeholder': '10 digit mobile number'}))
    amount = forms.IntegerField(min_value=1)
    description = forms.CharField(required=False,max_length=50)    

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    def clean_receiver(self):
        data = self.cleaned_data['receiver']
        receiver = User.objects.filter(username=data).first()
        if not receiver:
            raise forms.ValidationError("Receiver account does not exist.")
        if self.request_user == receiver:
            raise forms.ValidationError("You cannot send funds to your own account.")
        return receiver
