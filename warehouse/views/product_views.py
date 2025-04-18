from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from ..models import Product, Culture, ProductImage, ProductVariation
from ..forms import ProductForm, ProductImageFormSet, ProductFilterForm

@login_required
def product_list(request):
    """View to display the list of products."""
    products = Product.objects.all().order_by('name')
    filter_form = ProductFilterForm(request.GET)
    
    # Apply filters if form is valid
    if filter_form.is_valid():
        culture = filter_form.cleaned_data.get('culture')
        available_only = filter_form.cleaned_data.get('available_only')
        search = filter_form.cleaned_data.get('search')
        
        if culture:
            products = products.filter(culture=culture)
        
        if available_only:
            products = products.filter(is_available=True)
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(real_name__icontains=search) | 
                Q(import_name__icontains=search)
            )
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'warehouse/product/product_list.html', context)

@login_required
def product_detail(request, pk):
    """View to display details of a specific product."""
    product = get_object_or_404(Product, pk=pk)
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        culture=product.culture
    ).exclude(id=product.id)[:4]

    # Get all variations of the product
    variations = ProductVariation.objects.filter(parent_product=product)
    # Paginate results
    paginator = Paginator(variations, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'product': product,
        'related_products': related_products,
        'variations': page_obj,
    }    
    return render(request, 'warehouse/product/product_detail.html', context)

@login_required
def product_create(request):
    """View to create a new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=None, prefix='images')
        
        if form.is_valid() and formset.is_valid():
            # Спочатку зберігаємо товар
            product = form.save()
            
            # Прив'язуємо формсет до створеного товару
            formset.instance = product
            
            # Зберігаємо зображення
            image_instances = formset.save(commit=False)
            for image in image_instances:
                image.product = product  # Явно встановлюємо зв'язок
                image.save()
            
            # Видаляємо позначені для видалення зображення
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f'Товар "{product.name}" успішно створено.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()
        formset = ProductImageFormSet(prefix='images')
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Створення нового товару',
    }
    
    return render(request, 'warehouse/product/product_form.html', context)

@login_required
def product_update(request, pk):
    """View to update an existing product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product, prefix='images')
        
        if form.is_valid() and formset.is_valid():
            product = form.save()
            # Зберігаємо формсет
            formset.save()
            messages.success(request, f'Товар "{product.real_name}" успішно оновлено.')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product, prefix='images')
    
    context = {
        'form': form,
        'formset': formset,
        'product': product,
        'title': f'Редагування товару: {product.real_name}',
    }
    
    return render(request, 'warehouse/product/product_form.html', context)

@login_required
def product_delete(request, pk):
    """View to delete a product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успішно видалено.')
        return redirect('product_list')
    return redirect('product_detail', pk=product.pk)

@login_required
def category_products(request, category_id):
    """View to display products filtered by category."""
    category = get_object_or_404(Culture, pk=category_id)
    products = Product.objects.filter(category=category).order_by('name')
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/product/category_products.html', context)

@login_required
def culture_products(request, culture_id):
    """View to display products filtered by culture."""
    culture = get_object_or_404(Culture, pk=culture_id)
    products = Product.objects.filter(culture=culture).order_by('name')
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'culture': culture,
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/product/culture_products.html', context) 