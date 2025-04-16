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