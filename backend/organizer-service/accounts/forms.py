from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"placeholder": "you@organization.dz",
                                                                          "autofocus": True}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}))
