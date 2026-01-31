## django-hornet


```bash
pip install django-hornet
```

```python
MIDDLEWARE = [
    ...
    "django.middleware.csrf.CsrfViewMiddleware",
    "django_hornet.middleware.HtmxMiddleware",
    ...
]
```

#### Example

```python
from django_hornet.views import HornetView

class CounterView(HornetView):
    template_name = "counter.html"
    component_name = "counter"

    def get(self, request, *args, **kwargs):
        return self.render_to_component(self.html)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "increment":
            self.component.increment()
        elif action == "decrement":
            self.component.decrement()
        return self.update_to_component()
```

```html
<div id="result">
  <button
    hx-post="{% url 'counter' %}"
    hx-vals='{"action": "decrement"}'
    hx-target="#result"
  >
    -
  </button>
  <span>{{ count }}</span>
  <button
    hx-post="{% url 'counter' %}"
    hx-vals='{"action": "increment"}'
    hx-target="#result"
  >
    +
  </button>
</div>

```
