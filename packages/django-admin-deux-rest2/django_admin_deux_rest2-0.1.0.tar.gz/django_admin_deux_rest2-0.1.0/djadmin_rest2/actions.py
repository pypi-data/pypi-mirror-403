"""
REST API actions for django-admin-deux.
"""

from djadmin.actions import BaseAction, GeneralActionMixin, RecordActionMixin
from .views import ListCreateView, UpdateDeleteView


class RestListCreateAction(GeneralActionMixin, BaseAction):
    """
    REST API action for listing and creating objects.
    
    - GET: List all objects
    - POST: Create new object
    """
    
    label = 'API List/Create'
    action_name = 'api_list'
    icon = 'api'
    
    def get_url_pattern(self) -> str:
        """
        Custom URL pattern for REST API list endpoint.
        
        Returns: api/{app}_{model}/
        """
        opts = self.model._meta
        return f'api/{opts.app_label}_{opts.model_name}/'
    
    def get_serializer_fields(self):
        """
        Get fields to serialize from ModelAdmin configuration.
        
        Priority:
        1. model_admin.fields (if set)
        2. All model fields (if fields='__all__' or None)
        """
        # Access model_admin via self (action instance)
        fields = getattr(self.model_admin, 'fields', None)
        
        if fields == '__all__' or fields is None:
            return None  # Serialize all fields
        
        return list(fields) if fields else None


class RestUpdateDeleteAction(RecordActionMixin, BaseAction):
    """
    REST API action for retrieving, updating, and deleting objects.
    
    - GET: Retrieve single object
    - PUT: Update object
    - DELETE: Delete object
    """
    
    label = 'API Update/Delete'
    action_name = 'api_detail'
    icon = 'api'
    
    def get_url_pattern(self) -> str:
        """
        Custom URL pattern for REST API detail endpoint.
        
        Returns: api/{app}_{model}/<pk>/
        """
        opts = self.model._meta
        return f'api/{opts.app_label}_{opts.model_name}/<pk>/'
    
    def get_serializer_fields(self):
        """
        Get fields to serialize from ModelAdmin configuration.
        
        Priority:
        1. model_admin.fields (if set)
        2. All model fields (if fields='__all__' or None)
        """
        fields = getattr(self.model_admin, 'fields', None)
        
        if fields == '__all__' or fields is None:
            return None  # Serialize all fields
        
        return list(fields) if fields else None
