use std::collections::HashSet;

use rand::Rng;
use rand::SeedableRng;
use rand::rngs::StdRng;

use crate::enums::PpuFormat;
use crate::errors::PpuError;
use crate::errors::VerifierError;
use crate::errors::GenerateError;
use crate::constants::LETTER_MAP;
use crate::constants::DIGRAPH_MAP;


/// Represents a Chilean RUT (Rol Único Tributario) with its correlative number
/// and verifier digit.
///
/// Examples
/// ```
/// use rs_verify::utils::Rut;
/// 
/// let rut = Rut { correlative: 12345678, verifier: '5' };
/// assert_eq!(rut.correlative, 12345678);
/// assert_eq!(rut.verifier, '5');
/// ```
#[derive(Debug, Clone)]
pub struct Rut {
    /// The correlative number of the RUT.
    pub correlative: u32,
    /// The verifier digit or character of the RUT.
    pub verifier: char,
}

/// Implements methods for the [`Rut`] struct.
impl Rut {
    /// Creates a new `Rut` instance by calculating the verifier digit
    /// based on the provided correlative number.
    //// # Arguments
    /// * `correlative` - A `u32` representing the correlative number of the RUT.
    /// # Returns
    /// * `Ok(Rut)` - A new `Rut` instance with the calculated verifier.
    /// * `Err(VerifierError)` - If there is an error calculating the verifier.
    /// # Examples
    /// ```
    /// use rs_verify::utils::{Rut, calculate_verifier};
    /// 
    /// let rut = Rut::new(12345678).unwrap();
    /// assert_eq!(rut.correlative, 12345678);
    /// assert_eq!(rut.verifier, calculate_verifier(&"12345678").unwrap());
    /// ```
    pub fn new(correlative: u32) -> Result<Self, VerifierError> {
        let verifier = calculate_verifier(&correlative.to_string())?;
        Ok(Rut { correlative, verifier })
    }
}


/// Detects the format of a Chilean PPU (vehicle license plate).
///
/// # Arguments
///
/// * `ppu` - A reference to a string slice containing the PPU.
///
/// # Returns
/// * `Some(PpuFormat)` - if the input matches one of the supported formats.
/// * `None` - if the input does not match any known PPU format.
///
/// # Supported formats
/// - `LLLNN`  -> 3 letters followed by 2 digits
/// - `LLLNNN` -> 4 letters followed by 3 digits
/// - `LLLLNN` -> 4 letters followed by 2 digits
/// - `LLNNNN` -> 2 letters followed by 4 digits
///
/// Where:
/// - `L` = ASCII uppercase letter (`A`–`Z`)
/// - `N` = ASCII digit (`0`–`9`)
///
/// # Behavior
/// The input is first normalized by trimming whitespaces and converting it to
/// uppercase ASCII characters. The function then attempts to match the PPU
/// against the supported formats based on its length and character position.
///
/// # Notes
/// This function performs no allocation other than temporary normalization
/// and does not validate semantic rules beyond format structure.
///
/// # Examples
/// ```
/// use rs_verify::utils::get_ppu_format;
/// use rs_verify::enums::PpuFormat;
///
/// assert_eq!(get_ppu_format("PHZ55"),  Some(PpuFormat::LLLNN));
/// assert_eq!(get_ppu_format("PHZ123"), Some(PpuFormat::LLLNNN));
/// assert_eq!(get_ppu_format("PHZF12"), Some(PpuFormat::LLLLNN));
/// assert_eq!(get_ppu_format("PH1234"), Some(PpuFormat::LLNNNN));
///
/// assert_eq!(get_ppu_format("BAD"), None);
/// assert_eq!(get_ppu_format("12345"), None);
/// ```
pub fn get_ppu_format(ppu: &str) -> Option<PpuFormat> {
    let ppu = ppu.trim().to_ascii_uppercase();
    let ppu_bytes = ppu.as_bytes();

    match ppu_bytes.len() {
        5 => {
            if ppu_bytes[..3].iter().all(u8::is_ascii_alphabetic)
                && ppu_bytes[3..].iter().all(u8::is_ascii_digit)
            {
                Some(PpuFormat::LLLNN)
            } else {
                None
            }
        }

        6 => {
            if ppu_bytes[..3].iter().all(u8::is_ascii_alphabetic)
                && ppu_bytes[3..].iter().all(u8::is_ascii_digit)
            {
                Some(PpuFormat::LLLNNN)
            } else if ppu_bytes[..4].iter().all(u8::is_ascii_alphabetic)
                && ppu_bytes[4..].iter().all(u8::is_ascii_digit)
            {
                Some(PpuFormat::LLLLNN)
            } else if ppu_bytes[..2].iter().all(u8::is_ascii_alphabetic)
                && ppu_bytes[2..].iter().all(u8::is_ascii_digit)
            {
                Some(PpuFormat::LLNNNN)
            } else {
                None
            }
        }

        _ => None,
    }
}


/// Normalizes a given PPU string to a standard format.
///
/// # Arguments
/// * `ppu` - A reference to a string slice containing the PPU to normalize.
///
/// # Returns
/// * `Ok(String)` - The normalized PPU string if the input is valid.
/// * `Err(PpuError::UnknownFormat)` - If the input PPU is not recognized as
///    one of the supported formats.
///
/// # Behavior
/// The function trims leading and trailing whitespace from the input `ppu`
/// and converts it to uppercase ASCII characters. Then, it attempts to
/// determine the format of the `ppu` using the `get_ppu_format` function:
///
/// - If the format is recognized as `LLLNN` (3 letters followed by 2 digits),
///   the function prepends a '0' after the first 3 characters, resulting in a
///   normalized format of `LLL0NN`.
///
/// - If the format is recognized but not `LLLNN`, the `ppu` is returned
///   as-is in uppercase.
///
/// - If the format is not recognized, the function returns an error with a
///   message indicating the input was invalid.
///
/// # Examples
/// ```
/// use rs_verify::utils::normalize_ppu;
///
/// // Example of a valid `LLLNN` format input:
/// let result = normalize_ppu("abc12").unwrap();
/// assert_eq!(result, "ABC012");
///
/// // Example of a valid input that does not match `LLLNN` format:
/// let result = normalize_ppu("XYZ123").unwrap();
/// assert_eq!(result, "XYZ123");
///
/// // Example of an invalid input:
/// let result = normalize_ppu("invalid_ppu");
/// assert!(result.is_err());
/// ```
pub fn normalize_ppu(ppu: &str) -> Result<String, PpuError> {
    let ppu = ppu.trim().to_ascii_uppercase();

    match get_ppu_format(&ppu) {
        Some(PpuFormat::LLLNN) => {
            let mut output = String::with_capacity(6);
            output.push_str(&ppu[..3]);
            output.push('0');
            output.push_str(&ppu[3..]);
            Ok(output)
        }
        Some(_) => Ok(ppu),
        None => Err(PpuError::UnknownFormat { ppu }),
    }
}


/// Gets the value associated with a given letter from the `LETTER_MAP`.
///
/// # Parameters
/// * `letter` - A string slice representing the letter to look up. It is
///    expected to be a single-character string.
///
/// # Returns
/// * `Ok(&str)` - The value associated with the letter if it exists in the
///    `LETTER_MAP`.
/// * `Err(PpuError)`:
///     - [`PpuError::EmptyLetter`] - If the input is an empty string.
///     - [`PpuError::InvalidLength`] - If the input is not a
///       single-character string.
///     - [`PpuError::UnknownLetter`] - If the letter is not found in the
///       `LETTER_MAP`.
///
/// # Behavior
/// This function converts the input letter to its uppercase ASCII
/// representation and looks up the corresponding value in the `LETTER_MAP`.
/// If the letter is not found, it returns an error.
///
/// # Examples
/// ```
/// use rs_verify::utils::get_letter_value;
///
/// // LETTER_MAP contains mapping for "B" to "1".
/// let result = get_letter_value("B");
/// assert_eq!(result.unwrap(), "1");
///
/// // For an unknown letter, the function will return an error.
/// let result = get_letter_value("A");
/// assert!(result.is_err());
/// ```
pub fn get_letter_value(letter: &str) -> Result<&str, PpuError> {
    let letter = letter.to_ascii_uppercase();

    if letter.is_empty() {
        return Err(PpuError::EmptyLetter);
    }

    if letter.len() != 1 {
        return Err(
            PpuError::InvalidLength {
                expected: 1, actual: letter.len(), chars: letter
            }
        );
    }

    LETTER_MAP
        .iter()
        .find(|(k, _)| *k == letter)
        .map(|(_, value)| *value)
        .ok_or_else(|| PpuError::UnknownLetter { letter })
}


/// Retrieves the value associated with a given two-letter digraph.
///
/// # Arguments
/// * `letters` - A string slice representing the two-letter digraph whose
///    value needs to be retrieved.
///
/// # Returns
/// * `Ok(&str)` - The value associated with the given digraph if it exists.
/// * `Err(PpuError)`:
///     - [`PpuError::EmptyDigraph`] - If the input string is empty.
///     - [`PpuError::InvalidLength`] - If the input string does not have
///       exactly two characters.
///     - [`PpuError::UnknownDigraph`] - If the digraph is not found in
///       `DIGRAPH_MAP`.
///
/// # Behavior
/// This function converts the input letters to its uppercase ASCII
/// representation and looks up the corresponding value in the `DIGRAPH_MAP`.
/// If the letters are not found, it returns an error.
///
/// # Example
/// ```
/// use rs_verify::utils::get_digraph_value;
///
/// // DIGRAPH_MAP contains mapping for "AA" to "001".
/// let result = get_digraph_value("AA");
/// assert_eq!(result.unwrap(), "001");
///
/// // For unknown letters, the function will return an error.
/// let result = rs_verify::utils::get_letter_value("MM");
/// assert!(result.is_err());
/// ```
pub fn get_digraph_value(letters: &str) -> Result<&str, PpuError> {
    let letters = letters.to_ascii_uppercase();

    if letters.is_empty() {
        return Err(PpuError::EmptyDigraph);
    }

    if letters.len() != 2 {
        return Err(
            PpuError::InvalidLength {
                expected: 2, actual: letters.len(), chars: letters
            }
        );
    }

    DIGRAPH_MAP
        .iter()
        .find(|(k, _)| *k == letters)
        .map(|(_, v)| *v)
        .ok_or_else(|| PpuError::UnknownDigraph { letters })
}


/// Converts a Chilean PPU (vehicle license plate) into its numeric
/// representation.
///
/// # Arguments
/// * `ppu` - A reference to a string slice containing the PPU to convert.
///
/// # Returns
/// * `Ok(String)` containing the numeric representation of the PPU if the input
///   is valid and supported.
/// * `Err(PpuError)`:
///   - [`PpuError::UnknownFormat`] - The PPU does not match any known format.
///
/// # Behavior
/// The input PPU is first normalized by trimming whitespace and converting it
/// to uppercase ASCII characters. The function then determines the PPU format
/// and applies the corresponding letter-to-number mapping rules.
///
/// # Mapping rules
/// - For format `LLNNNN` (2 letters followed by 4 digits):
///   - The first two letters are treated as a digraph and mapped using
///     [`DIGRAPH_MAP`] (e.g. `"BR1234"` → `"0871234"`).
///
/// - For all other supported formats:
///   - Each letter is mapped individually using [`LETTER_MAP`].
///   - Digits are preserved as-is.
///
/// # Supported formats
/// See [`get_ppu_format`] for the list of recognized PPU formats.
///
/// # Notes
/// - This function performs no heap allocation other than building the output
///   string.
/// - Semantic validation beyond format and mapping rules (e.g., verifier
///   digit) is not performed here.
///
/// # Examples
/// ```
/// use rs_verify::utils::ppu_to_numeric;
///
/// // Digraph-based mapping (LLNNNN)
/// assert_eq!(ppu_to_numeric("BR1234").unwrap(), "0871234");
///
/// // Letter-by-letter mapping
/// assert_eq!(ppu_to_numeric("PHZF55").unwrap(), "069455");
///
/// // Invalid format
/// assert!(ppu_to_numeric("INVALID").is_err());
/// ```
pub fn ppu_to_numeric(ppu: &str) -> Result<String, PpuError> {
    let ppu = ppu.trim().to_ascii_uppercase();

    let fmt = get_ppu_format(&ppu)
        .ok_or_else(|| PpuError::UnknownFormat { ppu: ppu.clone() })?;

    if fmt == PpuFormat::LLNNNN {
        let prefix = &ppu[..2];
        let mapped = get_digraph_value(prefix)?;
        let digits = &ppu[2..];
        let mut output = String::with_capacity(
            mapped.len() + digits.len()
        );

        output.push_str(mapped);
        output.push_str(digits);
        return Ok(output)
    }

    let mut output = String::with_capacity(ppu.len());
    for c in ppu.chars() {
        if c.is_ascii_digit() {
            output.push(c);
        } else if c.is_ascii_alphabetic() {
            let letter = c.to_string();
            let v = get_letter_value(&letter)?;
            output.push_str(v);
        }
    }
    Ok(output)
}


/// Calculates the verifier digit or character based on a set of input digits
/// using Module 11 algorithm.
///
/// # Parameters
/// * `digits`: A string slice containing the numeric digits used for the
///   computation. Leading and trailing whitespaces are automatically trimmed
///   before processing.
///
/// # Returns
/// * `Ok(char)`: The computed verifier digit. This may be a numeric character
///    (`'0'` to `'9'`) or the character `'K'`.
/// * `Err(VerifierError)`:
///   - [`VerifierError::EmptyDigits`]: The input string is empty after
///     trimming whitespace.
///   - [`VerifierError::InvalidDigits`]: The input contains non-digit
///     characters.
///   - [`VerifierError::UnexpectedComputation`]: An unexpected branch in
///     computation logic (should not occur under normal conditions).
///
/// # Note
/// Ensure that the expected input strictly contains ASCII digits and does not exceed the
/// size limit imposed by `u32` arithmetic, as very long strings may result in overflow errors.
///
/// # Panic Safety
/// This function assumes the internal digit parsing (`char.to_digit(10)`) will succeed
/// for valid inputs. Providing invalid input (e.g., non-digit characters) will trigger an
/// error rather than a panic.
///
/// # Algorithm
/// 1. Reverse traverses the digits and compute the weighted sum, where
///    weights cycle between 2 and 7.
/// 2. Compute the modulus of the sum (mod 11).
/// 3. Derive the verifier character based on the result:
///    - If remainder is 11, output `'0'`.
///    - If remainder is 10, output `'K'`.
///    - Otherwise, output the numerical remainder as a character.
///
/// # Examples
/// ```
/// use rs_verify::utils::calculate_verifier;
/// use rs_verify::errors::VerifierError;
///
/// // Valid input
/// let verifier = calculate_verifier("12345678").unwrap();
/// assert_eq!(verifier, '5');
///
/// // Input with whitespace
/// let verifier = calculate_verifier(" 54321 ").unwrap();
/// assert_eq!(verifier, '7');
///
/// // Invalid input (non-digit characters)
/// let result = calculate_verifier("12A34");
/// assert!(matches!(result, Err(VerifierError::InvalidDigits { .. })));
///
/// // Empty input
/// let result = calculate_verifier("");
/// assert!(matches!(result, Err(VerifierError::EmptyDigits)));
/// ```
pub fn calculate_verifier(digits: &str) -> Result<char, VerifierError> {
    let digits = digits.trim();

    if digits.is_empty() {
        return Err(VerifierError::EmptyDigits);
    }

    if !digits.chars().all(|c| c.is_ascii_digit()) {
        return Err(
            VerifierError::InvalidDigits { input: digits.to_string() }
        );
    }

    let mut sum: u32 = 0;
    let mut factor: u32 = 2;

    for char in digits.chars().rev() {
        let digit =char.to_digit(10).expect("digit");
        sum += digit * factor;
        factor += 1;
        if factor > 7 {
            factor = 2;
        }
    }

    let result = 11 - (sum % 11);

    let verifier = match result {
        11 => '0',
        10 => 'K',
        0..=9 => char::from_digit(result, 10).unwrap(),
        _ => return Err(VerifierError::UnexpectedComputation),
    };

    Ok(verifier)
}


/// Validates a Chilean RUT (Rol Único Tributario) against its verifier digit.
///
/// This function checks whether the provided verifier digit matches the
/// expected verifier computed from the given numeric RUT using the
/// Module 11 algorithm.
///
/// # Arguments
/// * `digits` - A string slice containing the numeric part of the RUT
///   (without dots or verifier digit).
/// * `verifier` - A string slice containing the verifier character.
///   This must be a single ASCII digit (`'0'`–`'9'`) or the letter `'K'`
///   (case-insensitive).
///
/// # Returns
/// * `Ok(true)` - If the computed verifier matches the provided verifier.
/// * `Ok(false)` - If the computed verifier does not match the provided verifier.
/// * `Err(VerifierError)`:
///   - [`VerifierError::EmptyVerifier`] - If the verifier is empty.
///   - [`VerifierError::InvalidVerifier`] - If the verifier is not a single
///     digit or `'K'`.
///   - Any error propagated from [`calculate_verifier`] if the numeric part
///     of the RUT is invalid.
///
/// # Behavior
/// The function first normalizes the `verifier` by trimming whitespace and
/// converting it to uppercase ASCII. It then validates the verifier format
/// before computing the expected verifier from `digits` using
/// [`calculate_verifier`].
///
/// The result is a boolean comparison between the computed verifier and the
/// provided one.
///
/// # Notes
/// - This function does not perform formatting or normalization of the numeric
///   RUT (e.g., removal of dots or separators).
/// - The verifier comparison is case-insensitive.
/// - This function does not panic for invalid input; all validation errors are
///   returned as [`VerifierError`].
///
/// # Examples
/// ```
/// use rs_verify::utils::validate_rut;
///
/// // Valid RUT
/// let result = validate_rut("17702664", "6").unwrap();
/// assert!(result);
///
/// // Invalid verifier
/// let result = validate_rut("17702664", "5").unwrap();
/// assert!(!result);
///
/// // Verifier 'K' is allowed
/// let result = validate_rut("12345678", "K");
/// // Result depends on the computed verifier
///
/// // Invalid verifier format
/// let result = validate_rut("17702664", "KK");
/// assert!(result.is_err());
/// ```
pub fn validate_rut(digits: &str, verifier: &str) -> Result<bool, VerifierError> {
    let verifier = verifier.trim().to_ascii_uppercase();

    if verifier.is_empty() {
        return Err(VerifierError::EmptyVerifier);
    }

    if verifier.len() != 1
        || !(verifier.chars().all(|c| c.is_ascii_digit())
            || verifier.chars().all(|c| c == 'K')
    ) {
        return Err(VerifierError::InvalidVerifier { verifier });
    }

    match calculate_verifier(digits) {
        Ok(dv) => Ok(dv.to_string() == verifier),
        Err(msg) => Err(msg),
    }
}


/// Generates a list of valid Chilean RUTs (Rol Único Tributario) within a
/// specified range.
/// # Arguments
/// * `n` - The number of RUTs to generate. Must be a positive integer.
/// * `min` - The minimum correlative number (inclusive) for RUT generation.
/// * `max` - The maximum correlative number (inclusive) for RUT generation.
/// * `seed` - An optional seed for the random number generator to ensure
///   reproducibility.
///
/// # Returns
/// * `Ok(Vec<Rut>)` - A vector containing the generated RUTs, each with its
///   correlative number and corresponding verifier digit.
/// * `Err(GenerateError)`:
///   - [`GenerateError::InvalidRange`] - If `min` is not less than `max`.
///   - [`GenerateError::InvalidCount`] - If `n` is zero or negative.
///   - [`GenerateError::UnexpectedGeneration`] - If an unexpected error occurs
///     during RUT generation.
///
/// # Behavior
/// The function initializes a random number generator, optionally seeded
/// for reproducibility. It then generates `n` random correlative numbers
/// within the specified range, computes their corresponding verifier digits,
/// and constructs `Rut` instances for each generated RUT.
///
/// # Notes
/// - The function ensures that the generated correlative numbers are unique
///   within the specified range.
///
/// # Examples
/// ```
/// use rs_verify::utils::generate;
/// // Generate 5 RUTs within the range 1000000 to 2000000.
/// let ruts = generate(5, 1000000, 2000000, Some(42)).unwrap();
/// assert_eq!(ruts.len(), 5);
/// for rut in ruts {
///     println!("RUT: {}-{}", rut.correlative, rut.verifier);
/// }
/// ```
pub fn generate(
        n: i32,
        min: i32,
        max: i32,
        seed: Option<i64>
) -> Result<Vec<Rut>, GenerateError> {
    if n <= 0 {
        return Err(
            GenerateError::InvalidInput {
                msg: format!("`n` must be greater than zero: '{}' was given.", n)
            }
        );
    }

    if min < 0 || max < 0 {
        return Err(
            GenerateError::InvalidInput {
                msg: format!("`min` and `max` must be non-negative: min='{}', max='{}'.", min, max)
            }
        );
    }

    if !seed.is_none() && seed.unwrap() < 0 {
        return Err(
            GenerateError::InvalidInput {
                msg: format!("`seed` must be non-negative: '{}' was given.", seed.unwrap())
            }
        );
    }

    if min >= max {
        return Err(GenerateError::InvalidRange { min, max });
    }

    let range_size = (max - min + 1) as i32;
    if (n as i32) > range_size {
        return Err(GenerateError::InsufficientRange {
            n: n as i32,
            range_size,
        });
    }

    let mut rng: Box<dyn rand::RngCore> = match seed {
        Some(s) => Box::new(StdRng::seed_from_u64(s as u64)),
        None => Box::new(rand::thread_rng()),
    };

    let mut rut_list: Vec<Rut> = Vec::with_capacity(n as usize);
    let mut seen = HashSet::with_capacity(n as usize);

    while rut_list.len() < n as usize {
        let correlative = rng.gen_range(min..=max);
        if seen.insert(correlative) {
            let rut = Rut::new(correlative as u32)?;
            rut_list.push(rut);
        }
    }

    Ok(rut_list)
}