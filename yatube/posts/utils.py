from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Page, Paginator
from django.db.models.query import QuerySet

NUMBER_OF_POSTS = 10


# Паджинанор
def pagination(request: WSGIRequest, posts_list: QuerySet) -> Page:
    """Функция для добавления паджинатора на страницу"""
    paginator: Paginator = Paginator(posts_list, NUMBER_OF_POSTS)
    page_number: str = request.GET.get('page')
    page_obj: Page = paginator.get_page(page_number)
    return page_obj


# кеширование постов на странице
def posts_cacher(posts_list, cache_name: str, cache_timer: int) -> QuerySet:
    """Функция для кеширования списка постов"""
    cached_posts_list = cache.get(cache_name)
    if not cached_posts_list:
        cached_posts_list = posts_list
        cache.set(cache_name, cached_posts_list, cache_timer)
    return cached_posts_list
