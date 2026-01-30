from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._rs_cl_forge import _rs_cmf
    
    CmfClient = _rs_cmf.CmfClient

__all__ = (
    "CmfClient",
)

def __getattr__(name: str):
    if name in __all__:
        from ._rs_cl_forge import _rs_cmf
        return getattr(_rs_cmf, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")