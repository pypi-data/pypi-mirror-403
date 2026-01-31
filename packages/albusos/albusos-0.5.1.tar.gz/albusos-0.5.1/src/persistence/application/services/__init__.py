"""persistence.application

Studio application/service layer (host-facing orchestration).

Transport layers (`albus`) should call `persistence.application.service.StudioDomainService`
and translate domain errors into HTTP/WS/JSON-RPC responses.
"""

from __future__ import annotations

__all__: list[str] = []
