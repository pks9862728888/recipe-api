from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
EDIT_USER_URL = reverse('user:me')


def create_user(**kwargs):
    """Creates a new user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        """Setting up API client for all test cases"""
        self.client = APIClient()

    def test_user_creation_success(self):
        """Test new user creation with payload is successful"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'test123@pass',
            'name': 'Test name'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        # Checking whether user is created or not based on response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Checking whether user's password is correctly encrypted or not
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_user_exists(self):
        """Test that no duplicate user creation is not possible"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'test123@pass',
            'name': 'Test name'
        }
        # Creating user
        create_user(**payload)

        # Trying to create another user with same credentials
        user = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(user.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that user creation with password too short is not possible"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'te',
            'name': 'Test name'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Checking whether user is created inspite of password too short
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exists)

    def test_user_authentication_token(self):
        """Test that token is created for a valid user"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'test@1234com'
        }
        create_user(**payload)
        response = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_invalid_credentials_generates_no_token(self):
        """Test that no token is returned for invalid credentials"""
        payload = {'email': 'test@gmail.com', 'password': 'test@123com'}
        create_user(**payload)
        response = self.client.post(
            CREATE_TOKEN_URL, {'email': 'test@gmail.com', 'password': 'wrong'})

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_token_for_unknown_user(self):
        """Test that no token is returned for unknown user"""
        response = self.client.post(
            CREATE_TOKEN_URL, {'email': 'test@gmail.com',
                               'password': 'test@1234com'})

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_token_for_blank_credentials(self):
        """Test that user registration is not possible for blank fields"""
        response = self.client.post(
            CREATE_TOKEN_URL, {'email': 'test@gmail.com', 'password': ''})

        self.assertNotIn('token', response.data)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized_error(self):
        """Test that unauthorized access to user data is not allowed"""
        response = self.client.get(EDIT_USER_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API request that require authentication"""

    def setUp(self):
        """Setup for authenticated user tests"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpassword',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retieving profile of authenticated user success"""
        response = self.client.get(EDIT_USER_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_request_not_allowed(self):
        """Test that POST request is not allowed on url"""
        response = self.client.post(EDIT_USER_URL, {})

        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        payload = {
            'password': 'Newpassword',
            'name': 'New name'
        }

        response = self.client.patch(EDIT_USER_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertTrue(response.status_code, status.HTTP_200_OK)
