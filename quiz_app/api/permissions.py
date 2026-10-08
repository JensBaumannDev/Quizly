from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allow object access only to the quiz owner."""

    def has_object_permission(self, request, view, obj):
        """Return whether the requesting user owns the quiz."""

        return obj.user == request.user
