from __future__ import annotations

class Ppu:
    """
    Represents a Chilean PPU (vehicle license plate).

    Attributes
    ----------
    raw : str
        The input PPU.
    numeric : str
        The numeric representation of the PPU.
    normalized: str
        The normalized PPU.
    verifier: str
        The calculated verifier digit of the PPU.
    format: str
        The detected format of the PPU. Supported formats:

        - `LLLNN`  -> 3 letters followed by 2 digits
        - `LLLNNN` -> 4 letters followed by 3 digits
        - `LLLLNN` -> 4 letters followed by 2 digits
        - `LLNNNN` -> 2 letters followed by 4 digits
    complete: str
        The normalized PPU with the verifier digit, separated by '-'.
    """

    def __init__(self, ppu: str, /) -> None:
        """
        Initializes a Ppu instance by normalizing the input PPU and
        calculating its numeric representation.

        Parameters
        ----------
        ppu : str
            Chilean PPU (vehicle license plate).
        """

    @property
    def raw(self) -> str:
        """The input PPU."""

    @property
    def numeric(self) -> str:
        """The numeric representation of the PPU."""

    @property
    def normalized(self) -> str:
        """The normalized PPU."""

    @property
    def verifier(self) -> str:
        """The calculated verifier digit of the PPU."""

    @property
    def format(self) -> str:
        """The detected format of the PPU."""

    @property
    def complete(self) -> str:
        """The normalized PPU with the verifier digit, separated by '-'."""


def calculate_verifier(digits: str, /) -> str:
    """
    Calculates the verifier digit (DV) of a Chilean RUT/RUN using Module 11
    algorithm.

    Parameters
    ----------
    digits : str
        Numeric part of the RUT/RUN (digits only).

    Returns
    -------
    str
        Verifier digit: '0'..'9' or 'K'.
    """


def ppu_to_numeric(ppu: str, /) -> str:
    """
    Converts a Chilean PPU (vehicle license plate) into its numeric
    representation.

    Parameters
    ----------
    ppu : str
        Chilean PPU (vehicle license plate). Supported formats:

        - `LLLNN`  -> 3 letters followed by 2 digits
        - `LLLNNN` -> 4 letters followed by 3 digits
        - `LLLLNN` -> 4 letters followed by 2 digits
        - `LLNNNN` -> 2 letters followed by 4 digits

    Returns
    -------
    str
        Numeric representation of the PPU.
    """


def normalize_ppu(ppu: str, /) -> str:
    """
    Normalizes a given PPU string to a standard format.

    If the format is recognized as `LLLNN` (3 letters followed by 2 digits),
    the function prepends a '0' after the first 3 characters, resulting in a
    normalized format of `LLL0NN`. Otherwise, the `ppu` is returned as-is, but
    trimmed in uppercase.

    Parameters
    ----------
    ppu : Chilean PPU (vehicle license plate).

    Returns
    -------
    str
        Normalized PPU.
    """


def validate_rut(digits: str, verifier: str, /) -> bool:
    """
    Validates a Chilean RUT/RUN by checking if the provided verifier digit
    matches the calculated one using Module 11 algorithm.

    Parameters
    ----------
    digits : str
        Numeric part of the RUT/RUN (digits only).
    verifier : str
        Verifier digit to validate against: "0".."9" or "K".

    Returns
    -------
    bool
        `True` if the verifier is valid for the given correlative,
        `False` otherwise.
    """


def generate(
        n: int,
        min: int,
        max: int,
        seed: int | None = None
) -> list[dict[str, int | str]]:
    """
    Generates a list of unique Chilean RUT/RUN numbers with their verifier
    digits.

    Parameters
    ----------
    n : int
        The number of RUT/RUNs to generate.
    min : int
        The minimum value for the numeric part of the RUT/RUN.
    max : int
        The maximum value for the numeric part of the RUT/RUN.
    seed : int | None
        An optional seed for the random number generator to ensure
        reproducibility. If `None`, a random seed is used.

    Returns
    -------
    list[dict[str, int | str]]
        A list of dictionaries, each containing 'correlative' and 'verifier'
        keys representing the generated RUT/RUN numbers.
    
    Raises
    ------
    InvalidInput
        - If `n` is less than or equal to 0.
        - If `min` and/or `max` are negative.
        - If `seed` is given and is negative.
    InvalidRange
        If `min` is greater than or equal to `max`.
    InsufficientRange
        If the range between `min` and `max` is too small to generate `n`
        unique RUT/RUNs.
    """