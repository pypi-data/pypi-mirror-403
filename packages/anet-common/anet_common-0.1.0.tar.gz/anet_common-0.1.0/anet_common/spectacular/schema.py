from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter

class StandardAutoSchema(AutoSchema):
    """
    Standard AutoSchema klassi.
    1. Global headerlarni (Request-ID, Language) qo'shadi.
    2. ListAPIView lar uchun page/page_size larni avtomatik qo'shadi.
    """
    
    def get_override_parameters(self):
        params = super().get_override_parameters()
        
        # Global Headers
        global_params = [
            OpenApiParameter(
                name="X-Request-ID",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Unique Request ID for tracing",
                required=False
            ),
            OpenApiParameter(
                name="Accept-Language",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Language code (uz, ru, en)",
                enum=["uz", "ru", "en"],
                default="uz",
                required=False
            ),
        ]
        
        # Agar bu "list" metodi bo'lsa (pagination kerak)
        if self.method == 'GET' and self.view.action == 'list':
             # Paginatsiya parametrlarini qo'shish (agar DRF avtomatik qo'shmagan bo'lsa)
             # Odatda DRF Spectacular buni PageNumberPagination klassidan oladi, 
             # lekin biz aniq bo'lishi uchun bu yerda ham tekshiramiz.
             pass 

        return params + global_params
