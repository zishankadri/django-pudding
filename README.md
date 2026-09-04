<div class="centered-content">
	<h1>Pudding</h1>
	<span class="font-medium text-center">
	The sweet spot between the low/no code and “starting from scratch” for CRUD-heavy applications.
	</span>
</div>

# What is Pudding?

**Pudding** is a deeply extensible and flexible Django meta-framework for CRUD-heavy applications that turns models into modern, reactive UIs in minutes. powered by Python, HTMX, and Alpine.js.

- **Rich UI Library:** Assembled out-of-the-box components.
- **Pure Python Logic:** Build complete end-to-end features without touching HTML or JavaScript.
- **Zero Lock-In:** Easily drop back into custom HTML and standard Django templates anytime.

## Pudding in action

The below code is an example of a simple CRUD application:

```python
from pudding import domains, ui, actions
from pudding.actions import Action, Edit, interactive_action
# ... (non-pudding imports)

@interactive_action(
    slug="cancel-order",
    icon="trash-2",
    before=actions.Modal(
        form=CancelOrderForm,
        title="Cancel Order",
        subtitle="Please select a reason for canceling this order.",
        # ...
    ),
)
def cancel_order(action: Action, request: HttpRequest, ctx: dict[str, Any]):
	# Order canceling logic
	...

@domains.register
class OrderDomain(domains.Domain):
    slug = "order"
    model = Order  # Optional
    icon = "shopping-cart"  # Optional

    view = ui.Table(
        model=Order,
        row_actions=[
            cancel_order.trigger(size="icon-sm"),
            Edit().trigger(size="icon-sm"),
        ],
        bulk_actions=[cancel_order.trigger],
    )

    actions = [View(view=view), Edit(), cancel_order]
```

## Installation

1. **Install the package**

```shell
pip install django-pudding
```

2. **Add it to INSTALLED_APPS in settings.py**

```python
INSTALLED_APPS = [
	# ...
    "pudding",
]
```

3. **URL Configuration**

Include the `pudding.urls` in your project's root `urls.py`. The framework uses a centralized dispatch pattern where actions are routed based on `domain_slug` and `action_slug`

```python
# urls.py
from django.urls import path, include
 
urlpatterns = [
    # ... other paths
    path("dashboard/", include("pudding.urls")),
]
```

# ## Key Concepts

- *"Everything is an **action**."*
- and **actions** can be attached to **domains**.
- you may use built-in or custom UI components in the actions.

Pudding is built on three primary pillars:

| Concept           | Description                                                                                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Domains**       | The top-level namespace grouping a resource (eg. Django model) with its specific actions and UI configuration.          |
| **Actions**       | Functional or interactive units of work (e.g., Add, View, Edit, Delete, or custom logic) triggered by user interaction. |
| **UI Components** | A Python-side rendering layer (Tables, Frames, Buttons) that produces HTMX-compliant HTML.                              |

You can have a single action attached to multiple domains (eg. "**Export data**" Action attached to ProductsDomain, OrdersDomain and CustomersDomain

every view function you can think of can be an action in Pudding, even the "**View**" action which is called "list_view" in the traditional django-admin is just an action in Pudding.

For a deep dive into how these layers interact, see [[architecture]].

## Design Philosophy

The core philosophy of Pudding is to minimize context-switching between Python, HTML, and JavaScript. It achieves this through:

- **Declarative Python**: Define UI components and data interactions entirely in Python.
- **HTMX-First**: All interactions default to partial DOM updates via HTMX.
- **Component-Based UI**: Pre-built, themeable components (Tables, Modals, Forms) that delegate to Django templates.
- **Domain-Driven Structure**: Organize application logic around "Domains" that encapsulate a Django model and its associated actions.
