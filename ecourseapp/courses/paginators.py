from rest_framework.pagination import PageNumberPagination


class CoursePaginator(PageNumberPagination):
    page_size = 6

class CommentPaginator(PageNumberPagination):
    page_size = 2