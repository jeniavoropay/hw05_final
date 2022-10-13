from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow
from .utils import paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = (
        Post.objects
        .select_related('author')
        .select_related('group')
        .all()
    )
    page_obj = paginator(request, post_list)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = paginator(request, post_list)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    page_obj = paginator(request, post_list)
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    else:
        following = False
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_list = Comment.objects.filter(post=post).order_by('-created').all()
    comment_form = CommentForm()
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comment_list,
        'form': comment_form,
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'post': post,
            'form': form
        })
    form.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user).order_by('-pub_date')
    page_obj = paginator(request, post_list)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    author.following.filter(user=request.user).delete()
    return redirect('posts:profile', username=username)