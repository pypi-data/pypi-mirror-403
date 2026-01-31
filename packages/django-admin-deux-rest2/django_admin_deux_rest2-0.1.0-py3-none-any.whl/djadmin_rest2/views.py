"""
REST API views based on djrest.

Vendored from: https://gitlab.levitnet.be/levit/djrest
"""

import json
from typing import Any

from django.core.serializers import serialize
from django.http import HttpRequest, JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView


class ListCreateView(ListView):
    """
    Combined list and create view for REST API.
    
    - GET: Returns list of objects as JSON
    - POST: Creates new object from JSON data
    """
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return list of objects as JSON."""
        queryset = self.get_queryset()
        
        # Get fields to serialize
        fields = self.get_serializer_fields()
        
        # Serialize queryset
        data = serialize('json', queryset, fields=fields)
        
        return JsonResponse(json.loads(data), safe=False)
    
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Create new object from JSON data."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Create object
        obj = self.model(**data)
        
        try:
            obj.full_clean()
            obj.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Serialize created object
        fields = self.get_serializer_fields()
        serialized = serialize('json', [obj], fields=fields)
        
        return JsonResponse(json.loads(serialized)[0], status=201)
    
    def get_serializer_fields(self):
        """Get fields to serialize. Override in subclass."""
        return None  # None = all fields


class UpdateDeleteView(DetailView):
    """
    Combined update and delete view for REST API.
    
    - GET: Returns single object as JSON
    - PUT: Updates object from JSON data
    - DELETE: Deletes object
    """
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return single object as JSON."""
        obj = self.get_object()
        
        # Get fields to serialize
        fields = self.get_serializer_fields()
        
        # Serialize object
        data = serialize('json', [obj], fields=fields)
        
        return JsonResponse(json.loads(data)[0])
    
    def put(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Update object from JSON data."""
        obj = self.get_object()
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Update object fields
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        try:
            obj.full_clean()
            obj.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        # Serialize updated object
        fields = self.get_serializer_fields()
        serialized = serialize('json', [obj], fields=fields)
        
        return JsonResponse(json.loads(serialized)[0])
    
    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Delete object."""
        obj = self.get_object()
        obj.delete()
        
        return JsonResponse({'deleted': True}, status=204)
    
    def get_serializer_fields(self):
        """Get fields to serialize. Override in subclass."""
        return None  # None = all fields
