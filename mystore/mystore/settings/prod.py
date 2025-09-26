from .base import *
import os
import dj_database_url

DEBUG = False


STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


DATABASES = {
    'default': dj_database_url.parse(
        env('DATABASE_URL'),
        conn_max_age=600,  
        ssl_require=True                             
    )
}


DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL' : env('CLOUDINARY_URL')
}

ALLOWED_HOSTS = [
    "toro-mr5z.onrender.com",
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = [
    "https://toro-mr5z.onrender.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://toro-mr5z.onrender.com",
]


# ALLOWED_HOSTS = [
#     "13.127.207.111",
#     "0.0.0.0",
#     "13.127.207.111",
# ]

# CSRF_TRUSTED_ORIGINS = [
#     "https://13.127.207.111",
#     "http://13.127.207.111",
#     "https://summershein.muhamedpr.shop",
#     "https://www.summershein.muhamedpr.shop",
# ]

# CORS_ALLOWED_ORIGINS = [
#     "https://13.127.207.111",
#     "http://13.127.207.111",
#     "https://summershein.muhamedpr.shop",
#     "https://www.summershein.muhamedpr.shop",
# ]



