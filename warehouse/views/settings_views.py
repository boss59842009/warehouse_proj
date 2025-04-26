from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from datetime import datetime
import os
import zipfile
import shutil
import sqlite3
from ..models import BackupSettings, SystemParam, Culture, PackageType, MeasurementUnit
from ..forms import BackupSettingsForm, SystemParamForm, CultureForm, PackageTypeForm, MeasurementUnitForm

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
    system_parameters = SystemParam.objects.all()
    
    # Get reference data counts
    package_types_count = PackageType.objects.count()
    measurement_units_count = MeasurementUnit.objects.count()
    cultures_count = Culture.objects.count()
    form = SystemParamForm()
    parameters = SystemParam.objects.all()

    context = {
        'backup_settings': backup_settings,
        'system_parameters': system_parameters,
        'package_types_count': package_types_count,
        'measurement_units_count': measurement_units_count,
        'cultures_count': cultures_count,
        'form': form,
        'parameters': parameters,
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
    parameters = SystemParam.objects.all()
    
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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        form = SystemParamForm(request.POST)
        
        if form.is_valid():
            try:
                parameter = form.save()
                messages.success(request, f'Параметр успішно додано.')
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Параметр успішно додано.'
                    })
                return redirect('settings_index')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [str(e)]}
                    })
                messages.error(request, f'Помилка додавання параметра: {str(e)}')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': dict(form.errors.items())
                })
            # Для звичайного запиту помилки відображаються у формі
    else:
        form = SystemParamForm()
    
    context = {
        'form': form,
        'title': 'Додати системний параметр',
    }
    
    return render(request, 'warehouse/settings/parameter_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_system_parameter(request, pk):
    """View to edit a system parameter."""
    parameter = get_object_or_404(SystemParam, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        form = SystemParamForm(request.POST, instance=parameter)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Параметр "{parameter.name}" успішно оновлено.')
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f'Параметр "{parameter.name}" успішно оновлено.'
                    })
                return redirect('settings_index')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [str(e)]}
                    })
                messages.error(request, f'Помилка збереження параметра: {str(e)}')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': dict(form.errors.items())
                })
            # Для звичайного запиту помилки відображаються у формі
    else:
        form = SystemParamForm(instance=parameter)
    
    context = {
        'form': form,
        'parameter': parameter,
        'title': f'Редагувати параметр: {parameter.name}',
    }
    
    return render(request, 'warehouse/settings/parameter_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_system_parameter(request, pk):
    """View to delete a system parameter."""
    parameter = get_object_or_404(SystemParam, pk=pk)
    
    # Обробка GET-запиту - повертає на сторінку налаштувань
    # де відображається модальне вікно підтвердження
    if request.method == 'GET':
        return redirect('settings_index')
    
    # Обробка POST-запиту - виконує видалення параметра
    elif request.method == 'POST':
        # Зберігаємо назву параметра перед видаленням для повідомлення
        name = parameter.name
        
        # Перевіряємо наявність дочірніх параметрів
        children = parameter.children.all()
        if children.exists():
            # Якщо є дочірні параметри, видаляємо їх також
            for child in children.all():
                child_children = child.children.all()
                if child_children.exists():
                    child_children.delete()
                child.delete()
        print(parameter)
        # Видаляємо сам параметр
        parameter.delete()
        
        # Додаємо повідомлення про успішне видалення
        messages.success(request, f'Параметр "{name}" успішно видалено.')
        
        # Перенаправляємо на сторінку налаштувань
        return redirect('settings_index')
        
    # Якщо метод не GET і не POST, перенаправляємо на сторінку налаштувань
    return redirect('settings_index')
    
@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    """View to manage product categories."""
    categories = Culture.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = CultureForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Категорію "{form.cleaned_data["name"]}" успішно додано.')
            return redirect('manage_categories')
    else:
        form = CultureForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'warehouse/settings/manage_categories.html', context)

@login_required
@user_passes_test(is_admin)
def edit_category(request, pk):
    """View to edit a product category."""
    category = get_object_or_404(Culture, pk=pk)
    
    if request.method == 'POST':
        form = CultureForm(request.POST, instance=category)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Категорію "{category.name}" успішно оновлено.')
            return redirect('manage_categories')
    else:
        form = CultureForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    
    return render(request, 'warehouse/settings/category_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_category(request, pk):
    """View to delete a product category."""
    category = get_object_or_404(Culture, pk=pk)
    
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