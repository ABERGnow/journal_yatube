from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель, для создания группы сообщества."""

    title = models.CharField("title", max_length=200)
    slug = models.SlugField("slug", unique=True)
    description = models.TextField("description")

    def __str__(self):
        return self.title


class Post(CreatedModel):
    """Модель для хранения постов."""

    text = models.TextField(
        verbose_name="Текст поста",
        help_text="Введите текст поста",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="posts/",
        blank=True,
    )

    class Meta:
        """Внутренний класс, для изменения поведения полей модели."""

        ordering = ("-pub_date",)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        """Выводит поле text, при печати объекта модели Post."""
        return self.text[:15]


class Comment(CreatedModel):
    """Модель для хранения комментариев."""

    post = models.ForeignKey(
        Post,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор",
    )
    text = models.TextField(
        "Текст комментария",
        help_text="Введите текс комментария",
    )

    class Meta:
        """Внутренний класс, для изменения поведения полей модели."""

        ordering = ('-pub_date',)
        verbose_name = "Коментарий"
        verbose_name_plural = "Коментарии"

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    """Модель подписки на автора поста."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )
