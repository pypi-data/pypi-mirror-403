from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPageNumberPagination(PageNumberPagination):
    """
    Custom pagination that passes pagination metadata separately
    so the Renderer can move it into the 'meta' field.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        # Biz bu yerda standart Response qaytaramiz, lekin
        # Renderer tushunishi uchun structureni maxsus qilamiz.
        return Response({
            'results': data,
            'meta_pagination': {
                'page': self.page.number,
                'page_size': self.page.paginator.per_page,
                'total_items': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_prev': self.page.has_previous(),
            }
        })
