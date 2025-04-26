from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('categories/<int:category_id>/products/', views.category_products, name='category_products'),
    path('cultures/<int:culture_id>/products/', views.culture_products, name='culture_products'),

    # Order URLs
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/new/', views.order_create, name='order_create'),
    path('order/new/confirm/', views.order_confirm, name='order_confirm'),
    path('order/complete/', views.order_complete, name='order_complete'),
    path('orders/<int:pk>/cancel/', views.order_cancel, name='order_cancel'),
    # Cart URLs
    # path('cart/', views.view_cart, name='view_cart'),
    # path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/update/', views.update_cart, name='update_cart'),
    # path('cart/clear/', views.clear_cart, name='clear_cart'),
    # path('checkout/', views.checkout, name='checkout'),
    
    # Inventory URLs
    path('cuantity/', views.cuantity_list, name='cuantity_list'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inventory/new/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_update, name='inventory_update'),
    path('inventory/product/<int:product_id>/', views.product_inventory, name='product_inventory'),
    path('inventory/bulk/', views.bulk_inventory, name='bulk_inventory'),
    path('reports/stock/', views.stock_report, name='stock_report'),
    
    # Product Movement URLs
    path('product_income/new/', views.product_income_create, name='product_income_create'),
    path('movements/', views.movement_list, name='movement_list'),
    # path('movements/<int:pk>/', views.movement_detail, name='movement_detail'),
    # path('movements/incoming/', views.incoming_movement, name='incoming_movement'),
    # path('movements/outgoing/', views.outgoing_movement, name='outgoing_movement'),
    # path('products/<int:product_id>/movements/', views.product_movements, name='product_movements'),
    
    # Settings URLs
    path('settings/', views.settings_index, name='settings_index'),
    path('settings/backup/', views.backup_settings, name='backup_settings'),
    path('settings/backup/create/', views.create_backup, name='create_backup'),
    path('settings/backup/restore/', views.restore_backup, name='restore_backup'),
    path('settings/parameters/', views.system_parameters, name='system_parameters'),
    path('settings/parameters/add/', views.add_system_parameter, name='add_system_parameter'),
    path('settings/parameters/<int:pk>/edit/', views.edit_system_parameter, name='edit_system_parameter'),
    path('settings/parameters/<int:pk>/delete/', views.delete_system_parameter, name='delete_system_parameter'),
    path('settings/categories/', views.manage_categories, name='manage_categories'),
    path('settings/categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('settings/categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('settings/package-types/', views.manage_package_types, name='manage_package_types'),
    path('settings/package-types/<int:pk>/edit/', views.edit_package_type, name='edit_package_type'),
    path('settings/package-types/<int:pk>/delete/', views.delete_package_type, name='delete_package_type'),
    path('settings/measurement-units/', views.manage_measurement_units, name='manage_measurement_units'),
    path('settings/measurement-units/<int:pk>/edit/', views.edit_measurement_unit, name='edit_measurement_unit'),
    path('settings/measurement-units/<int:pk>/delete/', views.delete_measurement_unit, name='delete_measurement_unit'),
    path('settings/cultures/', views.manage_cultures, name='manage_cultures'),
    path('settings/cultures/<int:pk>/edit/', views.edit_culture, name='edit_culture'),
    path('settings/cultures/<int:pk>/delete/', views.delete_culture, name='delete_culture'),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='warehouse/auth/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(template_name='warehouse/auth/password_change.html'), name='password_change'),
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='warehouse/auth/password_change_done.html'), name='password_change_done'),
] 