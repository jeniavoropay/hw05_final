from http import HTTPStatus

from django.contrib.auth import get_user
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Group, Post

TEST_SLUG = 'test_slug'
TEST_NAME = 'test_name'
TEST_NAME_2 = 'test_name_2'
INDEX = reverse('posts:index')
FOLLOW = reverse('posts:follow_index')
FOLLOW_USER = reverse('posts:profile_follow', args=[TEST_NAME])
UNFOLLOW_USER = reverse('posts:profile_unfollow', args=[TEST_NAME])
POST_CREATE = reverse('posts:post_create')
GROUP_LIST = reverse('posts:group_list', args=[TEST_SLUG])
PROFILE = reverse('posts:profile', args=[TEST_NAME])
LOGIN = reverse('users:login')
NEXT = '?next='
REDIRECT_LOGIN_POST_CREATE = f'{LOGIN}{NEXT}{POST_CREATE}'
REDIRECT_LOGIN_FOLLOW = f'{LOGIN}{NEXT}{FOLLOW_USER}'
REDIRECT_LOGIN_UNFOLLOW = f'{LOGIN}{NEXT}{UNFOLLOW_USER}'
REDIRECT_LOGIN_FOLLOW_INDEX = f'{LOGIN}{NEXT}{FOLLOW}'
UNEXISTING_PAGE = '/unexisting_page/'
OK = HTTPStatus.OK
REDIRECT = HTTPStatus.FOUND
NOT_FOUND = HTTPStatus.NOT_FOUND


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_NAME)
        cls.user_2 = User.objects.create_user(username=TEST_NAME_2)
        cls.group = Group.objects.create(
            slug=TEST_SLUG,
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.REDIRECT_LOGIN_POST_EDIT = f'{LOGIN}{NEXT}{cls.POST_EDIT}'
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another_author = Client()
        cls.another_author.force_login(cls.user_2)

    def test_urls_at_desired_location(self):
        """Проверяется доступность страниц для пользователя с разными
        правами доступа."""
        pages_response = [
            [INDEX, self.client, OK],
            [GROUP_LIST, self.client, OK],
            [PROFILE, self.client, OK],
            [self.POST_DETAIL, self.client, OK],
            [self.POST_EDIT, self.client, REDIRECT],
            [POST_CREATE, self.client, REDIRECT],
            [UNEXISTING_PAGE, self.client, NOT_FOUND],
            [self.POST_EDIT, self.author, OK],
            [POST_CREATE, self.author, OK],
            [self.POST_EDIT, self.another_author, REDIRECT],
            [FOLLOW, self.client, REDIRECT],
            [FOLLOW, self.author, OK],
            [FOLLOW_USER, self.client, REDIRECT],
            [FOLLOW_USER, self.another_author, REDIRECT],
            [FOLLOW_USER, self.author, REDIRECT],
            [UNFOLLOW_USER, self.client, REDIRECT],
            [UNFOLLOW_USER, self.another_author, REDIRECT],
            [UNFOLLOW_USER, self.author, NOT_FOUND],
        ]
        for url, client, http in pages_response:
            with self.subTest(url=url, client=get_user(client).username):
                self.assertEqual(client.get(url).status_code, http)

    def test_anonymous_is_redirected_to_page(self):
        """Перенаправление пользователей с разными правамии доступа."""
        pages_redirect = [
            [POST_CREATE, self.client, REDIRECT_LOGIN_POST_CREATE],
            [self.POST_EDIT, self.client, self.REDIRECT_LOGIN_POST_EDIT],
            [self.POST_EDIT, self.another_author, self.POST_DETAIL],
            [FOLLOW_USER, self.client, REDIRECT_LOGIN_FOLLOW],
            [UNFOLLOW_USER, self.client, REDIRECT_LOGIN_UNFOLLOW],
            [FOLLOW, self.client, REDIRECT_LOGIN_FOLLOW_INDEX],
            [FOLLOW_USER, self.another_author, PROFILE],
            [UNFOLLOW_USER, self.another_author, PROFILE],
            [FOLLOW_USER, self.author, PROFILE],
        ]
        for url, client, redirect in pages_redirect:
            with self.subTest(url=url, client=get_user(client).username):
                self.assertRedirects(client.get(url), redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = {
            INDEX: 'posts/index.html',
            GROUP_LIST: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_EDIT: 'posts/create_post.html',
            POST_CREATE: 'posts/create_post.html',
            FOLLOW: 'posts/follow.html',
            UNEXISTING_PAGE: 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address),
                    template)
