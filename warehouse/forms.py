from django import forms
from django.forms import inlineformset_factory
from .models import (
    Product, ProductImage, PackageType, MeasurementUnit, Culture,
    Order, OrderItem, Inventory,
    BackupSettings, SystemParameter, ProductVariation, ProductVariationImage, ProductIncome, ProductIncomeItem
)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'real_name', 'culture', 'description', 'code'
        ]
        widgets = {
            'real_name': forms.TextInput(attrs={'class': 'form-control'}),
            'culture': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    fields=['image'],
    extra=0,  # Не створювати додаткові порожні форми
    can_delete=True,
    max_num=5
)

class ProductVariationForm(forms.ModelForm):
    class Meta:
        model = ProductVariation
        fields = [
            'real_name', "import_name", "lot_number", "package_type", "measurement_unit"
        ]
        widgets = {
            'real_name': forms.TextInput(attrs={'class': 'form-control'}),
            'import_name': forms.TextInput(attrs={'class': 'form-control'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'package_type': forms.Select(attrs={'class': 'form-select'}),
            'measurement_unit': forms.Select(attrs={'class': 'form-select'}),
        }

class ProductVariationImageForm(forms.ModelForm):
    class Meta:
        model = ProductVariationImage
        fields = ['image']

ProductVariationImageFormSet = inlineformset_factory(
    ProductVariation,
    ProductVariationImage,
    fields=['image'],
    extra=0,  # Не створювати додаткові порожні форми
    can_delete=True,
    max_num=5
)
# Формсет для варіацій товару
ProductVariationFormSet = inlineformset_factory(
    Product, 
    ProductVariation,
    form=ProductVariationForm,
    fields=('real_name', 'import_name', 'lot_number', 'package_type', 'measurement_unit'),
    extra=0,
    can_delete=True
)

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

class ProductIncomeForm(forms.ModelForm):
    class Meta:
        model = ProductIncome
        fields = ['movement_type']

class ProductIncomeItemForm(forms.ModelForm):
    class Meta:
        model = ProductIncomeItem
        fields = ['quantity', 'packages_count', 'lot_number', 'package_type', 'measurement_unit']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'packages_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control'}),
            'package_type': forms.Select(attrs={'class': 'form-select'}),
            'measurement_unit': forms.Select(attrs={'class': 'form-select'}),
        }

ProductIncomeItemFormSet = inlineformset_factory(
    ProductIncome,
    ProductIncomeItem,
    form=ProductIncomeItemForm,
    fields=['quantity', 'packages_count', 'lot_number', 'package_type', 'measurement_unit'],
    extra=0,
    can_delete=True
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
    real_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Пошук за справжньою назвою'
        })
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