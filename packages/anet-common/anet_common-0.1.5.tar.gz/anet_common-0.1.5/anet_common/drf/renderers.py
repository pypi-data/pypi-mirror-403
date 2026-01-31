import datetime
from rest_framework.renderers import JSONRenderer
from rest_framework.status import is_success
from django.utils import timezone
from django.utils.translation import get_language
from anet_common.middleware import get_current_request_id
from django.conf import settings

class AnetJSONRenderer(JSONRenderer):
    """
    Barcha muvaffaqiyatli javoblarni standart formatga o'tkazuvchi Renderer.
    Format:
    {
      "success": true,
      "status_code": 200,
      "data": ...,
      "errors": [],
      "meta": { ... }
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None

        # Agar bu error response bo'lsa (exception handler allaqachon formatlagan),
        # biz uni o'zgartirmaymiz, shunchaki JSON ga o'giramiz.
        # Exception handler o'zi "success": False formatini qaytaradi.
        if response and not is_success(response.status_code):
            return super().render(data, accepted_media_type, renderer_context)

        # Agar data None bo'lsa
        if data is None:
            data = {}

        # Paginatsiya ma'lumotlarini ajratib olish
        pagination_meta = {}
        if isinstance(data, dict) and 'results' in data and 'meta_pagination' in data:
            # Pagination class bizga results va meta_pagination qaytargan deb hisoblaymiz
            results_data = data['results']
            pagination_meta = data['meta_pagination']
        else:
            results_data = data

        # Meta ma'lumotlarni shakllantirish
        meta_data = {
            "request_id": get_current_request_id(),
            "timestamp": timezone.now().isoformat(),
            "service": getattr(settings, "SERVICE_NAME", "unknown-service"),
            "version": getattr(settings, "SERVICE_VERSION", "v1"),
            "language": get_language(),
        }

        # Agar paginatsiya mavjud bo'lsa, uni meta ga qo'shamiz
        if pagination_meta:
            meta_data["pagination"] = pagination_meta

        # Yakuniy response strukturasi
        status_code = response.status_code if response else 200
        final_response = {
            "success": True,
            "status_code": status_code,
            "data": results_data,
            "errors": [],
            "meta": meta_data
        }

        return super().render(final_response, accepted_media_type, renderer_context)
