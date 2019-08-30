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
