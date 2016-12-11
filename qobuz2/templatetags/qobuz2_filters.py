from django import template

from qobuz2.views import reverse_state_data


register = template.Library()


@register.filter
def state_name(value):
    return reverse_state_data[value]
