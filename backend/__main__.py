"""Production entry point: python -m backend."""
import uvicorn
from .settings import runtime_port


def main():
    uvicorn.run('backend.main:app', host='0.0.0.0', port=runtime_port())


if __name__ == '__main__':
    main()
