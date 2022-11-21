import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            text="Текст поста",
            group=cls.group,
            author=cls.user,
            image=cls.uploaded
        )
        cls.comment = mixer.blend(
            Comment,
            text=mixer.RANDOM,
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

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        response = self.auth.post(
            reverse("posts:post_create"),
            data={
                "text": self.post.text,
                "group": self.group.id,
                "image": self.post.image,
            },
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.id,
                image=self.post.image,
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        response = self.auth.post(
            reverse("posts:post_edit", args=({self.post.pk})),
            data={"text": self.post.text, "group": self.group.pk},
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", args=({self.post.pk}))
        )
        self.assertEqual(Post.objects.count(), 2)
        first_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.group.pk, self.group.pk)
        self.assertEqual(first_post.author.pk, self.user.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_create_guest_client(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        posts_count = Post.objects.count()
        form_data = {"text": self.post.text, "group": self.group.pk}
        response = self.anon.post(
            reverse("posts:post_edit", args=({self.post.pk})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, f"/auth/login/?next=/posts/{self.post.pk}/edit/")
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text="Изменяем текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_post(self):
        """Валидная форма создает коммент в Post."""
        form_data = {
            "text": self.comment.text,
            "author": self.comment.author,
        }
        response = self.auth.post(
            reverse("posts:post_detail", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertTrue(Comment.objects.filter(text=self.comment.text).exists())
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.author, form_data["author"])
        self.assertEqual(response.status_code, HTTPStatus.OK)
