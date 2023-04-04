from django.core.paginator import Paginator
from posts.constants import TEN_POSTS


def page_list(queryset, request):
    """Функция создания нумерации страниц"""
    paginator = Paginator(queryset, TEN_POSTS)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
