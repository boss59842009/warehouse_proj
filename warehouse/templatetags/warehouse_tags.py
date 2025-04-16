from django import template

register = template.Library()

@register.simple_tag
def calculate_total_items(orders):
    """Обчислює загальну кількість товарів у всіх замовленнях"""
    total = 0
    for order in orders:
        for item in order.items.all():
            total += item.quantity
    return total

@register.filter
def multiply(value, arg):
    """Multiply the arg by the value."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 