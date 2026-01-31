# django-admin-deux-rest2

REST API plugin for [django-admin-deux](https://github.com/yourusername/django-admin-deux).

Automatically adds RESTful API endpoints to all registered ModelAdmins, providing full CRUD operations via JSON.

## 📚 Documentation

See the [full documentation](djadmin_rest2/README.md) for:
- Installation instructions
- Configuration options
- API endpoint reference
- JavaScript examples with CSRF handling
- Testing with BaseCRUDTestCase
- Advanced usage

## 🚀 Quick Start

```bash
pip install django-admin-deux-rest2
```

```python
# settings.py
from djadmin import djadmin_apps

INSTALLED_APPS = [
    # ... Django apps
    'myapp',
    *djadmin_apps(),  # Auto-discovers and registers djadmin-rest2
]
```

```python
# myapp/djadmin.py
from djadmin import ModelAdmin, register
from djadmin.plugins.permissions import AllowAny

@register(Task)
class TaskAdmin(ModelAdmin):
    fields = ['title', 'description', 'status']
    permission_class = AllowAny()  # Public API
```

That's it! Your model now has REST API endpoints at:
- `GET/POST /djadmin/api/myapp_task/`
- `GET/PUT/DELETE /djadmin/api/myapp_task/<pk>/`

## 🎨 Demo Application

This repository includes a complete demo:

```bash
cd djadmin-rest2
python manage.py runserver
```

- **JavaScript Todo App**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/djadmin/todo/item/
- **REST API**: http://localhost:8000/djadmin/api/todo_item/

## 📦 Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development setup and testing instructions.

## 🤝 Contributing

Contributions are welcome! This is part of the django-admin-deux plugin ecosystem.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
