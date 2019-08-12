from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for creating token for user"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, args):
        """Validate and authenticate the user"""
        email = args.get('email')
        password = args.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        # If user is not authenticate then raise validation error
        if not user:
            msg = _('Unable to authenticate with the given credentials.')
            raise serializers.ValidationError(msg, code='authentication')

        args['user'] = user
        return args
