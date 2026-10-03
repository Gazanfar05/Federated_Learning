from __future__ import annotations

import uvicorn

from server.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
        ssl_keyfile=settings.tls_key_file,
        ssl_certfile=settings.tls_cert_file,
        log_level="info",
    )
