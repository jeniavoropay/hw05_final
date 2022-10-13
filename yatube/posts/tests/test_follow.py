from django.test import TestCase, Client
from django.urls import reverse

from ..models import User, Post, Follow

TEST_NAME = 'test_name'
TEST_SUB_NAME = 'test_subscriber'
FOLLOW = reverse('posts:follow_index')
FOLLOW_USER = reverse('posts:profile_follow', args=[TEST_NAME])
UNFOLLOW_USER = reverse('posts:profile_unfollow', args=[TEST_NAME])
PROFILE = reverse('posts:profile', args=[TEST_NAME])


class PostFollowTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=TEST_NAME)
        cls.subscriber = User.objects.create_user(username=TEST_SUB_NAME)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_subscriber = Client()
        self.authorized_user.force_login(self.user)
        self.authorized_subscriber.force_login(self.subscriber)

    def test_post_for_follower_display(self):
        """Запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        self.authorized_subscriber.get(FOLLOW_USER)
        response = self.authorized_subscriber.get(FOLLOW)
        self.assertIn(self.post, response.context['page_obj'])
        self.authorized_subscriber.get(UNFOLLOW_USER)
        response = self.authorized_subscriber.get(FOLLOW)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_user_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        follow_count = Follow.objects.count()
        response = self.authorized_subscriber.get(FOLLOW_USER)
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.subscriber,
                author=self.user
            ).exists()
        )
        response = self.authorized_subscriber.get(UNFOLLOW_USER)
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.subscriber,
                author=self.user
            ).exists()
        )
