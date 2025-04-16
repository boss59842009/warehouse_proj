from django import forms
from django.forms import inlineformset_factory
from .models import (
    Product, Category, PackageType, MeasurementUnit, Culture,
    Order, OrderItem, Inventory, ProductMovement, ProductImage,
    BackupSettings, SystemParameter
)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'real_name', 'culture', 'category', 'package_type', 
            'measurement_unit', 'lot_number', 'import_name', 'quantity',
            'packages_count', 'image', 'description', 'is_available', 'price'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'real_name': forms.TextInput(attrs={'class': 'form-control'}),
            'culture': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'package_type': forms.Select(attrs={'class': 'form-select'}),
            'measurement_unit': forms.Select(attrs={'class': 'form-select'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'import_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'packages_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']

ProductImageFormSet = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, 
    extra=1, can_delete=True
)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class PackageTypeForm(forms.ModelForm):
    class Meta:
        model = PackageType
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class MeasurementUnitForm(forms.ModelForm):
    class Meta:
        model = MeasurementUnit
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'comment']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm, 
    extra=1, can_delete=True
)

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['product', 'quantity_expected', 'quantity_actual', 'comment']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity_expected': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'quantity_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ProductMovementForm(forms.ModelForm):
    class Meta:
        model = ProductMovement
        fields = ['product', 'movement_type', 'quantity', 'date', 'document_number', 'comment', 'order']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
        }

class BackupSettingsForm(forms.ModelForm):
    class Meta:
        model = BackupSettings
        fields = ['auto_backup', 'backup_frequency', 'backup_location']
        widgets = {
            'auto_backup': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'backup_frequency': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'backup_location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SystemParameterForm(forms.ModelForm):
    class Meta:
        model = SystemParameter
        fields = ['key', 'value', 'description']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'min': 1}))
    product_id = forms.IntegerField(widget=forms.HiddenInput())

class CartForm(forms.Form):
    CHOICES = [('update', 'Оновити'), ('checkout', 'Оформити замовлення')]
    action = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

class CartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, widget=forms.NumberInput(
        attrs={'class': 'form-control', 'min': 0}))
    product_id = forms.IntegerField(widget=forms.HiddenInput())

class CheckoutForm(forms.Form):
    comment = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Коментар до замовлення'}))

class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), 
        required=False,
        empty_label="Всі категорії",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(), 
        required=False,
        empty_label="Всі культури",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    available_only = forms.BooleanField(
        required=False, 
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    search = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Пошук за назвою'
        })
    )

class ReportForm(forms.Form):
    REPORT_FORMATS = [
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    ]
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), 
        required=False,
        empty_label="Всі категорії",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    format = forms.ChoiceField(
        choices=REPORT_FORMATS, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='csv'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    ) 