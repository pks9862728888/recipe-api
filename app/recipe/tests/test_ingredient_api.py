from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from recipe.serializers import IngredientSerializer
from core.models import Ingredient

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):
    """Tests the publicly available ingredient"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving Ingredients"""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientTest(TestCase):
    """Test the privately available Ingredient"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@gmail.com",
            password="testpassword"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=self.user, name="Cucumber")
        Ingredient.objects.create(user=self.user, name="Brinjal")

        res = self.client.get(INGREDIENT_URL)

        ingredient = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredient, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_ingredient_authenticated_user(self):
        """Test that ingredients are returned only for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'testdd@gmail.com',
            'testpassword2'
        )

        Ingredient.objects.create(user=user2, name='Cabbage')
        ingredient = Ingredient.objects.create(user=self.user, name='Potato')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test that create ingredinent is successful"""
        payload = {'name': 'brinjal'}
        self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test that creating invalid ingredient is not allowed"""
        res = self.client.post(INGREDIENT_URL, {'name': ''})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
