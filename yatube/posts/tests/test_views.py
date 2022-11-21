import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from ..constants import TEN_POSTS, TEST_OF_POST, THREE_POSTS
from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create_user(username="auth")
        cls.group = mixer.blend(
            Group,
            slug=mixer.RANDOM,
            title=mixer.RANDOM,
            description=mixer.RANDOM,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Текст",
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.anon = Client()
        self.auth = Client()
        self.auth.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_detail", args=({self.post.pk})
            ): "posts/post_detail.html",
            reverse(
                "posts:group_list", args=({self.group.slug})
            ): "posts/group_list.html",
            reverse("posts:profile", args=({self.post.author})): "posts/profile.html",
            reverse("posts:post_edit", args=({self.post.pk})): "posts/create_post.html",
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.anon.get(reverse("posts:index"))
        post_object = response.context["page_obj"][0]
        post_text = post_object.text
        post_image = post_object.image
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_index_page_cached(self):
        """Проверка кеширования шаблона index."""
        response = self.auth.get(reverse("posts:index"))
        Post.objects.all().delete()
        response1 = self.auth.get(reverse("posts:index"))
        self.assertEqual(response.content, response1.content)
        cache.clear()
        Post.objects.create(author=self.user, text="Тестовый пост")
        response2 = self.auth.get(reverse("posts:index"))
        self.assertNotEqual(response1.content, response2.content)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile/ сформирован с правильным контекстом."""
        response = self.auth.get(reverse("posts:profile", args=({self.user})))
        first_object = response.context["page_obj"][0]
        post_author = first_object.author
        post_image = first_object.image
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth.get(reverse("posts:post_detail", args=({self.post.pk})))
        post_text = {
            response.context["post"].text: self.post.text,
            response.context["post"].group: self.group,
            response.context["post"].author: self.user,
            response.context["post"].image: self.post.image,
        }
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth.get(reverse("posts:group_list", args=({self.group.slug})))
        first_object = response.context["page_obj"][0]
        post_group = first_object.group.title
        post_image = first_object.image
        self.assertEqual(post_group, self.group.title)
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.auth.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth.get(reverse("posts:post_edit", args=({self.post.pk})))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correct_added_post_pages(self):
        """Проверка отображение поста на страницах:
        index, group_list, profile.
        """
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse("posts:group_list", args=({self.group.slug})): Post.objects.get(
                group=self.post.group
            ),
            reverse("posts:profile", args=({self.post.author})): Post.objects.get(
                group=self.post.group
            ),
        }
        for value, expacted in form_fields.items():
            with self.subTest(value=value):
                response = self.auth.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expacted, form_field)

    def test_post_have_correct_group(self):
        """Проверка принадлежности поста к своей группе."""
        form_fields = {
            reverse("posts:group_list", args=({self.group.slug})): Post.objects.exclude(
                group=self.post.group
            ),
        }
        for value, expacted in form_fields.items():
            with self.subTest(value=value):
                response = self.auth.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expacted, form_field)


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.anon = Client()
        self.user = User.objects.create(username="auth")
        self.auth = Client()
        self.auth.force_login(self.user)
        self.group = Group.objects.create(
            slug="test-slug", title="Заголовок", description="Описание группы"
        )
        cache.clear()
        bulk_post: list = []
        for i in range(TEST_OF_POST):
            bulk_post.append(
                Post(text=f"Тестовый пост {i}", group=self.group, author=self.user)
            )
        Post.objects.bulk_create(bulk_post)

    def test_index_first_page_contains_ten_records(self):
        response = self.auth.get(reverse("posts:index"))
        self.assertEqual(len(response.context["page_obj"]), TEN_POSTS)

    def test_index_second_page_contains_three_records(self):
        response = self.auth.get(reverse("posts:index") + "?page=2")
        self.assertEqual(len(response.context["page_obj"]), THREE_POSTS)

    def test_group_post_first_page_contains_ten_records(self):
        response = self.auth.get(reverse("posts:group_list", args=({self.group.slug})))
        self.assertEqual(len(response.context["page_obj"]), TEN_POSTS)

    def test_group_post_second_page_contains_three_records(self):
        response = self.auth.get(
            reverse("posts:group_list", args=({self.group.slug})) + "?page=2",
        )
        self.assertEqual(len(response.context["page_obj"]), THREE_POSTS)

    def test_profile_first_page_contains_ten_records(self):
        response = self.auth.get(reverse("posts:profile", args=({self.user})))
        self.assertEqual(len(response.context["page_obj"]), TEN_POSTS)

    def test_profile_second_page_contains_three_records(self):
        response = self.auth.get(
            reverse("posts:profile", args=({self.user})) + "?page=2",
        )
        self.assertEqual(len(response.context["page_obj"]), THREE_POSTS)


class FollowTests(TestCase):
    def setUp(self):
        self.auth_follower = Client()
        self.auth_following = Client()
        self.follower = User.objects.create_user(username="follower")
        self.following = User.objects.create_user(username="following")
        self.post = Post.objects.create(author=self.following, text="Тестовая запись")
        self.auth_follower.force_login(self.follower)
        self.auth_following.force_login(self.following)

    def test_follow(self):
        """Авторизованный пользователь может
        подписываться.
        """
        self.auth_follower.get(
            reverse("posts:profile_follow", args=({self.following.username}))
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Авторизованный пользователь может
        отменить подписку.
        """
        self.auth_follower.get(
            reverse("posts:profile_follow", args=({self.following.username}))
        )
        self.auth_follower.get(
            reverse("posts:profile_unfollow", args=({self.following.username}))
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription(self):
        """Пост появляется в ленте подписчиков."""
        Follow.objects.create(user=self.follower, author=self.following)
        response = self.auth_follower.get(reverse("posts:follow_index"))
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, "Тестовая запись")
        response = self.auth_following.get(reverse("posts:follow_index"))
        self.assertNotContains(response, "Тестовая запись")
