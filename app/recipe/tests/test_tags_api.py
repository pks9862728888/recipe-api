from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagApiTests(TestCase):
    """Test the publicly available API tags"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving the tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@gmail.com",
            password="testPassword"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""

        Tag.objects.create(user=self.user, name="recipes")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tag_retrieved_limited_to_user(self):
        """Test that tags are retrieved only for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'temp@gmail.com',
            'temp_password'
        )

        Tag.objects.create(user=user2, name="unauthorised")
        tag = Tag.objects.create(user=self.user, name='dessert')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag invalid"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_tag_assigned_to_recipe(self):
        """Test filtering tags those assigned to recipies only"""
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')

        recipe = Recipe.objects.create(
            user=self.user,
            title='recipe1',
            time_minutes=23,
            price=33.00
        )
        recipe.tags.add(tag1)

        res = self.client.get(
            TAGS_URL,
            {'assigned_only': 1}
        )
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtering_tags_assigned_unique(self):
        """Test filtering tags returns only unique values"""
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        Tag.objects.create(user=self.user, name='ingredient2')

        recipe1 = Recipe.objects.create(
            user=self.user,
            title='recipe1',
            time_minutes=23,
            price=23.33
        )
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='recipe2',
            time_minutes=24,
            price=23.03
        )
        recipe2.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
