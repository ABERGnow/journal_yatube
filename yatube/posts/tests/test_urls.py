from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from mixer.backend.django import mixer

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )
        cls.group = mixer.blend(
            Group,
            slug=mixer.RANDOM,
            title=mixer.RANDOM,
            description=mixer.RANDOM,
        )
        cls.INDEX_URL = "/"
        cls.LOGIN_URL = f"/{cls.user}/login/?next=/create/"
        cls.PROFILE_URL = f"/profile/{cls.user}/"
        cls.NON_PAGE_URL = "/unexisting_page/"
        cls.POST_EDIT_URL = f"/posts/{cls.post.pk}/edit/"
        cls.GROUP_LIST_URL = f"/group/{cls.group.slug}/"
        cls.POST_DETAIL_URL = f"/posts/{cls.post.pk}/"
        cls.POST_CREATE_URL = "/create/"

    def setUp(self):
        self.anon = Client()
        self.auth = Client()
        self.auth.force_login(self.user)
        cache.clear()

    def test_access_url_for_all_users(self):
        """Страницы доступны всем пользователям."""
        url_names = [
            self.INDEX_URL,
            self.PROFILE_URL,
            self.GROUP_LIST_URL,
            self.POST_DETAIL_URL,
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.anon.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_accses_url_for_authorized_client(self):
        """Страницы доступны авторизованному пользователю."""
        response = self.auth.get(self.POST_CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_list_url_exists_at_desired_location(self):
        """Страница редактирования поста доступна автору."""
        response = self.auth.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin(self):
        """Страница создания поста перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.anon.get(self.POST_CREATE_URL, follow=True)
        self.assertRedirects(response, self.LOGIN_URL)

    def unexisting_page(self):
        """Несуществующая страница."""
        response = self.anon.get(self.NON_PAGE_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (self.INDEX_URL, "posts/index.html"),
            (self.PROFILE_URL, "posts/profile.html"),
            (self.POST_EDIT_URL, "posts/create_post.html"),
            (self.GROUP_LIST_URL, "posts/group_list.html"),
            (self.POST_DETAIL_URL, "posts/post_detail.html"),
            (self.POST_CREATE_URL, "posts/create_post.html"),
        )
        for url, template in templates_url_names:
            with self.subTest(template=template):
                response = self.auth.get(url)
                self.assertTemplateUsed(response, template)
