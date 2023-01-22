from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import pagination, posts_cacher

CACHE_SEC_FOR_POSTS = 20


def index(request):
    posts_list = Post.objects.select_related('group', 'author')
    # Кеширование
    index_posts_cache = posts_cacher(
        posts_list,
        'index_posts_cache',
        CACHE_SEC_FOR_POSTS,
    )

    page_obj = pagination(request, index_posts_cache)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    # кеширование постов подписок (если оставить не проходит тест)
    # follow_posts_cache = posts_cacher(
    #     posts_list,
    #     'follow_posts_cache',
    #     CACHE_SEC_FOR_POSTS,
    # )
    page_obj = pagination(request, posts_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User.objects.all(), username=username)
    if request.user != author:
        Follow.objects.update_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User.objects.all(), username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', author)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('group')
    page_obj = pagination(request, posts_list)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.select_related('author')
    page_obj = pagination(request, posts_list)
    show_follow = False
    following = False
    if request.user == author or request.user.is_anonymous:
        show_follow = True
    else:
        following = Follow.objects.filter(user=request.user, author=author)

    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'show_follow': show_follow,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.select_related('post')
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if request.method != 'POST':
        return render(request, 'posts/create_post.html', {'form': form})
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    is_edit = True
    context = {
        'is_edit': is_edit,
        'form': form
    }

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST' and form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
