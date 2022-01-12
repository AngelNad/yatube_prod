from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.http import HttpResponseRedirect

from yatube.settings import PAGE_COUNT

from .forms import CommentForm, PostForm
from .models import Follow, Group, Like, Post, User


def get_page_obj(objects, page_number, items_on_list):
    return Paginator(objects, items_on_list).get_page(page_number)


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page_number = request.GET.get('page')
    page_obj = get_page_obj(post_list, page_number, PAGE_COUNT)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_number = request.GET.get('page')
    page_obj = get_page_obj(post_list, page_number, PAGE_COUNT)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = posts.count()
    page_number = request.GET.get('page')
    page_obj = get_page_obj(posts, page_number, PAGE_COUNT)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user,
                                  author=author).exists()
    )
    context = {
        'posts': posts,
        'post_count': post_count,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post_user = get_object_or_404(Post, pk=post_id)
    post_count = post_user.author.posts.count()
    form = CommentForm(request.POST or None)
    post_comments = post_user.comments.all()
    liking_post_user = (
        request.user.is_authenticated
        and Like.objects.filter(user=request.user, post=post_user).exists()
    )
    count_like_post = Like.objects.filter(post=post_user).count()
    count_post_comments = len(post_comments)
    context = {
        'post_user': post_user,
        'post_count': post_count,
        'form': form,
        'post_comments': post_comments,
        'count_post_comments': count_post_comments,
        'liking_post_user': liking_post_user,
        'count_like_post': count_like_post
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/create_post.html', {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:profile', username=post.author)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    page_obj = get_page_obj(post_list, page_number, PAGE_COUNT)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    if author == request.user:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    Like.objects.get_or_create(user=request.user, post=post)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def post_dislike(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    Like.objects.filter(user=request.user, post=post).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

