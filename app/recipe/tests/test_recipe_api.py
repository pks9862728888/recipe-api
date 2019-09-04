import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def recipe_image_upload_url(recipe_id):
    """Generates and returns url for upoading image for recipe"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def get_detail_url(recipe_id):
    """Generates and returns url for recipe detail view"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Sample tag'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sample ingredient'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample title',
        'time_minutes': 5,
        'price': 12.84
    }
    defaults.update(**params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeTest(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_is_required_for_access(self):
        """Test that authentication is required for retrieving recipe"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTest(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='tests@gmaail.com',
            password='tesdsfsfsdfsdfs'
        )
        self.client.force_authenticate(self.user)

    def test_retrieving_recipe(self):
        """Test retrieving recipe for authenticated user is success"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_recipe_authenticated(self):
        """Test that recipes are returned only for authenticated user"""
        user2 = get_user_model().objects.create_user(
            email='tstm@gmail.com',
            password='secretpasscode'
        )

        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_details(self):
        """Test that correct details are retrieved"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = get_detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test that creating basic recipe is successful"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 12,
            'price': 11.09
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(str(payload[key]), str(getattr(recipe, key)))

    def test_create_recipe_with_tags(self):
        """Test that creating recipe with tags is successful"""
        tag1 = sample_tag(user=self.user, name='Tag1')
        tag2 = sample_tag(user=self.user, name='Tag2')

        payload = {
            'title': 'Sample title',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 5,
            'price': 10.09
        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test that creating recipe with ingredients is successful"""
        ingredient1 = sample_ingredient(user=self.user, name='ingredient1')
        ingredient2 = sample_ingredient(user=self.user, name='ingredient2')

        payload = {
            'title': 'Sample title',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 4,
            'price': 33.22
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update(self):
        """Test that creating partial update is successful"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Sample tag')

        payload = {
            'title': 'New title',
            'tags': [new_tag.id, ]
        }
        url = get_detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update(self):
        """Test creating full update is successful"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'New title',
            'time_minutes': 10,
            'price': 99.99
        }
        url = get_detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(str(recipe.price), str(payload['price']))
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    def test_filter_recipe_by_tags(self):
        """Test returning recipe with specific tags"""
        tag1 = sample_tag(user=self.user, name='tag1')
        tag2 = sample_tag(user=self.user, name='tag2')
        recipe1 = sample_recipe(user=self.user, title='recipe1')
        recipe2 = sample_recipe(user=self.user, title='recipe2')
        recipe3 = sample_recipe(user=self.user, title='recipe3')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        res = self.client.get(
            RECIPE_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipe_by_ingredients(self):
        """Test returning recipe with specific ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='ingredient1')
        ingredient2 = sample_ingredient(user=self.user, name='ingredient2')
        recipe1 = sample_recipe(user=self.user, title='recipe1')
        recipe2 = sample_recipe(user=self.user, title='recipe2')
        recipe3 = sample_recipe(user=self.user, title='recipe3')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        res = self.client.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class RecipeImageUploadTests(TestCase):
    """Tests for uploading image in recipe"""

    def setUp(self):
        """Setup code for running tests"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='temp@gmail.com',
            password='supersecrettestpassword'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        """Cleanup code after running tests"""
        self.recipe.image.delete()

    def test_image_upload_to_recipe(self):
        """Test that image is successfully uploaded to recipe"""
        url = recipe_image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_invalid_image_upload_fail(self):
        """Test that invalid image upload to recipe is failed"""
        url = recipe_image_upload_url(self.recipe.id)
        res = self.client.post(url,
                               {'image': 'invalid-image'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
