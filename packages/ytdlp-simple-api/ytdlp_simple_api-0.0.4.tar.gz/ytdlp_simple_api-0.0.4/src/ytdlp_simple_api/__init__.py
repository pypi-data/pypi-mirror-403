from uvicorn import run

from ytdlp_simple_api.api import app
from ytdlp_simple_api.config import PORT


def serve():
    run(app, host='0.0.0.0', port=PORT)


__all__ = ['serve']

if __name__ == '__main__':
    serve()
