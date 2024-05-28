# captions/forms.py
from django import forms

class ImageUploadForm(forms.Form):
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'id': 'file', 'class': 'inputfile'})
    )

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    