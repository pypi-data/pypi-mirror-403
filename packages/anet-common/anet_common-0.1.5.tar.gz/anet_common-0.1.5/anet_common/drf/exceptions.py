import logging
import json
import os
from pathlib import Path

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, APIException

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language
from anet_common.middleware import get_current_request_id

logger = logging.getLogger(__name__)

# Load error catalog
try:
    current_dir = Path(__file__).resolve().parent.parent
    with open(os.path.join(current_dir, 'errors.json'), 'r', encoding='utf-8') as f:
        ERROR_CATALOG = json.load(f)
except Exception as e:
    logger.error(f"Failed to load errors.json: {e}")
    ERROR_CATALOG = {}


def _get_catalog_error(key, lang):
    """Katalogdan xatolikni oladi"""
    error_obj = ERROR_CATALOG.get(key, ERROR_CATALOG.get("SERVER_ERROR"))
    if not error_obj:
        return "UNKNOWN", "Unknown Error"
    
    code = error_obj.get("code")
    message = error_obj.get("message", {}).get(lang, error_obj.get("message", {}).get("en", "Error"))
    return code, message


def _determine_source(request, status_code, field_name=None):
    """
    Xatolik manbasini aniqlaydi.
    """
    if status_code == 404:
        return "path"
    if status_code in (401, 403):
        return "header"
    
    if status_code == 400:
        # Agar GET metodi bo'lsa, xatolik query parametrlarda bo'lishi ehtimoli yuqori
        if request.method == "GET":
            return "query"
        # POST/PUT/PATCH da body da bo'ladi
        return "body"
    
    return None


def _flatten_errors(errors, parent_key=None):
    """
    DRF ning ichma-ich (nested) xatolarini tekis ro'yxatga aylantiradi.
    """
    flat_errors = []
    
    if isinstance(errors, list):
        for err in errors:
            flat_errors.extend(_flatten_errors(err, parent_key))
    elif isinstance(errors, dict):
        for key, value in errors.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            flat_errors.extend(_flatten_errors(value, new_key))
    else:
        # Bu yerda string keladi
        flat_errors.append({
            "field": parent_key or "non_field_errors",
            "detail_message": str(errors)
        })
        
    return flat_errors


def custom_exception_handler(exc, context):
    """
    Global exception handler.
    """
    # Call DRF's default handler
    response = exception_handler(exc, context)
    request = context.get('request')
    lang = get_language()

    # Agar kutilmagan xato (500) bo'lsa
    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        code, msg = _get_catalog_error("SERVER_ERROR", lang)
        
        data = {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "data": None,
            "errors": [{
                "code": code,
                "message": msg,
                "detail_message": str(exc) if settings.DEBUG else "Internal Server Error",
                "field": None,
                "source": None,
                "details": None
            }],
            "meta": {
                "request_id": get_current_request_id(),
                "timestamp": timezone.now().isoformat(),
                "service": getattr(settings, "SERVICE_NAME", "unknown"),
                "version": getattr(settings, "SERVICE_VERSION", "v1"),
                "language": lang
            }
        }
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # DRF tutgan xatolarni formatlash
    flat_error_list = []
    
    # Asosiy xatolik turini aniqlash (Katalogdan olish uchun)
    catalog_key = "SERVER_ERROR"
    if response.status_code == 404:
        catalog_key = "NOT_FOUND"
    elif response.status_code == 401:
        catalog_key = "UNAUTHORIZED"
    elif response.status_code == 403:
        catalog_key = "FORBIDDEN"
    elif response.status_code == 400:
        catalog_key = "VALIDATION_ERROR"

    code, catalog_message = _get_catalog_error(catalog_key, lang)
    
    # Custom Exceptionlardan qo'shimcha details ni olish
    extra_details = getattr(exc, 'extra_details', None)
    if not extra_details:
        extra_details = getattr(exc, 'details', None)
        # DRF ning o'zi detail deb string qaytaradi, uni olmasligimiz kerak
        if isinstance(extra_details, str): 
            extra_details = None

    # Agar response.data ro'yxat yoki lug'at bo'lsa, uni flatten qilamiz
    raw_errors = _flatten_errors(response.data)
    
    formatted_errors = []
    for item in raw_errors:
        # Xatolik manbasini aniqlash
        error_source = _determine_source(request, response.status_code, item['field'])
        
        formatted_errors.append({
            "code": code, 
            "message": catalog_message,
            "detail_message": item['detail_message'],
            "field": item['field'],
            "source": error_source,
            "details": extra_details # Agar mavjud bo'lsa
        })
    
    # Agar hech qanday detail bo'lmasa
    if not formatted_errors and response.status_code >= 400:
        formatted_errors.append({
            "code": code,
            "message": catalog_message,
            "detail_message": catalog_message,
            "field": None,
            "source": _determine_source(request, response.status_code),
            "details": extra_details
        })

    response.data = {
        "success": False,
        "status_code": response.status_code,
        "data": None,
        "errors": formatted_errors,
        "meta": {
            "request_id": get_current_request_id(),
            "timestamp": timezone.now().isoformat(),
            "service": getattr(settings, "SERVICE_NAME", "unknown"),
            "version": getattr(settings, "SERVICE_VERSION", "v1"),
            "language": lang
        }
    }

    return response
