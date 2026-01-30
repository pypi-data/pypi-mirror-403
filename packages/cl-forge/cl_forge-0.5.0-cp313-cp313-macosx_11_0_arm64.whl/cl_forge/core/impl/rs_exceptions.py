from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._rs_cl_forge import _rs_cmf, _rs_verify

    CmfClientException = _rs_cmf.CmfClientException
    EmptyPath = _rs_cmf.EmptyPath
    BadStatus = _rs_cmf.BadStatus
    EmptyApiKey = _rs_cmf.EmptyApiKey
    InvalidPath = _rs_cmf.InvalidPath
    ConnectError = _rs_cmf.ConnectError

    PpuException = _rs_verify.PpuException
    UnknownFormat = _rs_verify.UnknownFormat
    InvalidLength = _rs_verify.InvalidLength
    UnknownLetter = _rs_verify.UnknownLetter
    EmptyLetter = _rs_verify.EmptyLetter
    UnknownDigraph = _rs_verify.UnknownDigraph
    EmptyDigraph = _rs_verify.EmptyDigraph

    VerifierException = _rs_verify.VerifierException
    EmptyDigits = _rs_verify.EmptyDigits
    EmptyVerifier = _rs_verify.EmptyVerifier
    InvalidDigits = _rs_verify.InvalidDigits
    InvalidVerifier = _rs_verify.InvalidVerifier
    UnexpectedComputation = _rs_verify.UnexpectedComputation

    GenerateException = _rs_verify.GenerateException
    InvalidRange = _rs_verify.InvalidRange
    InvalidInput = _rs_verify.InvalidInput
    InsufficientRange = _rs_verify.InsufficientRange
    UnexpectedGeneration = _rs_verify.UnexpectedGeneration

__all__ = (
    "CmfClientException",
    "EmptyPath",
    "BadStatus",
    "EmptyApiKey",
    "InvalidPath",
    "ConnectError",
    "PpuException",
    "UnknownFormat",
    "InvalidLength",
    "UnknownLetter",
    "EmptyLetter",
    "UnknownDigraph",
    "EmptyDigraph",
    "VerifierException",
    "EmptyDigits",
    "EmptyVerifier",
    "InvalidDigits",
    "InvalidVerifier",
    "UnexpectedComputation",
    "GenerateException",
    "InvalidRange",
    "InvalidInput",
    "InsufficientRange",
    "UnexpectedGeneration",
)

__cmf_exceptions__ = (
    "CmfClientException",
    "EmptyPath",
    "BadStatus",
    "EmptyApiKey",
    "InvalidPath",
    "ConnectError",
)

__verify_exceptions__ = (
    "PpuException",
    "UnknownFormat",
    "InvalidLength",
    "UnknownLetter",
    "EmptyLetter",
    "UnknownDigraph",
    "EmptyDigraph",
    "VerifierException",
    "EmptyDigits",
    "EmptyVerifier",
    "InvalidDigits",
    "InvalidVerifier",
    "UnexpectedComputation",
    "GenerateException",
    "InvalidRange",
    "InvalidInput",
    "InsufficientRange",
    "UnexpectedGeneration",
)


def __getattr__(name: str):
    if name in __cmf_exceptions__:
        from ._rs_cl_forge import _rs_cmf as _cmf  # noqa
        return getattr(_cmf, name)
    if name in __verify_exceptions__:
        from ._rs_cl_forge import _rs_verify as _verify  # noqa
        return getattr(_verify, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
