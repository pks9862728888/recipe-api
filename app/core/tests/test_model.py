from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email="test@gmail.com", password="testpass"):
    """Create a sample user"""
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Testing whether new user creation with email is successful"""
        # Custom data to input in model
        email = 'test@londonappdev.com'
        password = 'Password123'

        # Putting data in model
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        # Testing email and password
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_superuser_with_email_successful(self):
        """Checks whether superuser creation with email is successful"""
        email = "abc@gmail.com"
        password = "Dilbar@123"

        user = get_user_model().objects.create_superuser(email=email,
                                                         password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_email_normalized(self):
        """Testing whether email is normalized or not"""
        email = "test@XYZ.com"
        user = get_user_model().objects.create_user(email=email,
                                                    password='tesT@123')

        self.assertEqual(user.email, email.lower())

    def test_whether_empty_email_raises_value_error(self):
        """Testing that empty email raises ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'Pass123@')

    def test_tag_str(self):
        """Tests the tag string representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name="TestName"
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Tests the Ingredient string representation"""
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name="Cucumber"
        )

        self.assertEquals(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Tests the Recipe string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title="Test recipe",
            time_minutes=5,
            price=10.50
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        test_uuid = 'test-uuid'
        mock_uuid.return_value = test_uuid
        file_path = models.get_recipe_image_file_path(None, 'filename.jpg')

        ext_path = f'uploads/recipe/{test_uuid}.jpg'

        self.assertEquals(file_path, ext_path)
