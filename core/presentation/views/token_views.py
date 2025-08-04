# core/presentation/views/token_views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rolepermissions.roles import get_user_roles
from rolepermissions.checkers import has_permission

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        roles = get_user_roles(user)
        role_names = [role.get_name() for role in roles]
        
        token['roles'] = role_names
        
        permissions = {}
        
        if roles:
            role = roles[0]            
            available_permissions = role.available_permissions
            
            for permission in available_permissions:
                permissions[permission] = has_permission(user, permission)
        
        token['permissions'] = permissions
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        user = self.user
        roles = get_user_roles(user)
        role_names = [role.get_name() for role in roles]
        
        data['user_id'] = user.id
        data['email'] = user.email
        data['roles'] = role_names
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer