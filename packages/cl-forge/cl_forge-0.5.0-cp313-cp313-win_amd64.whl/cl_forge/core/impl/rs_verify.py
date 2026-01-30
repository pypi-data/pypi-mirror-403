from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._rs_cl_forge import _rs_verify
    
    Ppu = _rs_verify.Ppu
    calculate_verifier = _rs_verify.calculate_verifier
    normalize_ppu = _rs_verify.normalize_ppu
    ppu_to_numeric = _rs_verify.ppu_to_numeric
    validate_rut = _rs_verify.validate_rut
    generate = _rs_verify.generate

__all__ = (
    "Ppu",
    "calculate_verifier",
    "normalize_ppu",
    "ppu_to_numeric",
    "validate_rut",
    "generate",
)

def __getattr__(name: str):
    if name in __all__:
        from ._rs_cl_forge import _rs_verify
        return getattr(_rs_verify, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")