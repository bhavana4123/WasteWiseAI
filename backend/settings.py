"""Deployment configuration, independent of scientific parameters."""
import os
from urllib.parse import urlsplit


def runtime_port():
    try:
        port = int(os.getenv('PORT', '8080'))
    except ValueError:
        raise ValueError('PORT must be an integer between 1 and 65535') from None
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be an integer between 1 and 65535')
    return port


def cors_origins():
    default = '' if os.getenv('WASTEWISE_ENV', '').lower() == 'production' else (
        'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173')
    origins = []
    for value in os.getenv('WASTEWISE_CORS_ORIGINS', default).split(','):
        origin = value.strip()
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or '*' in origin or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment):
            raise ValueError('WASTEWISE_CORS_ORIGINS must contain explicit HTTP(S) origins without paths or wildcards')
        try:
            parsed.port
        except ValueError:
            raise ValueError('Invalid port in WASTEWISE_CORS_ORIGINS') from None
        if origin not in origins:
            origins.append(origin)
    return origins
