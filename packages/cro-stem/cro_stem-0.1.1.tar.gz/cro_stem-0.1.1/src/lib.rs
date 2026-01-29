//! A lightweight, high-performance Croatian language stemmer.
//!
//! This library is a Rust port of a Python prototype, designed for speed and
//! efficiency with zero-copy and UTF-8 safety as primary goals. The stemming
//! process follows a deterministic, multi-phase pipeline.

// Use `lazy_static` to ensure our static data (like the normalization rules)
// is initialized only once, at runtime, when it's first accessed. This is
// the standard and most idiomatic way in Rust to handle complex static data
// that can't be computed at compile time (like a HashMap).
use lazy_static::lazy_static;
use std::collections::HashMap;
// `Cow` stands for "Clone-on-Write". It's a smart pointer that can hold either
// a borrowed reference (`&str`) or an owned value (`String`). We use it to
// avoid allocating a new String if the word hasn't been modified during a
// stemming phase, thus adhering to the zero-copy principle where possible.


// --- Static Data Definitions ---
// By defining these as `static` arrays of string slices (`&'static str`),
// we ensure they are compiled directly into the binary. They have a 'static
// lifetime, meaning they are available for the entire duration of the program's
// execution without any runtime initialization cost.

// Suffixes are sorted by length, from longest to shortest, to ensure our
// "Longest Match First" logic works correctly.
static SUFFIXES: &[&str] = &[
    "njak", "nost", "ijeg", "ijem", "nje", "aka", "ima", "ama", "jeh", "om", "em", "og", "im", "ih",
    "oj", "oh", "iš", "en", "ov", "ši", "a", "e", "i", "o", "u",
];

static PREFIXES: &[&str] = &["naj", "pre", "iz", "na", "po"];

// Here, `lazy_static!` creates a thread-safe, one-time initialized HashMap.
// The code inside the macro is executed only once.
lazy_static! {
    static ref NORMALIZATION_RULES: HashMap<&'static str, &'static str> = {
        let mut map = HashMap::new();
        map.insert("čovjec", "čovjek");
        map.insert("čovječ", "čovjek");
        map.insert("majc", "majk");
        map.insert("vrapc", "vrab");
        map.insert("jač", "jak");
        map.insert("mišlj", "misl");
        map.insert("sveučilišn", "sveučilišt");
        map.insert("ručic", "ruk");
        map.insert("pjes", "pjesm");
        map.insert("drveć", "drv");
        map.insert("molb", "mol");
        map.insert("mom", "momk");
        map.insert("rasl", "rast");
        map.insert("ljep", "lijep");
        map
    };
}

/// The main struct for the Croatian stemmer.
/// It holds mutable data, like user-defined exceptions.
#[derive(Default)]
pub struct CroStem {
    exceptions: HashMap<String, String>,
}

// The `impl` block is where we define methods associated with our `CroStem` struct.
impl CroStem {
    /// Creates a new `CroStem` instance.
    pub fn new() -> Self {
        CroStem {
            exceptions: HashMap::new(),
        }
    }

    /// The main stemming pipeline. Accepts a string slice to avoid unnecessary
    /// copying and returns an owned `String`.
    pub fn stem(&self, word: &str) -> String {
        // --- Phase 1: Sanitization ---
        // This phase is guaranteed to return an owned `String` because it
        // lowercases and may remove characters.
        let sanitized_word = self.sanitize(word);

        // --- Phase 2: Exception Handling ---
        // We check for exceptions early to skip the entire pipeline if a known
        // irregular word is found.
        if let Some(stem) = self.exceptions.get(&sanitized_word) {
            return stem.clone();
        }

        // --- Phase 3: Suffix Removal ---
        // This is the most complex phase. It repeatedly strips suffixes.
        // Because it can modify the word multiple times, it works with and
        // returns an owned `String`.
        let without_suffix = self.remove_suffix(&sanitized_word);

        // --- Phase 4: Prefix Removal ---
        // This phase is applied *after* suffix stripping, as determined through
        // testing. It can return a borrowed slice (`&str`) if no prefix is
        // found, or a new slice if one is stripped. We use `Cow` to handle this.
        let without_prefix = self.remove_prefix(&without_suffix);

        // --- Phase 5: Normalization ---
        // This final phase corrects the root based on sound changes. It returns
        // a `&str` (either the original slice or a 'static one from our map).
        let normalized = self.normalize(&without_prefix);

        normalized.to_string()
    }

    /// Sanitizes the input word by lowercasing and removing punctuation.
    /// This function must return an owned `String` because `to_lowercase()`
    /// can change the byte representation of the string.
    fn sanitize(&self, word: &str) -> String {
        // A simple `replace` loop is often fast enough for a small set of
        // punctuation. For a larger set, a `HashSet` or `filter` on chars
        // could be used.
        let mut clean = word.to_lowercase();
        clean.retain(|c: char| !matches!(c, '.' | ',' | ';' | ':' | '!' | '?'));
        clean
    }

    /// Repeatedly removes the longest matching suffix from the end of the word.
    /// Returns an owned `String` because the word is modified in a loop.
    fn remove_suffix(&self, word: &str) -> String {
        let mut result = word.to_string();
        loop {
            let original_len = result.len();

            for suffix in SUFFIXES {
                if result.ends_with(suffix) {
                    // This is a critical point for UTF-8 safety. We get the byte length
                    // of the potential root. `ends_with` guarantees that the suffix
                    // matches a byte sequence at the end, so a simple byte slice is safe
                    // and will not panic.
                    let root_byte_len = result.len() - suffix.len();
                    let potential_root = &result[..root_byte_len];

                    // We still need to count UTF-8 characters (`chars().count()`) for the
                    // length check, as `len()` would only give us bytes.
                    if potential_root.chars().count() > 2 {
                        result.truncate(root_byte_len);
                        break; // Restart the loop with the new, shorter word.
                    }
                }
            }

            // If the string length hasn't changed after a full pass over all
            // suffixes, no more suffixes can be removed, and we can exit.
            if result.len() == original_len {
                break;
            }
        }
        result
    }

    /// Removes the first matching prefix from the start of the word.
    /// Returns a `&str` slice, as it only ever removes from the beginning
    /// and doesn't need to allocate a new String.
    fn remove_prefix<'a>(&self, word: &'a str) -> &'a str {
        for prefix in PREFIXES {
            if word.starts_with(prefix) {
                // Slicing from the start is also UTF-8 safe because we use the
                // byte length of a known-good prefix.
                let potential_root = &word[prefix.len()..];
                if potential_root.chars().count() > 3 {
                    return potential_root;
                }
            }
        }
        word
    }

    /// Normalizes the word root based on a predefined set of rules.
    /// Returns a `&str` slice, either the original or a `'static` one from the
    // rule map. No allocation is performed.
    fn normalize<'a>(&self, word: &'a str) -> &'a str {
        // `get()` returns an `Option<&'static str>`.
        // `copied()` converts `Option<&'static &str>` to `Option<&'static str>`.
        // `unwrap_or()` returns the value if `Some`, or the provided default (`word`) if `None`.
        // This is a concise and highly efficient way to do a map lookup with a fallback.
        NORMALIZATION_RULES.get(word).copied().unwrap_or(word)
    }

    /// Adds a custom word-stem exception to the stemmer instance.
    pub fn add_exception(&mut self, word: String, stem: String) {
        self.exceptions.insert(word, stem);
    }
}


// --- Testing Module ---
// The `#[cfg(test)]` attribute tells the Rust compiler to only compile and
// run this module when `cargo test` is executed.
#[cfg(test)]
mod tests {
    // `use super::*;` brings all items from the parent module (our library)
    // into the scope of the tests.
    use super::*;

    #[test]
    fn test_basic_stemming() {
        let stemmer = CroStem::new();
        // This test now correctly reflects the logic, expecting "stan"
        assert_eq!(stemmer.stem("stanovi"), "stan");
        assert_eq!(stemmer.stem("stanova."), "stan");
    }

    #[test]
    fn test_prefix_removal() {
        let stemmer = CroStem::new();
        // The stem of "najljepši" should be "lijep" after removing "naj" and "ši".
        // A simple length check is a good, robust test.
        let result = stemmer.stem("najljepši");
        assert_eq!(result, "lijep");
    }

    #[test]
    fn test_normalization() {
        let stemmer = CroStem::new();
        // The stemmer should apply normalization rules correctly.
        let result = stemmer.stem("čovjeca"); // "čovjeca" -> "čovjec" -> "čovjek"
        assert_eq!(result, "čovjek");
    }

    #[test]
    fn test_exception_handling() {
        let mut stemmer = CroStem::new();
        // Exceptions should be handled before the main pipeline.
        stemmer.add_exception("bio".to_string(), "biti".to_string());
        let result = stemmer.stem("bio");
        assert_eq!(result, "biti");
    }
    
    #[test]
    fn test_full_pipeline() {
        let stemmer = CroStem::new();
        // "radišnost" -> "radiš" (suffix -nost) -> "rad" (suffix -iš)
        assert_eq!(stemmer.stem("radišnost"), "rad");
    }

    #[test]
    fn test_new_suffixes() {
        let stemmer = CroStem::new();
        assert_eq!(stemmer.stem("pjevanje"), "pjev");
        assert_eq!(stemmer.stem("hladnjak"), "hlad");
    }
}

// --- Python Bindings ---
// This section uses `pyo3` to create a Python module.

use pyo3::prelude::*;

// This is a wrapper function marked with `#[pyfunction]`. It will be exposed
// to Python. It creates a new stemmer instance for each call, which is simple
// and safe for multi-threading in Python, although a shared instance could
// be used for higher performance if needed.
#[pyfunction]
fn stem(word: &str) -> PyResult<String> {
    let stemmer = CroStem::new();
    Ok(stemmer.stem(word))
}

/// A Python module implemented in Rust.
#[pymodule]
fn cro_stem(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(stem, m)?)?;
    Ok(())
}

