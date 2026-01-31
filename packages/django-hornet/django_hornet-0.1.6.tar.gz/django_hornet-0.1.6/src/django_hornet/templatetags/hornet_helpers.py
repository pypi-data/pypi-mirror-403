from django import template
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse

from django_hornet.manager import ComponentManager

register = template.Library()


@register.simple_tag(takes_context=True)
def load_component(context, app_name, component_name, key=None):
    request = context["request"]
    manager = ComponentManager(request, app_name)
    component = manager.load_component(component_name)
    state = component.__dict__
    state["key"] = key
    html = render_to_string(f"components/{str(component_name).replace('_', '/')}.html", state)
    return html
