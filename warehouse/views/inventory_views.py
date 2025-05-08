from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.http import HttpResponse
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime
from ..models import Product, Culture, Inventory, ProductVariation, InventoryItem
from ..forms import InventoryForm, ProductIncomeItemForm, ProductVariationFilterForm, ReportForm, OrderItemForm, InventoryItemForm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import JsonResponse


@login_required
def cuantity_list(request):
    """View to display list of inventory records."""
    if request.method == 'GET':
        filter_form = ProductVariationFilterForm(request.GET)
        if filter_form.is_valid():
            filter_kwargs = {}
            if filter_form.cleaned_data['culture']:
                filter_kwargs['parent_product__culture'] = filter_form.cleaned_data['culture']
            if filter_form.cleaned_data['real_name']:
                filter_kwargs['real_name__icontains'] = filter_form.cleaned_data['real_name']
            if filter_form.cleaned_data['name']:
                filter_kwargs['import_name__icontains'] = filter_form.cleaned_data['name']
            if filter_form.cleaned_data['lot_number']:
                filter_kwargs['lot_number__icontains'] = filter_form.cleaned_data['lot_number']
            if filter_form.cleaned_data['measurement_unit']:
                filter_kwargs['measurement_unit'] = filter_form.cleaned_data['measurement_unit']
            if filter_form.cleaned_data['package_type']:
                filter_kwargs['package_type'] = filter_form.cleaned_data['package_type']

            variations = ProductVariation.objects.filter(**filter_kwargs)
    else:
        variations = ProductVariation.objects.all().order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(variations, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'variations': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'warehouse/inventory/cuantity_list.html', context)

@login_required
def product_income_create(request):
    """View to create a new product income record."""
    # Якщо це AJAX-запит для отримання варіацій
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('product_id'):
        product_id = request.GET.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            variations = ProductVariation.objects.filter(parent_product_id=product_id)
            variations_data = [
                {
                    'id': variation.id,
                    'name': variation.import_name or variation.name or 'Основна варіація',
                    'real_name': variation.real_name or '',
                    'lot_number': variation.lot_number or '',
                    'package_type': variation.package_type.id if variation.package_type else None,
                    'measurement_unit': variation.measurement_unit.id if variation.measurement_unit else None,
                    'product_id': variation.parent_product_id,
                    'culture': product.culture.name if product.culture else '',
                    'culture_id': product.culture.id if product.culture else None
                }
                for variation in variations
            ]
            return JsonResponse({'variations': variations_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Прибуткова накладна успішно створена.')
            return redirect('inventory_list')
    else:
        form = OrderItemForm()
    
    # Отримуємо всі товари та культури для відображення в шаблоні
    products = Product.objects.all().prefetch_related('variations', 'productimage_set')
    cultures = Culture.objects.all()
    
    # Створюємо formset для товарів у накладній
    ProductIncomeFormSet = formset_factory(ProductIncomeItemForm, extra=0)
    formset = ProductIncomeFormSet(prefix='form')
    
    context = {
        'form': form,
        'formset': formset,
        'products': products,
        'cultures': cultures,
    }
    return render(request, 'warehouse/movement/income_create_form.html', context)

@login_required
def inventory_detail(request, pk):
    """View to display details of a specific inventory record."""
    inventory = get_object_or_404(Inventory, pk=pk)
    
    context = {
        'inventory': inventory,
    }
    
    return render(request, 'warehouse/inventory/inventory_detail.html', context)

@login_required
def inventory_create(request):
    """View to create a new inventory record."""
    
    # Якщо це AJAX-запит для отримання варіацій
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('product_id'):
        product_id = request.GET.get('product_id')
        try:
            product = Product.objects.get(id=product_id)
            variations = ProductVariation.objects.filter(parent_product_id=product_id)
            variations_data = [
                {
                    'id': variation.id,
                    'name': variation.import_name or variation.name or 'Основна варіація',
                    'real_name': variation.real_name or product.real_name or '',
                    'lot_number': variation.lot_number or '',
                    'quantity': variation.quantity,
                    'package_type': variation.package_type.id if variation.package_type else None,
                    'measurement_unit': variation.measurement_unit.id if variation.measurement_unit else None,
                    'product_id': variation.parent_product_id,
                    'culture': product.culture.name if product.culture else '',
                    'culture_id': product.culture.id if product.culture else None
                }
                for variation in variations
            ]
            return JsonResponse({'variations': variations_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'POST':
        # Створюємо форму інвентаризації
        form = InventoryForm(request.POST)
        
        # Створюємо формсет для елементів інвентаризації
        InventoryItemFormSet = formset_factory(InventoryItemForm, extra=0)
        formset = InventoryItemFormSet(request.POST, prefix='form')
        
        if form.is_valid() and formset.is_valid():
            # Зберігаємо основну форму інвентаризації
            inventory = form.save(commit=False)
            inventory.performed_by = request.user
            inventory.movement_type = 'inventory'
            inventory.save()
            
            # Зберігаємо елементи інвентаризації
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                    item = item_form.save(commit=False)
                    item.inventory = inventory
                    
                    # Отримуємо product_variation
                    variation_id = item_form.cleaned_data.get('product_variation').id
                    item.product_variation = ProductVariation.objects.get(id=variation_id)
                    
                    # Зберігаємо різницю між очікуваною та фактичною кількістю
                    # Очікувана кількість береться з поточної кількості товару
                    item.quantity = item.product_variation.quantity
                    
                    # Якщо fact_quantity не надана, використовуємо поточну кількість
                    if 'fact_quantity' not in item_form.cleaned_data or item_form.cleaned_data['fact_quantity'] is None:
                        item.fact_quantity = item.quantity
                    else:
                        item.fact_quantity = item_form.cleaned_data['fact_quantity']
                    
                    # Обчислюємо різницю
                    item.difference = item.fact_quantity - item.quantity
                    
                    # Зберігаємо елемент інвентаризації
                    item.save()
                    
                    # Оновлюємо кількість товару в продукті
                    item.product_variation.quantity = item.fact_quantity
                    item.product_variation.save()
            
            messages.success(request, 'Інвентаризацію успішно створено.')
            return redirect('movement_list')
        else:
            # Якщо форма невалідна, виводимо помилки
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
            
            # Виводимо помилки формсету
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    messages.error(request, f"Помилка в товарі #{i+1}: {form_errors}")
    else:
        form = InventoryForm()
        # Створюємо порожній формсет
        InventoryItemFormSet = formset_factory(InventoryItemForm, extra=0)
        formset = InventoryItemFormSet(prefix='form')
    
    # Отримуємо всі товари та культури для відображення в шаблоні
    products = Product.objects.all().prefetch_related('variations', 'productimage_set')
    cultures = Culture.objects.all()
    
    # Отримуємо всі варіації продуктів
    variations = ProductVariation.objects.all().select_related('parent_product', 'parent_product__culture', 'measurement_unit', 'package_type')
    
    context = {
        'form': form,
        'formset': formset,
        'products': products,
        'variations': variations,
        'cultures': cultures,
    }
    return render(request, 'warehouse/inventory/inventory_form.html', context)

@login_required
def stock_report(request):
    """View to display and generate stock reports."""
    # Перевіряємо, чи натиснута кнопка скидання фільтрів
    if 'reset' in request.GET:
        # Видаляємо збережені фільтри з сесії
        if 'stock_report_filters' in request.session:
            del request.session['stock_report_filters']
        return redirect('stock_report')
    
    # Ініціалізуємо форми
    form = ReportForm(request.GET)
    
    # Визначаємо, які параметри фільтрації використовувати
    filter_params = request.GET
    
    # Якщо це запит на генерацію звіту і є збережені фільтри, використовуємо їх
    if 'generate' in request.GET and 'stock_report_filters' in request.session:
        filter_params = request.session['stock_report_filters']
    
    # Ініціалізуємо форму фільтрації з відповідними параметрами
    filter_form = ProductVariationFilterForm(filter_params)
    
    # Отримуємо відфільтровані дані
    variations = ProductVariation.objects.all().order_by('-created_at')
    
    if filter_form.is_valid():
        # Зберігаємо фільтри в сесії, якщо це не запит на генерацію звіту
        if 'generate' not in request.GET:
            request.session['stock_report_filters'] = request.GET.dict()
        
        # Застосовуємо фільтри
        filter_kwargs = {}
        if filter_form.cleaned_data['culture']:
            filter_kwargs['parent_product__culture'] = filter_form.cleaned_data['culture']
        if filter_form.cleaned_data['real_name']:
            filter_kwargs['real_name__icontains'] = filter_form.cleaned_data['real_name']
        if filter_form.cleaned_data['name']:
            filter_kwargs['import_name__icontains'] = filter_form.cleaned_data['name']
        if filter_form.cleaned_data['lot_number']:
            filter_kwargs['lot_number__icontains'] = filter_form.cleaned_data['lot_number']
        if filter_form.cleaned_data['measurement_unit']:
            filter_kwargs['measurement_unit'] = filter_form.cleaned_data['measurement_unit']
        if filter_form.cleaned_data['package_type']:
            filter_kwargs['package_type'] = filter_form.cleaned_data['package_type']
        
        if filter_kwargs:
            variations = variations.filter(**filter_kwargs)
    
    # Calculate totals
    total_products = variations.count()
    total_packages = variations.aggregate(Sum('packages_count'))['packages_count__sum'] or 0
    total_value = sum(product.quantity * product.price for product in variations)
    
    # Generate report if requested
    if 'generate' in request.GET and form.is_valid():
        report_format = form.cleaned_data.get('format', 'csv')
        if report_format == 'csv':
            return generate_csv_report(variations)
        elif report_format == 'pdf':
            return generate_pdf_report(variations)
    
    # Paginate results for display
    paginator = Paginator(variations, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'variations': page_obj,
        'form': form,
        'filter_form': filter_form,
        'total_products': total_products,
        'total_packages': total_packages,
        'total_value': total_value,
    }
    return render(request, 'warehouse/inventory/stock_report.html', context)

def generate_csv_report(products_variations, category=None):
    """Generate and return a CSV report of products."""
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stock_report_{timestamp}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header row
    header = [
        '№',
        'Культура', 
        'Назва справжня', 
        'Назва', 
        'Номер лоту', 
        'Од. виміру', 
        'Тип упаковки', 
        'Кількість упаковок', 
    ]
    writer.writerow(header)
    i = 1
    # Write data rows
    for product_variation in products_variations:
        culture_name = product_variation.parent_product.culture.name if product_variation.parent_product.culture else '-'
        measurement_unit_name = product_variation.measurement_unit.name if product_variation.measurement_unit else '-'                    
        row = [
            i, 
            culture_name, 
            product_variation.real_name, 
            product_variation.name, 
            product_variation.lot_number or '-',
            measurement_unit_name, 
            product_variation.package_type, 
            product_variation.packages_count, 
        ]
        writer.writerow(row)
        i += 1

    return response

def generate_pdf_report(products_variations, category=None):
    """Generate and return a PDF report of products."""
    response = HttpResponse(content_type='application/pdf')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stock_report_{timestamp}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF object in landscape orientation
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(A4[1], A4[0]))  # Виправлено дублювання параметра pagesize
    elements = []
    
    # Імпортуємо модулі один раз на початку функції
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    # Використовуємо вбудовані шрифти з reportlab, які підтримують кирилицю
    # або шрифти, які доступні в системі
    try:
        # Спробуємо використати шрифт Arial Unicode для кирилиці
        pdfmetrics.registerFont(TTFont('CustomFont', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
        # Використовуємо той самий шрифт для жирного тексту, оскільки немає окремого жирного варіанту
        pdfmetrics.registerFont(TTFont('CustomFont-Bold', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
        font_name = 'CustomFont'
        font_name_bold = 'CustomFont-Bold'
    except:
        try:
            # Спробуємо використати Arial, який також підтримує кирилицю
            pdfmetrics.registerFont(TTFont('CustomFont', '/System/Library/Fonts/Supplemental/Arial.ttf'))
            pdfmetrics.registerFont(TTFont('CustomFont-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
            font_name = 'CustomFont'
            font_name_bold = 'CustomFont-Bold'
        except:
            # Якщо не вдалося, використовуємо стандартний шрифт з кодуванням UTF-8
            font_name = 'Helvetica'
            font_name_bold = 'Helvetica-Bold'
    
    # Prepare data for the table
    data = [
        ['№', 'Культура', 'Назва справжня', 'Назва', 'Номер лоту', 'Од. виміру', 'Тип упаковки', 'Кількість упаковок']
    ]
    i = 1
    for product_variation in products_variations:
        culture_name = product_variation.parent_product.culture.name if product_variation.parent_product.culture else '-'
        measurement_unit_name = product_variation.measurement_unit.name if product_variation.measurement_unit else '-'
        
        row = [
            i,
            culture_name,
            product_variation.real_name,
            product_variation.name,
            product_variation.lot_number or '-',
            measurement_unit_name,
            product_variation.package_type,
            product_variation.packages_count,
        ]
        data.append(row)
        i += 1

    # Create table and set style
    # Налаштовуємо ширину стовпців для кращого відображення в альбомному режимі
    col_widths = [30, 80, 140, 140, 100, 80, 90, 120]  # Приблизні ширини стовпців
    table = Table(data, colWidths=col_widths)
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Центруємо номери
        ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),  # Центруємо кількість
    ])
    table.setStyle(style)
    
    # Add title
    title = 'Звіт про залишки товарів'
    if category:
        title += f' (Культура: {Culture.objects.get(pk=category).name})'
    
    # Додаємо заголовок до документу
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name_bold,
        alignment=1,  # По центру
        spaceAfter=12
    )
    
    elements.append(Paragraph(title, title_style))
    
    # Add date
    date_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontName=font_name,
        alignment=1,  # По центру
        spaceAfter=12
    )
    elements.append(Paragraph(f'Дата формування: {date_str}', date_style))
    
    # Add the table to the elements list
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    response.write(pdf)
    return response

@login_required
def product_inventory(request, product_id):
    """View to perform inventory for a specific product."""
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        actual_quantity = int(request.POST.get('actual_quantity', 0))
        comment = request.POST.get('comment', '')
        
        inventory = Inventory(
            product=product,
            quantity_expected=product.quantity,
            quantity_actual=actual_quantity,
            comment=comment,
            performed_by=request.user
        )
        inventory.save()
        
        # Update product quantity if requested
        if 'update_product' in request.POST:
            product.quantity = actual_quantity
            product.save()
            messages.success(request, f'Кількість товару "{product.name}" оновлено.')
        
        messages.success(request, f'Інвентаризацію для "{product.name}" успішно створено.')
        return redirect('inventory_detail', pk=inventory.pk)
    
    context = {
        'product': product,
    }
    
    return render(request, 'warehouse/inventory/product_inventory.html', context)

@login_required
def bulk_inventory(request):
    """View to perform inventory for multiple products at once."""
    products = Product.objects.filter(is_available=True).order_by('category__name', 'name')
    
    # Filter by category if provided
    category_id = request.GET.get('category', '')
    if category_id:
        try:
            category = Culture.objects.get(pk=int(category_id))
            products = products.filter(category=category)
        except (Culture.DoesNotExist, ValueError):
            pass
    
    if request.method == 'POST':
        inventories_created = 0
        products_updated = 0
        
        for product in products:
            qty_key = f'qty_{product.id}'
            if qty_key in request.POST:
                try:
                    actual_quantity = int(request.POST[qty_key])
                    comment = request.POST.get(f'comment_{product.id}', '')
                    
                    inventory = Inventory(
                        product=product,
                        quantity_expected=product.quantity,
                        quantity_actual=actual_quantity,
                        comment=comment,
                        performed_by=request.user
                    )
                    inventory.save()
                    inventories_created += 1
                    
                    # Update product quantity if checkbox is checked
                    if f'update_{product.id}' in request.POST:
                        product.quantity = actual_quantity
                        product.save()
                        products_updated += 1
                        
                except (ValueError, TypeError):
                    pass
        
        if inventories_created > 0:
            messages.success(request, f'Створено {inventories_created} записів інвентаризації. Оновлено кількість для {products_updated} товарів.')
        else:
            messages.warning(request, 'Жодного запису інвентаризації не створено.')
            
        return redirect('inventory_list')
    
    # Get categories for filter
    categories = Culture.objects.all()
    
    # Paginate results for display
    paginator = Paginator(products, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
    }
    
    return render(request, 'warehouse/inventory/bulk_inventory.html', context) 