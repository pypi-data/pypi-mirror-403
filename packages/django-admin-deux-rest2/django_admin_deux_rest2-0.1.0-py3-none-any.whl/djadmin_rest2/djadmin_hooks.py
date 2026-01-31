"""
Plugin hooks for django-admin-deux-rest2.
"""

from djadmin.plugins import hookimpl


@hookimpl
def djadmin_get_required_apps():
    """
    Register this plugin in INSTALLED_APPS.
    
    This is required for Django to find the plugin's templates.
    """
    return ['djadmin_rest2']


@hookimpl
def djadmin_provides_features():
    """
    Advertise features this plugin provides.
    
    Provides:
    - 'rest_api': REST API endpoints
    - 'crud': Create, Read, Update, Delete operations via REST API
    """
    return ['rest_api', 'crud']


@hookimpl
def djadmin_get_default_general_actions():
    """Register REST API list/create action for all ModelAdmins."""
    from .actions import RestListCreateAction
    return [RestListCreateAction]


@hookimpl
def djadmin_get_default_record_actions():
    """Register REST API update/delete action for all ModelAdmins."""
    from .actions import RestUpdateDeleteAction
    return [RestUpdateDeleteAction]


@hookimpl
def djadmin_get_action_view_base_class(action):
    """
    Override base view class for REST actions.
    
    This allows the actions to use ListCreateView and UpdateDeleteView
    instead of standard Django CBVs.
    """
    from .actions import RestListCreateAction, RestUpdateDeleteAction
    from .views import ListCreateView, UpdateDeleteView
    
    return {
        RestListCreateAction: ListCreateView,
        RestUpdateDeleteAction: UpdateDeleteView,
    }


@hookimpl
def djadmin_get_action_view_attributes(action):
    """
    Add serializer fields to REST API views.
    
    This makes the get_serializer_fields() method from the action
    available on the view.
    """
    from .actions import RestListCreateAction, RestUpdateDeleteAction
    
    # Get serializer fields from action
    if isinstance(action, (RestListCreateAction, RestUpdateDeleteAction)):
        fields = action.get_serializer_fields()
        
        return {
            type(action): {
                'get_serializer_fields': lambda self: fields,
            }
        }
    
    return {}


@hookimpl
def djadmin_get_test_methods():
    """
    Provide test methods for REST API actions.
    
    These will be used by BaseCRUDTestCase to test the REST endpoints.
    """
    from .actions import RestListCreateAction, RestUpdateDeleteAction
    
    def test_rest_list_get(test_case, action):
        """Test GET request to list endpoint."""
        url = test_case._get_action_url(action)
        response = test_case.client.get(url)
        
        test_case.assertEqual(response.status_code, 200)
        test_case.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        test_case.assertIsInstance(data, list)
    
    def test_rest_list_post(test_case, action):
        """Test POST request to create endpoint."""
        import json
        
        url = test_case._get_action_url(action)
        
        # Get create data from test case
        create_data = test_case.get_create_data()
        
        response = test_case.client.post(
            url,
            data=json.dumps(create_data),
            content_type='application/json'
        )
        
        test_case.assertEqual(response.status_code, 201)
        test_case.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        test_case.assertIn('pk', data)
    
    def test_rest_detail_get(test_case, action):
        """Test GET request to detail endpoint."""
        # Use the object created in setUp()
        url = test_case._get_action_url(action, test_case.obj)
        response = test_case.client.get(url)
        
        test_case.assertEqual(response.status_code, 200)
        test_case.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        test_case.assertEqual(data['pk'], test_case.obj.pk)
    
    def test_rest_detail_put(test_case, action):
        """Test PUT request to update endpoint."""
        import json
        
        # Use the object created in setUp()
        url = test_case._get_action_url(action, test_case.obj)
        
        # Get update data - pass the object
        update_data = test_case.get_update_data(test_case.obj)
        
        response = test_case.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        test_case.assertEqual(response.status_code, 200)
        test_case.assertEqual(response['Content-Type'], 'application/json')
    
    def test_rest_detail_delete(test_case, action):
        """Test DELETE request to delete endpoint."""
        # Create a separate object to delete (not test_case.obj)
        kwargs = test_case.get_factory_delete_kwargs()
        obj_to_delete = test_case.model_factory_class.create(**kwargs)
        
        url = test_case._get_action_url(action, obj_to_delete)
        response = test_case.client.delete(url)
        
        test_case.assertEqual(response.status_code, 204)
        
        # Verify object is deleted
        test_case.assertFalse(
            test_case.model.objects.filter(pk=obj_to_delete.pk).exists()
        )
    
    return {
        RestListCreateAction: {
            '_test_rest_list_get': test_rest_list_get,
            '_test_rest_list_post': test_rest_list_post,
        },
        RestUpdateDeleteAction: {
            '_test_rest_detail_get': test_rest_detail_get,
            '_test_rest_detail_put': test_rest_detail_put,
            '_test_rest_detail_delete': test_rest_detail_delete,
        }
    }
