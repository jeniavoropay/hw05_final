from django.core.paginator import Paginator

from django.conf import settings


def paginator(request, post_list):
    return Paginator(
        post_list,
        settings.POSTS_PER_PAGE
    ).get_page(
        request.GET.get('page')
    )
