from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os
from django.core.exceptions import ValidationError
    

class PackageType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Тип упаковки")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Тип упаковки"
        verbose_name_plural = "Типи упаковки"

class MeasurementUnit(models.Model):
    name = models.CharField(max_length=50, verbose_name="Одиниця виміру")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Одиниця виміру"
        verbose_name_plural = "Одиниці виміру"

class Culture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва культури")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Культура"
        verbose_name_plural = "Культури"

class BaseProduct(models.Model):
    name = models.CharField(max_length=200, verbose_name="Назва продукту", unique=True, null=True, blank=True)
    real_name = models.CharField(max_length=200, verbose_name="Назва справжня", blank=True, null=True)
    package_type = models.ForeignKey(PackageType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тип упаковки")
    measurement_unit = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Одиниця виміру")
    lot_number = models.CharField(max_length=100, verbose_name="Номер лоту", blank=True, null=True)
    import_name = models.CharField(max_length=200, verbose_name="Імпорт назва", blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name="Опис товару")
    is_available = models.BooleanField(default=True, verbose_name="В наявності")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Кількість")
    packages_count = models.PositiveIntegerField(default=0, verbose_name="Кількість упаковок")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ціна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    
    class Meta:
        abstract = True
        unique_together = ('name', 'lot_number')

class Product(BaseProduct):
    culture = models.ForeignKey(Culture, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Культура")
    code = models.CharField(max_length=50, verbose_name="Код товару", unique=True)
    has_variations = models.BooleanField(default=False, verbose_name="Має варіації")
    
    def __str__(self):
        return f"{self.real_name}"
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Фото товару")

    def __str__(self):
        return f"Фото для {self.product.real_name}"
    
    class Meta:
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товарів"


class ProductVariation(BaseProduct):
    parent_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations', verbose_name="Основний товар")
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Артикул")
    
    def __str__(self):
        return f"{self.parent_product.name} - {self.name}"
    
    class Meta:
        verbose_name = "Варіація товару"
        verbose_name_plural = "Варіації товарів"

class ProductVariationImage(models.Model):
    product = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, verbose_name="Варіація товару")
    image = models.ImageField(upload_to='product_variations/', blank=True, null=True, verbose_name="Фото товару")

    def __str__(self):
        return f"Фото для {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('successful', 'Успішно'),
        ('canceled', 'Скасовано'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Користувач")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='successful', verbose_name="Статус")
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Загальна сума")
    
    def update_total_price(self):
        self.total_price = sum(item.total_price for item in self.items.all())
        self.save(update_fields=['total_price'])
    
    def __str__(self):
        return f"Замовлення №{self.id} від {self.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Замовлення")
    product = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за одиницю")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Загальна ціна")
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Якщо ціна не встановлена, беремо з товару
        if not self.price:
            self.price = self.product.price
        if not self.quantity:
            self.quantity = self.product.quantity
        # Розрахунок загальної ціни
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)
        self.order.update_total_price()
    
    class Meta:
        verbose_name = "Товар у замовленні"
        verbose_name_plural = "Товари у замовленні"

class Inventory(models.Model):
    movement_type = models.CharField(max_length=100, default='inventory', verbose_name="Тип накладної", null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Виконав")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    
    def __str__(self):
        return f"Інвентаризація від {self.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Інвентаризація"
        verbose_name_plural = "Інвентаризації"

class InventoryItem(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, verbose_name="Інвентаризація")
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, verbose_name="Варіація товару")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Кількість") 
    fact_quantity = models.PositiveIntegerField(default=0, verbose_name="Фактична кількість")
    difference = models.IntegerField(default=0, verbose_name="Відхилення")

    def __str__(self):
        return f"Інвентаризація від {self.inventory.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Варіація в інвентаризації"
        verbose_name_plural = "Варіації в інвентаризації"
    
class ProductIncome(models.Model):
    movement_type = models.CharField(max_length=100, default='incoming', verbose_name="Тип накладної")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Виконав")
    total_quantity = models.PositiveIntegerField(default=0, verbose_name="Загальна кількість")
    total_packages_count = models.PositiveIntegerField(default=0, verbose_name="Загальна кількість упаковок")

    def update_total_quantity(self):
        self.total_quantity = sum(item.quantity for item in self.items.all())
        self.save(update_fields=['total_quantity'])
    
    def update_total_packages_count(self):
        self.total_packages_count = sum(item.packages_count for item in self.items.all())
        self.save(update_fields=['total_packages_count'])

    def __str__(self):
        if self.created_at:
            return f"Оприбуткування {self.created_at.strftime('%d.%m.%Y')}"
        return f"Оприбуткування (без дати)"
    
    class Meta:
        verbose_name = "Прибуткова накладна"
        verbose_name_plural = "Прибуткові накладні"

class ProductIncomeItem(models.Model):
    product_income = models.ForeignKey(ProductIncome, on_delete=models.CASCADE, verbose_name="Оприбуткування товару")
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, verbose_name="Варіація товару")
    quantity = models.PositiveIntegerField(verbose_name="Кількість")
    packages_count = models.PositiveIntegerField(verbose_name="Кількість упаковок")
    lot_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Номер лоту")
    package_type = models.ForeignKey(PackageType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тип упаковки")
    measurement_unit = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Одиниця виміру")

    def __str__(self):
        return f"{self.product_variation.name} ({self.quantity} {self.product_variation.measurement_unit})"
    
    class Meta:
        verbose_name = "Варіація в прибутковій накладній"
        verbose_name_plural = "Варіації в прибутковій накладній"


class BackupSettings(models.Model):
    auto_backup = models.BooleanField(default=True, verbose_name="Автоматичне резервне копіювання")
    backup_frequency = models.PositiveIntegerField(default=1, verbose_name="Частота резервного копіювання (днів)")
    last_backup = models.DateTimeField(null=True, blank=True, verbose_name="Останнє резервне копіювання")
    backup_location = models.CharField(max_length=255, default="backups/", verbose_name="Місце зберігання резервних копій")
    
    def __str__(self):
        return "Налаштування резервного копіювання"
    
    class Meta:
        verbose_name = "Налаштування резервного копіювання"
        verbose_name_plural = "Налаштування резервного копіювання"

class SystemParameter(models.Model):
    key = models.CharField(max_length=100, unique=True, verbose_name="Ключ")
    value = models.CharField(max_length=255, verbose_name="Значення")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    
    def __str__(self):
        return self.key
    
    class Meta:
        verbose_name = "Системний параметр"
        verbose_name_plural = "Системні параметри" 

class SystemParam(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва параметра")
    parameter = models.ForeignKey('self', on_delete=models.CASCADE, verbose_name="Параметр", 
                                 null=True, blank=True, related_name='children')
    has_parent = models.BooleanField(default=False, verbose_name="Має батьківський параметр")

    def get_all_children_ids(self):
        """Рекурсивно отримати ID всіх дочірніх параметрів"""
        result = []
        for child in self.children.all():
            result.append(child.id)
            result.extend(child.get_all_children_ids())
        return result

    def clean(self):
        # Перевірка на самопосилання
        if self.parameter == self:
            raise ValidationError("Параметр не може посилатися на самого себе")
        
        # Перевірка на циклічні посилання
        parent = self.parameter
        while parent is not None:
            if parent.parameter == self:
                raise ValidationError("Виявлено циклічне посилання між параметрами")
            parent = parent.parameter
        
        # Перевірка, чи батьківський параметр не є дочірнім для поточного
        if self.pk is not None and self.parameter is not None:
            children_ids = self.get_all_children_ids()
            if self.parameter.pk in children_ids:
                raise ValidationError("Батьківський параметр не може бути одним із дочірніх параметрів")
    
    def save(self, *args, **kwargs):
        # Викликаємо clean перед збереженням для валідації
        self.clean()
        
        # Встановлюємо has_parent на основі наявності батьківського параметра
        if self.parameter is not None:
            self.has_parent = True
        else:
            self.has_parent = False
            
        # Викликаємо батьківський метод save
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Системний параметр"
        verbose_name_plural = "Системні параметри"

