from django.test import TestCase
from django.core.cache import cache
from mixer.backend.django import mixer

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = mixer.blend(
            Group,
            slug=mixer.RANDOM,
            title=mixer.RANDOM,
            description=mixer.RANDOM,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст поста",
            group=cls.group,
        )
        cls.FIELD_VERBOSES = (
            ("author", "Автор"),
            ("text", "Текст поста"),
            ("group", "Группа"),
            ("pub_date", "Дата публикации"),
        )
        cls.HELP_TEXT_FIELDS = (
            ("text", "Введите текст поста"),
            ("group", "Группа, к которой будет относиться пост"),
        )

    def test_model_post_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        self.assertEqual(post.text[:15], str(post))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        for field, expected_value in self.FIELD_VERBOSES:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        for field, expected_value in self.HELP_TEXT_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value,
                )


class GroupModelTest(TestCase):
    def setUp(self):
        self.group = mixer.blend(
            Group,
            slug=mixer.RANDOM,
            title=mixer.RANDOM,
            description=mixer.RANDOM,
        )
        cache.clear()

    def test_model_group_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        self.assertEqual(group.title, str(group))
