from django.views.generic import TemplateView
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse

from .manager import ComponentManager


class HornetView(TemplateView):

    def template_wrapper(self):
        return render_to_string(
            f"components/{str(self.component_name).replace('_', '/')}.html", self.state
        )

    def render_to_component(self, state=None):
        if not state is None:
            self.state = state
        else:
            self.state = self.component.__dict__
        return render(self.request, self.template_name, {"component_html": self.template_wrapper()})

    def update_to_html(self):
        self.manager.save_component(self.component_name, self.component)
        html = self.template_wrapper()
        return html
    
    def update_to_component(self):
        self.manager.save_component(self.component_name, self.component)
        html = self.template_wrapper()
        return HttpResponse(html)

    def dispatch(self, *args, **kwargs):
        self.manager = ComponentManager(self.request)
        self.component = self.manager.load_component(self.component_name)
        self.state = self.component.__dict__
        self.html = self.template_wrapper()
        return super(HornetView, self).dispatch(*args, **kwargs)
