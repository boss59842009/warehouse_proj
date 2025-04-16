from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime
import os
import zipfile
import shutil
import sqlite3
from ..models import BackupSettings, SystemParameter, Category, PackageType, MeasurementUnit, Culture
from ..forms import BackupSettingsForm, SystemParameterForm, CategoryForm, PackageTypeForm, MeasurementUnitForm, CultureForm

def is_admin(user):
    """Check if the user is an admin or superuser."""
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def settings_index(request):
    """Main settings page."""
    # Get backup settings
    try:
        backup_settings = BackupSettings.objects.first()
        if not backup_settings:
            backup_settings = BackupSettings.objects.create()
    except:
        backup_settings = BackupSettings.objects.create()
    
    # Get system parameters
    system_parameters = SystemParameter.objects.all()
    
    # Get reference data counts
    categories_count = Category.objects.count()
    package_types_count = PackageType.objects.count()
    measurement_units_count = MeasurementUnit.objects.count()
    cultures_count = Culture.objects.count()
    
    context = {
        'backup_settings': backup_settings,
        'system_parameters': system_parameters,
        'categories_count': categories_count,
        'package_types_count': package_types_count,
        'measurement_units_count': measurement_units_count,
        'cultures_count': cultures_count,
    }
    
    return render(request, 'warehouse/settings/settings_index.html', context)

@login_required
@user_passes_test(is_admin)
def backup_settings(request):
    """View to edit backup settings."""
    backup_settings = BackupSettings.objects.first()
    if not backup_settings:
        backup_settings = BackupSettings.objects.create()
    
    if request.method == 'POST':
        form = BackupSettingsForm(request.POST, instance=backup_settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Налаштування резервного копіювання успішно оновлено.')
            return redirect('settings_index')
    else:
        form = BackupSettingsForm(instance=backup_settings)
    
    context = {
        'form': form,
        'title': 'Налаштування резервного копіювання',
    }
    
    return render(request, 'warehouse/settings/backup_settings.html', context)

@login_required
@user_passes_test(is_admin)
def create_backup(request):
    """View to manually create a backup."""
    try:
        # Get backup settings
        backup_settings = BackupSettings.objects.first()
        if not backup_settings:
            backup_settings = BackupSettings.objects.create()
        
        # Create backup directory if it doesn't exist
        backup_dir = backup_settings.backup_location
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a timestamp for the backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        # Create a zip file for the backup
        with zipfile.ZipFile(backup_file, 'w') as zip_file:
            # Add database file to the backup
            zip_file.write('db.sqlite3', 'db.sqlite3')
            
            # Add media files
            for root, dirs, files in os.walk('media'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'media')
                    zip_file.write(file_path, f'media/{arcname}')
        
        # Update last backup time
        backup_settings.last_backup = datetime.now()
        backup_settings.save()
        
        messages.success(request, f'Резервну копію успішно створено: {backup_file}')
        
    except Exception as e:
        messages.error(request, f'Помилка створення резервної копії: {str(e)}')
    
    return redirect('settings_index')

@login_required
@user_passes_test(is_admin)
def restore_backup(request):
    """View to restore from a backup file."""
    if request.method == 'POST':
        try:
            backup_file = request.FILES.get('backup_file')
            
            if not backup_file:
                messages.error(request, 'Не вказано файл резервної копії.')
                return redirect('settings_index')
            
            # Create a temporary directory for extraction
            temp_dir = 'backup_temp'
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract the backup zip file
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Close database connection
            from django.db import connection
            connection.close()
            
            # Replace the database file
            shutil.copy(os.path.join(temp_dir, 'db.sqlite3'), 'db.sqlite3')
            
            # Replace media files if they exist in the backup
            media_backup_dir = os.path.join(temp_dir, 'media')
            if os.path.exists(media_backup_dir):
                if os.path.exists('media'):
                    shutil.rmtree('media')
                shutil.copytree(media_backup_dir, 'media')
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            messages.success(request, 'Відновлення з резервної копії успішно завершено. Будь ласка, перезапустіть сервер.')
            
        except Exception as e:
            messages.error(request, f'Помилка відновлення з резервної копії: {str(e)}')
        
        return redirect('settings_index')
    
    return render(request, 'warehouse/settings/restore_backup.html')

@login_required
@user_passes_test(is_admin)
def system_parameters(request):
    """View to manage system parameters."""
    parameters = SystemParameter.objects.all()
    
    if request.method == 'POST':
        # Handle parameter update
        for param in parameters:
            value = request.POST.get(f'value_{param.id}', '')
            if value != param.value:
                param.value = value
                param.save()
                messages.success(request, f'Параметр "{param.key}" успішно оновлено.')
        
        return redirect('system_parameters')
    
    context = {
        'parameters': parameters,
    }
    
    return render(request, 'warehouse/settings/system_parameters.html', context)

@login_required
@user_passes_test(is_admin)
def add_system_parameter(request):
    """View to add a new system parameter."""
    if request.method == 'POST':
        form = SystemParameterForm(request.POST)
        
        if form.is_valid():
            # Check if parameter already exists
            key = form.cleaned_data['key']
            if SystemParameter.objects.filter(key=key).exists():
                messages.error(request, f'Параметр з ключем "{key}" вже існує.')
                return render(request, 'warehouse/settings/parameter_form.html', {'form': form})
            
            form.save()
            messages.success(request, f'Параметр "{key}" успішно додано.')
            return redirect('system_parameters')
    else:
        form = SystemParameterForm()
    
    context = {
        'form': form,
        'title': 'Додати системний параметр',
    }
    
    return render(request, 'warehouse/settings/parameter_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_system_parameter(request, pk):
    """View to edit a system parameter."""
    parameter = get_object_or_404(SystemParameter, pk=pk)
    
    if request.method == 'POST':
        form = SystemParameterForm(request.POST, instance=parameter)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Параметр "{parameter.key}" успішно оновлено.')
            return redirect('system_parameters')
    else:
        form = SystemParameterForm(instance=parameter)
    
    context = {
        'form': form,
        'parameter': parameter,
        'title': f'Редагувати параметр: {parameter.key}',
    }
    
    return render(request, 'warehouse/settings/parameter_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_system_parameter(request, pk):
    """View to delete a system parameter."""
    parameter = get_object_or_404(SystemParameter, pk=pk)
    
    if request.method == 'POST':
        key = parameter.key
        parameter.delete()
        messages.success(request, f'Параметр "{key}" успішно видалено.')
        return redirect('system_parameters')
    
    context = {
        'parameter': parameter,
    }
    
    return render(request, 'warehouse/settings/parameter_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    """View to manage product categories."""
    categories = Category.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Категорію "{form.cleaned_data["name"]}" успішно додано.')
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/manage_categories.html', context)

@login_required
@user_passes_test(is_admin)
def edit_category(request, pk):
    """View to edit a product category."""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Категорію "{category.name}" успішно оновлено.')
            return redirect('manage_categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    
    return render(request, 'warehouse/settings/category_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    """View to delete a product category."""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'Категорію "{category_name}" успішно видалено.')
        except Exception as e:
            messages.error(request, f'Не вдалося видалити категорію: {str(e)}')
        
        return redirect('manage_categories')
    
    context = {
        'category': category,
    }
    
    return render(request, 'warehouse/settings/category_confirm_delete.html', context)

# Similar views for PackageType, MeasurementUnit, and Culture
@login_required
@user_passes_test(is_admin)
def manage_package_types(request):
    """View to manage package types."""
    package_types = PackageType.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = PackageTypeForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип упаковки "{form.cleaned_data["name"]}" успішно додано.')
            return redirect('manage_package_types')
    else:
        form = PackageTypeForm()
    
    context = {
        'package_types': package_types,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/manage_package_types.html', context)

@login_required
@user_passes_test(is_admin)
def edit_package_type(request, pk):
    """View to edit a package type."""
    package_type = get_object_or_404(PackageType, pk=pk)
    
    if request.method == 'POST':
        form = PackageTypeForm(request.POST, instance=package_type)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Тип упаковки "{package_type.name}" успішно оновлено.')
            return redirect('manage_package_types')
    else:
        form = PackageTypeForm(instance=package_type)
    
    context = {
        'form': form,
        'package_type': package_type,
    }
    
    return render(request, 'warehouse/settings/package_type_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_package_type(request, pk):
    """View to delete a package type."""
    package_type = get_object_or_404(PackageType, pk=pk)
    
    if request.method == 'POST':
        try:
            package_type_name = package_type.name
            package_type.delete()
            messages.success(request, f'Тип упаковки "{package_type_name}" успішно видалено.')
        except Exception as e:
            messages.error(request, f'Не вдалося видалити тип упаковки: {str(e)}')
        
        return redirect('manage_package_types')
    
    context = {
        'package_type': package_type,
    }
    
    return render(request, 'warehouse/settings/package_type_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def manage_measurement_units(request):
    """View to manage measurement units."""
    measurement_units = MeasurementUnit.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = MeasurementUnitForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Одиницю виміру "{form.cleaned_data["name"]}" успішно додано.')
            return redirect('manage_measurement_units')
    else:
        form = MeasurementUnitForm()
    
    context = {
        'measurement_units': measurement_units,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/manage_measurement_units.html', context)

@login_required
@user_passes_test(is_admin)
def edit_measurement_unit(request, pk):
    """View to edit a measurement unit."""
    unit = get_object_or_404(MeasurementUnit, pk=pk)
    
    if request.method == 'POST':
        form = MeasurementUnitForm(request.POST, instance=unit)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Одиницю виміру "{form.cleaned_data["name"]}" успішно оновлено.')
            return redirect('manage_measurement_units')
    else:
        form = MeasurementUnitForm(instance=unit)
    
    context = {
        'unit': unit,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/measurement_unit_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_measurement_unit(request, pk):
    """View to delete a measurement unit."""
    unit = get_object_or_404(MeasurementUnit, pk=pk)
    
    if request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        messages.success(request, f'Одиницю виміру "{unit_name}" успішно видалено.')
        return redirect('manage_measurement_units')
    
    context = {
        'unit': unit,
    }
    
    return render(request, 'warehouse/settings/measurement_unit_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def manage_cultures(request):
    """View to manage cultures."""
    cultures = Culture.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = CultureForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Культуру "{form.cleaned_data["name"]}" успішно додано.')
            return redirect('manage_cultures')
    else:
        form = CultureForm()
    
    context = {
        'cultures': cultures,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/manage_cultures.html', context)

@login_required
@user_passes_test(is_admin)
def edit_culture(request, pk):
    """View to edit a culture."""
    culture = get_object_or_404(Culture, pk=pk)
    
    if request.method == 'POST':
        form = CultureForm(request.POST, instance=culture)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Культуру "{form.cleaned_data["name"]}" успішно оновлено.')
            return redirect('manage_cultures')
    else:
        form = CultureForm(instance=culture)
    
    context = {
        'form': form,
        'culture': culture,
    }
    
    return render(request, 'warehouse/settings/culture_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_culture(request, pk):
    """View to delete a culture."""
    culture = get_object_or_404(Culture, pk=pk)
    
    if request.method == 'POST':
        try:
            culture_name = culture.name
            culture.delete()
            messages.success(request, f'Культуру "{culture_name}" успішно видалено.')
        except Exception as e:
            messages.error(request, f'Не вдалося видалити культуру: {str(e)}')
        
        return redirect('manage_cultures')
    
    context = {
        'culture': culture,
    }
    
    return render(request, 'warehouse/settings/culture_confirm_delete.html', context) 