import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import User, Group, Post

TEST_SLUG = 'test_slug'
TEST_SLUG_2 = 'test_slug_2'
TEST_NAME = 'test_name'
INDEX = reverse('posts:index')
GROUP_LIST = reverse('posts:group_list', args=[TEST_SLUG])
GROUP_LIST_2 = reverse('posts:group_list', args=[TEST_SLUG_2])
PROFILE = reverse('posts:profile', args=[TEST_NAME])
TEST_IMAGE = SimpleUploadedFile(
    name='test_pic.png',
    content=(
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    ),
    content_type='image/png',
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_NAME)
        cls.group = Group.objects.create(
            slug=TEST_SLUG,
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            slug=TEST_SLUG_2,
            title='Вторая тестовая группа',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=TEST_IMAGE
        )
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile, post_detail сформированы
        с правильным контекстом."""
        urls = (
            (INDEX, 'page_obj'),
            (GROUP_LIST, 'page_obj'),
            (PROFILE, 'page_obj'),
            (self.POST_DETAIL, 'post'),
        )
        for url, obj in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if obj == 'page_obj':
                    # Корректно брать первый можно не всегда.
                    # Добавьте проверку его "единственности" в наборе.
                    self.assertEqual(len(response.context[obj]), 1)
                    post = response.context[obj][0]
                elif obj == 'post':
                    post = response.context[obj]
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                # Спринт 6: При выводе поста с картинкой изображение передаётся
                # в словаре context на 4 страницы из теста
                self.assertEqual(post.image, self.post.image)

    def test_post_another_group_display(self):
        """Пост не появялется в group_list, для которого
        не предназначен."""
        response = self.client.get(GROUP_LIST_2)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_author_profile_display(self):
        """Автор появляется в контексте профиля."""
        response = self.authorized_client.get(PROFILE)
        author = response.context['author']
        self.assertEqual(author, self.user)

    def test_group_group_list_display(self):
        """Группа появляется в контексте групп-ленты
        без искажения атрибутов."""
        response = self.authorized_client.get(GROUP_LIST)
        group = response.context['group']
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.id, self.group.id)

    def test_pages_contain_num_posts(self):
        """Ленты с постами содержат правильное число постов
        на страницах."""
        self.posts = Post.objects.bulk_create(
            Post(
                author=self.user,
                group=self.group,
                text=f'Тестовый пост {i}',
            )
            for i in range(settings.POSTS_PER_PAGE)
        )
        pages = [
            [INDEX, settings.POSTS_PER_PAGE],
            [GROUP_LIST, settings.POSTS_PER_PAGE],
            [PROFILE, settings.POSTS_PER_PAGE],
            [f'{INDEX}?page=2', 1],
            [f'{GROUP_LIST}?page=2', 1],
            [f'{PROFILE}?page=2', 1],
        ]
        for page, num_posts in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(len(response.context['page_obj']), num_posts)

    def test_cache_index_page(self):
        """При удалении поста он останется в response.content /index/,
        пока не отчистить кэш принудительно."""
        self.post_2 = Post.objects.create(
            author=self.user,
            text='Еще один тестовый пост',
        )
        response_1 = self.authorized_client.get(INDEX)
        self.assertIn(self.post_2, response_1.context['page_obj'])
        self.post_2.delete()
        response_2 = self.authorized_client.get(INDEX)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(INDEX)
        self.assertNotEqual(response_1.content, response_3.content)
