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
from ..models import Product, Culture, Inventory
from ..forms import InventoryForm, ReportForm

@login_required
def inventory_list(request):
    """View to display list of inventory records."""
    inventories = Inventory.objects.all().order_by('-created_at')
    
    # Paginate results
    paginator = Paginator(inventories, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/inventory/inventory_list.html', context)

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
    products = Product.objects.all().order_by('category__name', 'name')
    form = ReportForm(request.GET)
    
    # Apply filters if form is valid
    if form.is_valid():
        category = form.cleaned_data.get('category')
        
        if category:
            products = products.filter(category=category)
    
    # Calculate totals
    total_products = products.count()
    total_quantity = products.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_value = sum(product.quantity * product.price for product in products)
    
    # Generate report if requested
    if 'generate' in request.GET and form.is_valid():
        report_format = form.cleaned_data.get('format', 'csv')
        
        if report_format == 'csv':
            return generate_csv_report(products, category)
        elif report_format == 'pdf':
            return generate_pdf_report(products, category)
    
    # Paginate results for display
    paginator = Paginator(products, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': total_value,
    }
    
    return render(request, 'warehouse/inventory/stock_report.html', context)

def generate_csv_report(products, category=None):
    """Generate and return a CSV report of products."""
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stock_report_{timestamp}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header row
    header = [
        'ID', 'Назва товару', 'Категорія', 'Культура', 
        'Кількість', 'Одиниця виміру', 'Ціна', 'Загальна вартість', 
        'Номер лоту', 'В наявності'
    ]
    writer.writerow(header)
    
    # Write data rows
    for product in products:
        culture_name = product.culture.name if product.culture else '-'
        measurement_unit_name = product.measurement_unit.name if product.measurement_unit else '-'
        total_value = product.quantity * product.price
        
        row = [
            product.id, 
            product.name, 
            product.category.name, 
            culture_name,
            product.quantity, 
            measurement_unit_name, 
            product.price, 
            total_value,
            product.lot_number or '-',
            'Так' if product.is_available else 'Ні',
        ]
        writer.writerow(row)
    
    return response

def generate_pdf_report(products, category=None):
    """Generate and return a PDF report of products."""
    response = HttpResponse(content_type='application/pdf')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stock_report_{timestamp}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create the PDF object
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Prepare data for the table
    data = [
        ['ID', 'Назва товару', 'Категорія', 'Кількість', 'Ціна', 'Загальна вартість']
    ]
    
    for product in products:
        total_value = product.quantity * product.price
        
        row = [
            str(product.id),
            product.name,
            product.category.name,
            str(product.quantity),
            str(product.price),
            str(total_value),
        ]
        data.append(row)
    
    # Create table and set style
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    
    # Add title
    title = 'Звіт про залишки товарів'
    if category:
        title += f' (Категорія: {category.name})'
    
    # Add date
    date_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    
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