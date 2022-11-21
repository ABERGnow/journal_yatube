from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import page_list


def index(request):
    """Выводит шаблон главной страницы."""
    page_obj = page_list(Post.objects.select_related("author", "group"), request)
    context = {"page_obj": page_obj}
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """Выводит шаблон с группами постов."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = page_list(post_list, request)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    """Выводит шаблон профайла пользователя."""
    author = get_object_or_404(User, username=username)
    page_obj = page_list(author.posts.all(), request)
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    """Выводит шаблон информации поста."""
    post = get_object_or_404(Post.objects.select_related("author", "group"), pk=post_id)
    author_posts = post.author.posts.all().count()
    comments_form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        "post": post,
        "comments_form": comments_form,
        "comments": comments,
        "author_posts": author_posts,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    """Выводит шаблон создания поста."""
    if request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", post.author.username)
        return render(request, "posts/create_post.html", {"form": form})
    form = PostForm()
    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    """Выводит шаблон редактирования поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        if request.method == "POST":
            form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=post,
            )
            if form.is_valid():
                form.save()
                return redirect("posts:post_detail", post_id)
        form = PostForm(instance=post)
        return render(
            request,
            "posts/create_post.html",
            {
                "form": form,
                "post": post,
                "is_edit": True,
            },
        )
    return render("posts:post_detail", post_id)


@login_required
def add_comment(request, post_id):
    """Вывод шаблон добавления поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    page_obj = page_list(
        Post.objects.filter(author__following__user=request.user), request
    )
    context = {"page_obj": page_obj}
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    """Вывод шаблона подписки на автора"""
    author = get_object_or_404(User, username=username)
    if author != request.user and (
        not request.user.follower.filter(author=author).exists()
    ):
        Follow.objects.create(user=request.user, author=author)
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    """Вывод шаблона отписки от автора."""
    author = get_object_or_404(User, username=username)
    follower = request.user.follower.filter(author=author)
    if follower.exists():
        follower.delete()
    return redirect("posts:profile", author.username)
