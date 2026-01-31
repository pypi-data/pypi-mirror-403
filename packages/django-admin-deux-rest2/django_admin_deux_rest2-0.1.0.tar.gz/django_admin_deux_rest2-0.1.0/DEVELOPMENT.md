# djadmin-rest2 Development Guide

## Project Structure

```
djadmin-rest2/
├── venv/                      # Python 3.13 virtual environment
├── djadmin_rest2/             # Plugin package
│   ├── __init__.py            # Package info
│   ├── actions.py             # RestListCreateAction, RestUpdateDeleteAction
│   ├── views.py               # ListCreateView, UpdateDeleteView (vendored from djrest)
│   └── djadmin_hooks.py       # Plugin hooks (15 hooks)
├── todo/                      # Test Django app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py              # Item model (description, is_done)
│   ├── djadmin.py             # ItemAdmin with AllowAny permission
│   └── migrations/
├── manage.py                  # Django management script
├── settings.py                # Django settings
├── urls.py                    # URL configuration
├── wsgi.py                    # WSGI application
├── pyproject.toml             # Package metadata
├── README.md                  # User documentation
├── create_test_data.py        # Create sample todo items
├── test_api.sh                # Manual API testing script
└── DEVELOPMENT.md             # This file

```

## Setup

### 1. Install Dependencies

```bash
cd djadmin-rest2
source venv/bin/activate
uv pip install -e ../. -e .
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Test Data

```bash
python create_test_data.py
```

This creates 5 sample todo items.

## Running the Dev Server

```bash
python manage.py runserver 0.0.0.0:8000
```

**Demo App**: Visit http://localhost:8000/ for a JavaScript todo app that demonstrates the REST API in action.

**Admin Interface**: Visit http://localhost:8000/djadmin/todo/item/ for the django-admin-deux interface.

## API Endpoints

The plugin automatically registers REST API endpoints for all ModelAdmins:

### List/Create Endpoint

**URL**: `/djadmin/api/{app}_{model}/`

**GET** - List all objects:
```bash
curl http://localhost:8000/djadmin/api/todo_item/
```

**POST** - Create new object:
```bash
curl -X POST http://localhost:8000/djadmin/api/todo_item/ \
  -H "Content-Type: application/json" \
  -d '{"description": "New task", "is_done": false}'
```

### Detail/Update/Delete Endpoint

**URL**: `/djadmin/api/{app}_{model}/<pk>/`

**GET** - Retrieve single object:
```bash
curl http://localhost:8000/djadmin/api/todo_item/1/
```

**PUT** - Update object:
```bash
curl -X PUT http://localhost:8000/djadmin/api/todo_item/1/ \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated task", "is_done": true}'
```

**DELETE** - Delete object:
```bash
curl -X DELETE http://localhost:8000/djadmin/api/todo_item/1/
```

## Testing

### Manual Testing

Run the test script:

```bash
./test_api.sh
```

This tests all 5 HTTP methods (GET list, POST, GET detail, PUT, DELETE).

### Automated Testing

Tests will be added using BaseCRUDTestCase with custom test methods registered via the plugin hook.

**Test methods provided by plugin** (in `djadmin_hooks.py`):
- `_test_rest_list_get` - Test GET list endpoint
- `_test_rest_list_post` - Test POST create endpoint
- `_test_rest_detail_get` - Test GET detail endpoint
- `_test_rest_detail_put` - Test PUT update endpoint
- `_test_rest_detail_delete` - Test DELETE endpoint

## Plugin Architecture

### Actions

**`RestListCreateAction`** (General Action):
- Extends `GeneralActionMixin` + `BaseAction`
- URL pattern: `api/{app}_{model}/`
- View: `ListCreateView`
- Serialization: Auto-generated from `ModelAdmin.fields`

**`RestUpdateDeleteAction`** (Record Action):
- Extends `RecordActionMixin` + `BaseAction`
- URL pattern: `api/{app}_{model}/<pk>/` (generic `<pk>` supports int/uuid/string)
- View: `UpdateDeleteView`
- Serialization: Auto-generated from `ModelAdmin.fields`

### Hooks Used

1. **`djadmin_provides_features()`** - Advertises `'rest_api'` feature
2. **`djadmin_get_default_general_actions()`** - Registers `RestListCreateAction`
3. **`djadmin_get_default_record_actions()`** - Registers `RestUpdateDeleteAction`
4. **`djadmin_get_action_view_base_class(action)`** - Sets `ListCreateView`/`UpdateDeleteView`
5. **`djadmin_get_action_view_attributes(action)`** - Adds `get_serializer_fields()` method
6. **`djadmin_get_test_methods()`** - Registers 5 test methods for BaseCRUDTestCase

### Serialization

Fields are auto-detected from `ModelAdmin.fields`:

```python
@register(Item)
class ItemAdmin(ModelAdmin):
    fields = ['description', 'is_done']  # Only these fields serialized
```

If `fields` is not set or `'__all__'`, all model fields are serialized.

### Permissions

The plugin respects ModelAdmin's `permission_class`:

```python
from djadmin.plugins.permissions import AllowAny

@register(Item)
class ItemAdmin(ModelAdmin):
    permission_class = AllowAny()  # Public API, no authentication
```

**Available permission classes**:
- `AllowAny` - No restrictions (used for public APIs)
- `IsAuthenticated` - Requires login
- `IsStaff` - Requires staff status
- `IsSuperuser` - Requires superuser
- `HasDjangoPermission()` - Django model permissions

## Views (Vendored from djrest)

### `ListCreateView`

Combines Django's `ListView` with create functionality:
- **GET**: Serializes queryset to JSON using Django's serializer
- **POST**: Creates object from JSON body, validates, saves, returns created object

### `UpdateDeleteView`

Combines Django's `DetailView` with update/delete:
- **GET**: Serializes single object to JSON
- **PUT**: Updates object from JSON body, validates, saves, returns updated object
- **DELETE**: Deletes object, returns 204 No Content

Both views call `get_serializer_fields()` to determine which fields to serialize.

## Next Steps

1. **Manual Testing**: Start dev server and test with `test_api.sh`
2. **Write Automated Tests**: Create test suite using BaseCRUDTestCase
3. **Add More Features**: Consider pagination, filtering, sorting
4. **Documentation**: Expand README with more examples
5. **Distribution**: Publish to PyPI as `django-admin-deux-rest2`

## Files Modified

- Created plugin package: `djadmin_rest2/`
- Created test app: `todo/`
- Django project files: `settings.py`, `urls.py`, `manage.py`, `wsgi.py`
- Package metadata: `pyproject.toml`
- Documentation: `README.md`, `DEVELOPMENT.md`
- Test utilities: `create_test_data.py`, `test_api.sh`
