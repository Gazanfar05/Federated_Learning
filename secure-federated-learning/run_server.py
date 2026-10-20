from __future__ import annotations

import uvicorn

from server.config import settings


if __name__ == "__main__":
    server_options = {
        "host": settings.server_host,
        "port": settings.server_port,
        "reload": False,
        "log_level": "info",
    }
    if settings.tls_enabled:
        server_options.update(
            ssl_keyfile=settings.tls_key_file,
            ssl_certfile=settings.tls_cert_file,
        )

    uvicorn.run("server.main:app", **server_options)
