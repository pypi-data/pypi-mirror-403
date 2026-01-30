from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclasses import dataclass
    from typing import Literal

    from cl_forge.core.schemas import EurRecord, IpcRecord, UFRecord, UsdRecord, UTMRecord

class CmfClient:
    """
    Client for interacting with the Chilean CMF API.

    The API is free to use, but has a limit of 10.000 monthly requests per
    user and requires an API key for authentication, which can be requested in
    `Contact`_ and is usually sent to the given email during the day.

    .. _Contact: https://api.cmfchile.cl/api_cmf/contactanos.jsp

    Attributes
    ----------
    api_key: str
        Truncated API Key to at most 5 characters.
    base_url: str
        The base URL for the CMF API.

    Notes
    -----
    - CMF stands for `Comisión para el Mercado Financiero`.
    """
    def __init__(self, api_key: str) -> None:
        """
        Initializes the CMF client with the provided API key.

        Parameters
        ----------
        api_key: str
            The API key for authenticating with the CMF API.
        """

    def get(
            self,
            path: str,
            format: Literal['json', 'xml'] = 'json', # noqa: A002
            params: dict | None = None
    ) -> dict | str:
        """
        Sends a GET request to the specified CMF API endpoint. See the `API Docs`_
        for all the available endpoints.

        .. _API Docs: https://api.cmfchile.cl/documentacion/index.html

        Parameters
        ----------
        path : str
            The API endpoint path. Must start with '/'.
        format : Literal['json', 'xml']
            The format of the response. Must be lower case 'json' or 'xml'.
            Defaults to 'json'.
        params : dict | None
            Optional query parameters for the request.

        Raises
        ------
        EmptyPath
            If the path is empty.
        InvalidPath
            If the path doesn't start with '/'.
        BadStatus
            If the request doesn't succeed (status code != 200).
        ValueError
            If the format is not 'json' or 'xml', or if fail to parse JSON the
            response.

        Returns
        -------
        dict | str
            The response from the CMF API. Returns a dict if format is 'json', 
            and a str if format is 'xml'.
        """


@dataclass(frozen=True)
class Ipc:
    """
    Client for the CMF IPC (Índice de Precios al Consumidor) endpoints.
    """
    __slots__ = ("_client",)

    def __init__(self, api_key: str) -> None:
        """
        Initializes the IPC client with the provided API key.

        Parameters
        ----------
        api_key : str
            The API key for authenticating with the CMF API.
        """

    def current(
            self,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> IpcRecord:
        """
        Retrieves the lastest available IPC record.

        Parameters
        ----------
        fmt : Literal['json', 'xml']
            The format of the response. Must be lower case 'json' or 'xml'.
            Defaults to 'json'.

        Returns
        -------
        IpcRecord
            The latest IPC record.
        """

    def year(
            self,
            year: int | None = None,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> list[IpcRecord]:
        """
        Retrieves the IPC records for a specific year.

        Parameters
        ----------
        year : int | None
            The year for which to retrieve IPC records. If None, defaults to
            the current year.
        fmt : Literal['xml', 'json']
            The format of the response. Must be lower case 'json' or 'xml'.

        Returns
        -------
        list[IpcRecord]
            A list of IPC records for the specified year.

        Raises
        ------
        BadStatus
            If there's no data available for the specified year.
        """

@dataclass(frozen=True)
class Usd:
    """
    Client for the CMF USD (Dólar Observado) endpoints.
    """
    __slots__ = ("_client",)

    def __init__(self, api_key: str) -> None: ...

    def current(
            self,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> UsdRecord: ...

    def year(
            self,
            year: int | None = None,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> list[UsdRecord]: ...


@dataclass(frozen=True)
class Eur:
    """
    Client for the CMF EUR (Euro) endpoints.
    """
    __slots__ = ("_client",)

    def __init__(self, api_key: str) -> None: ...

    def current(
            self,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> EurRecord: ...

    def year(
            self,
            year: int | None = None,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> list[EurRecord]: ...

@dataclass(frozen=True)
class Uf:
    """
    Client for the CMF UF (Unidad de Fomento) endpoints.
    """
    __slots__ = ("_client",)

    def __init__(self, api_key: str) -> None: ...

    def current(
            self,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> UFRecord: ...

    def year(
            self,
            year: int | None = None,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> list[UFRecord]: ...


@dataclass(frozen=True)
class Utm:
    """
    Client for the CMF UTM (Unidad Tributaria Mensual) endpoints.
    """
    __slots__ = ("_client",)

    def __init__(self, api_key: str) -> None: ...

    def current(
            self,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> UTMRecord: ...

    def year(
            self,
            year: int | None = None,
            fmt: Literal['xml', 'json'] = 'json'
    ) -> list[UTMRecord]: ...