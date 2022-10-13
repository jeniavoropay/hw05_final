import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms


from ..models import Post, Group, User, Comment

TEST_SLUG = 'test_slug'
TEST_SLUG_2 = 'test_slug_2'
TEST_NAME = 'test_name'
INDEX = reverse('posts:index')
POST_CREATE = reverse('posts:post_create')
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
class PostFormsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_NAME)
        cls.group = Group.objects.create(
            slug=TEST_SLUG,
            title='Тестовая группа',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            slug=TEST_SLUG_2,
            title='Вторая тестовая группа',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_COMMENT = reverse('posts:add_comment', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Второй тестовый пост',
            'group': self.group.id,
            'image': TEST_IMAGE,
        }
        response = self.authorized_client.post(
            POST_CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Получить из базы все созданные посты
        objects_created = Post.objects.exclude(id=self.post.id)
        # Проверить что в этом наборе ОДИН пост.
        self.assertEqual(len(objects_created), 1)
        # У ЭТОГО поста проверить поля
        post = objects_created.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        # Спринт 6: При отправке поста с картинкой через PostForm
        # создаётся запись в базе данных
        self.assertEqual(post.image.name, f'posts/{form_data["image"].name}')
        self.assertEqual(post.author, self.user)

    def test_edit_post(self):
        """Валидная форма редактирует запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный пост',
            'group': self.group_2.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(Post.objects.count(), posts_count)
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.author, self.post.author)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post для создания и редактирования поста сформирован
        с правильным контекстом."""
        urls = [self.POST_EDIT, POST_CREATE]
        form_fields = {
            'text': forms.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                for value, expected in form_fields.items():
                    form_field = response.context['form'].fields.get(value)
                    self.assertIsInstance(form_field, expected)

    # Добавлено в Спринте 6
    def test_new_comment_display(self):
        """После успешной отправки комментарий появляется на странице поста."""
        сomments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            self.POST_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.count(),
            сomments_count + 1
        )
        self.assertRedirects(response, self.POST_DETAIL)
        self.assertEqual(len(response.context['comments']), 1)
        comment = response.context['comments'][0]
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.text, form_data['text'])
