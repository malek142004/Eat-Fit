from django import template
from django.utils import timezone
from datetime import date

register = template.Library()

@register.filter
def time_until(appointment_date):
    if not isinstance(appointment_date, date):
        return ""

    today = timezone.now().date()
    delta = appointment_date - today

    if delta.days < 0:
        return "Passed"
    elif delta.days == 0:
        return "Today"
    elif delta.days == 1:
        return "Tomorrow"
    elif delta.days < 7:
        return f"In {delta.days} days"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"In {weeks} week{'s' if weeks > 1 else ''}"
    elif delta.days < 365:
        months = delta.days // 30
        return f"In {months} month{'s' if months > 1 else ''}"
    else:
        years = delta.days // 365
        return f"In {years} year{'s' if years > 1 else ''}"
