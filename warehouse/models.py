from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва категорії")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

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

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Назва продукту")
    real_name = models.CharField(max_length=200, verbose_name="Назва справжня")
    culture = models.ForeignKey(Culture, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Культура")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    package_type = models.ForeignKey(PackageType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тип упаковки")
    measurement_unit = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Одиниця виміру")
    lot_number = models.CharField(max_length=100, verbose_name="Номер лоту", blank=True, null=True)
    import_name = models.CharField(max_length=200, verbose_name="Імпорт назва", blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0, verbose_name="Кількість")
    packages_count = models.PositiveIntegerField(default=0, verbose_name="Кількість упаковок")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Фото товару")
    description = models.TextField(blank=True, null=True, verbose_name="Опис товару")
    is_available = models.BooleanField(default=True, verbose_name="В наявності")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ціна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='products/', verbose_name="Зображення")
    
    def __str__(self):
        return f"Зображення для {self.product.name}"
    
    class Meta:
        verbose_name = "Зображення товару"
        verbose_name_plural = "Зображення товарів"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'В обробці'),
        ('processing', 'Обробляється'),
        ('completed', 'Завершено'),
        ('canceled', 'Скасовано'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Користувач")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Загальна сума")
    
    def __str__(self):
        return f"Замовлення №{self.id} від {self.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Замовлення")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за одиницю")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Загальна ціна")
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Товар у замовленні"
        verbose_name_plural = "Товари у замовленні"

class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity_expected = models.PositiveIntegerField(default=0, verbose_name="Очікувана кількість")
    quantity_actual = models.PositiveIntegerField(default=0, verbose_name="Фактична кількість")
    difference = models.IntegerField(default=0, verbose_name="Відхилення")
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Виконав")
    
    def save(self, *args, **kwargs):
        self.difference = self.quantity_actual - self.quantity_expected
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Інвентаризація {self.product.name} від {self.created_at.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Інвентаризація"
        verbose_name_plural = "Інвентаризації"

class ProductMovement(models.Model):
    MOVEMENT_TYPES = (
        ('incoming', 'Надходження'),
        ('outgoing', 'Видача'),
        ('return', 'Повернення'),
        ('write_off', 'Списання'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name="Тип руху")
    quantity = models.PositiveIntegerField(verbose_name="Кількість")
    date = models.DateTimeField(default=timezone.now, verbose_name="Дата")
    document_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Номер документу")
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар")
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Виконав")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Замовлення")
    
    def __str__(self):
        return f"{self.get_movement_type_display()} {self.product.name} ({self.quantity} {self.product.measurement_unit})"
    
    class Meta:
        verbose_name = "Рух товару"
        verbose_name_plural = "Рух товарів"

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