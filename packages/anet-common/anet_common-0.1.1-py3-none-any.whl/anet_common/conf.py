from django.utils.translation import gettext_lazy as _

# 1. COMMON LANGUAGES
COMMON_LANGUAGES = (
    ("uz", "O'zbek"),
    ("ru", "Русский"),
    ("en", "English"),
)

COMMON_MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
COMMON_MODELTRANSLATION_DEFAULT_LANGUAGE = "uz"

# 2. COMMON REST FRAMEWORK SETTINGS
COMMON_REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        # Bizning custom renderer birinchi turishi kerak
        "anet_common.drf.renderers.AnetJSONRenderer", 
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "EXCEPTION_HANDLER": "anet_common.drf.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "anet_common.drf.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "anet_common.spectacular.schema.StandardAutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# 3. COMMON SPECTACULAR SETTINGS
COMMON_SPECTACULAR_SETTINGS = {
    "TITLE": "Anet Microservice API",
    "DESCRIPTION": "Standardized API for Anet System",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}
