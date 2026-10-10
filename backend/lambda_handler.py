"""Lambda entry point for Function URLs and API Gateway HTTP API events.

Lifespan stays enabled: each invocation validates the packaged scientific
repository through the existing FastAPI startup path. No server is started.
"""
from mangum import Mangum
from .main import app

handler = Mangum(app, lifespan='on')
