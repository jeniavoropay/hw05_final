from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

TEST_SLUG = 'test_slug'
TEST_NAME = 'test_name'
POST_ID = 1
URL_ROUTES = (
    ('/', 'index', None),
    ('/create/', 'post_create', None),
    (f'/profile/{TEST_NAME}/', 'profile', (TEST_NAME,)),
    (f'/group/{TEST_SLUG}/', 'group_list', (TEST_SLUG,)),
    (f'/posts/{POST_ID}/', 'post_detail', (POST_ID,)),
    (f'/posts/{POST_ID}/edit/', 'post_edit', (POST_ID,)),
    (f'/posts/{POST_ID}/comment/', 'add_comment', (POST_ID,)),
    ('/follow/', 'follow_index', None),
    (f'/profile/{TEST_NAME}/follow/', 'profile_follow', (TEST_NAME,)),
    (f'/profile/{TEST_NAME}/unfollow/', 'profile_unfollow', (TEST_NAME,)),
)


class PostRoutesTest(TestCase):

    def test_urls_equal_routes(self):
        """Рассчитываемые маршруты дают ожидаемые явные url."""
        for url, route, args in URL_ROUTES:
            with self.subTest(url=url):
                self.assertEqual(
                    url, reverse(f'{app_name}:{route}', args=args))
