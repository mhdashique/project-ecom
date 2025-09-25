from .base import *
import os
import dj_database_url



DEBUG = False


STATIC_ROOT = os.path.join(BASE_DIR, "static/")


DATABASES = {
    'default': dj_database_url.parse(
        env('DATABASE_URL'),
        conn_max_age=600,  
        ssl_require=True                             
    )
}

ALLOWED_HOSTS = [
    "your-app-name.onrender.com",   # Render domain
    "127.0.0.1",                    # Local dev
    "localhost",                    # Local dev
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-app-name.onrender.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://your-app-name.onrender.com",
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



