from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Custom permission to only allow users with role='ADMIN' to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN' 