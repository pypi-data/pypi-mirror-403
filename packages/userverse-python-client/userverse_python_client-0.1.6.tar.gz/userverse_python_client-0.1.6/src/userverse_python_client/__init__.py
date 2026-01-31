"""userverse_python_client public API."""

from typing import TYPE_CHECKING, Any

from .clients.user import UverseUserClient

if TYPE_CHECKING:  # pragma: no cover
    from .clients.company import UverseCompanyClient

__all__ = ["UverseUserClient", "UverseCompanyClient"]


def __getattr__(name: str) -> Any:
    if name == "UverseCompanyClient":
        from .clients.company import UverseCompanyClient as _CompanyClient

        return _CompanyClient
    raise AttributeError(f"module 'userverse_python_client' has no attribute {name!r}")
