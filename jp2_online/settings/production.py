# -*- coding: utf-8 -*-
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    '138.197.197.47',
    'junipero.erikiado.com',
    'basededatos.educacionintegral.org']

CORS_ORIGIN_WHITELIST = (
    '138.197.197.47',
    'junipero.erikiado.com',
    'basededatos.educacionintegral.org')

STATIC_ROOT = os.path.join(BASE_DIR, "../static/")