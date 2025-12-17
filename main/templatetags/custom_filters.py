from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

# Color scheme matching the home template (orange/red gradient)
TEMPLATE_COLORS = {
    'primary_gradient': 'linear-gradient(90deg, #f8896e, #f66056)',
    'primary_start': '#f8896e',
    'primary_end': '#f66056',
    'secondary_gradient': 'linear-gradient(135deg, #fdbcb4 0%, #f8896e 100%)',
    'breakfast': '#f8896e',
    'lunch': '#f66056',
    'dinner': '#ff6655',
    'snack': '#fdbcb4',
    'calories': '#e74c3c',
    'protein': '#3498db',
    'carbs': '#f39c12',
    'fat': '#9b59b6',
    'text_dark': '#2c3e50',
    'text_light': '#7f8c8d',
    'background_light': '#f8f9fa',
    'white': '#ffffff'
}

@register.filter
def get_color(color_name):
    """Get color value from template color scheme"""
    return TEMPLATE_COLORS.get(color_name, '#667eea')

@register.filter
def meal_type_color(meal_type):
    """Get color for meal type"""
    colors = {
        'breakfast': TEMPLATE_COLORS['breakfast'],
        'lunch': TEMPLATE_COLORS['lunch'],
        'dinner': TEMPLATE_COLORS['dinner'],
        'snack': TEMPLATE_COLORS['snack']
    }
    return colors.get(meal_type.lower(), TEMPLATE_COLORS['primary_start'])

@register.filter
def nutrition_color(nutrient):
    """Get color for nutrient type"""
    colors = {
        'calories': TEMPLATE_COLORS['calories'],
        'protein': TEMPLATE_COLORS['protein'],
        'carbs': TEMPLATE_COLORS['carbs'],
        'fat': TEMPLATE_COLORS['fat']
    }
    return colors.get(nutrient.lower(), TEMPLATE_COLORS['primary_start'])

@register.filter
def gradient_style(color_type='primary'):
    """Get gradient style for CSS"""
    if color_type == 'primary':
        return TEMPLATE_COLORS['primary_gradient']
    elif color_type == 'secondary':
        return TEMPLATE_COLORS['secondary_gradient']
    else:
        return TEMPLATE_COLORS['primary_gradient']

@register.filter
def rgba_color(color_name, alpha=1):
    """Convert hex color to rgba with alpha"""
    color = TEMPLATE_COLORS.get(color_name, '#667eea')
    # Simple hex to rgb conversion
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})'

@register.filter
def progress_color(value, max_value):
    """Get progress bar color based on percentage"""
    try:
        percentage = (float(value) / float(max_value)) * 100
        if percentage < 25:
            return TEMPLATE_COLORS['breakfast']
        elif percentage < 50:
            return TEMPLATE_COLORS['lunch']
        elif percentage < 75:
            return TEMPLATE_COLORS['dinner']
        else:
            return TEMPLATE_COLORS['snack']
    except (ValueError, ZeroDivisionError):
        return TEMPLATE_COLORS['primary_start']
