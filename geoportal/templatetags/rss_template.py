from datetime import datetime
from django import template
register = template.Library()
@register.filter
def convert_str_date(value):
    try:
        return str(datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').date())
    except:
        return value