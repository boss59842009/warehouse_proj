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
from ..models import Product, Culture, Inventory, ProductVariation
from ..forms import InventoryForm, ReportForm, OrderItemForm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

@login_required
def cuantity_list(request):
    """View to display list of inventory records."""
    variations = ProductVariation.objects.all().order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(variations, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'variations': page_obj,
    }
    
    return render(request, 'warehouse/inventory/cuantity_list.html', context)

@login_required
def product_income_create(request):
    """View to create a new product income record."""
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Інвентаризація успішно створена.')
            return redirect('inventory_list')
    else:
        form = OrderItemForm()  # Додано ініціалізацію форми для GET-запиту
    
    context = {
        'form': form,
    }
    return render(request, 'warehouse/inventory/product_income_create.html', context)

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
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.performed_by = request.user
            
            # Set expected quantity from current product quantity
            product = inventory.product
            inventory.quantity_expected = product.quantity
            
            inventory.save()
            
            messages.success(request, f'Інвентаризацію для "{product.name}" успішно створено.')
            return redirect('inventory_detail', pk=inventory.pk)
    else:
        form = InventoryForm()
    
    context = {
        'form': form,
        'title': 'Створити нову інвентаризацію',
    }
    
    return render(request, 'warehouse/inventory/inventory_form.html', context)

@login_required
def inventory_update(request, pk):
    """View to update an existing inventory record."""
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory)
        
        if form.is_valid():
            inventory = form.save()
            
            # Update product quantity if needed
            if 'update_product' in request.POST:
                product = inventory.product
                product.quantity = inventory.quantity_actual
                product.save()
                messages.success(request, f'Кількість товару "{product.name}" оновлено.')
            
            messages.success(request, f'Інвентаризацію успішно оновлено.')
            return redirect('inventory_detail', pk=inventory.pk)
    else:
        form = InventoryForm(instance=inventory)
    
    context = {
        'form': form,
        'inventory': inventory,
        'title': f'Редагувати інвентаризацію для {inventory.product.name}',
    }
    
    return render(request, 'warehouse/inventory/inventory_form.html', context)

@login_required
def stock_report(request):
    """View to display and generate stock reports."""
    products_variations = ProductVariation.objects.all().order_by('parent_product__culture__name', 'real_name')
    form = ReportForm(request.GET)
    
    # Apply filters if form is valid
    if form.is_valid():
        culture = form.cleaned_data.get('culture')
        
        if culture:
            products_variations = products_variations.filter(parent_product__culture=culture)
    
    # Calculate totals
    total_products = products_variations.count()
    total_quantity = products_variations.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_value = sum(product.quantity * product.price for product in products_variations)
    
    # Generate report if requested
    if 'generate' in request.GET and form.is_valid():
        report_format = form.cleaned_data.get('format', 'csv')
        
        if report_format == 'csv':
            return generate_csv_report(products_variations, culture)
        elif report_format == 'pdf':
            return generate_pdf_report(products_variations, culture)
    
    # Paginate results for display
    paginator = Paginator(products_variations, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'variations': page_obj,
        'form': form,
        'total_products': total_products,
        'total_quantity': total_quantity,
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