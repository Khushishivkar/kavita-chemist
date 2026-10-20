from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Category, ContactMessage, Product, StockTransaction

User = get_user_model()


class StyledFormMixin:
    """Gives every field the site's .form-input class."""

    def _style(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-input').strip()


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['username'].widget.attrs.update({'placeholder': 'Username', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'placeholder': 'Password'})


class RegisterForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        for name in ('username', 'password1', 'password2'):
            self.fields[name].help_text = ''
        self.fields['password2'].label = 'Confirm password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'How can we help?'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'brand', 'category', 'description', 'price', 'quantity', 'reorder_level', 'expiry_date')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['category'].empty_label = 'Select a category'


class StockForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ('kind', 'quantity', 'notes')
        widgets = {'notes': forms.TextInput(attrs={'placeholder': 'Optional note (supplier, bill no., reason...)'})}

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self._style()

    def clean(self):
        data = super().clean()
        qty, kind = data.get('quantity'), data.get('kind')
        if self.product and kind == StockTransaction.OUT and qty and qty > self.product.quantity:
            self.add_error('quantity', f'Only {self.product.quantity} in stock.')
        return data
