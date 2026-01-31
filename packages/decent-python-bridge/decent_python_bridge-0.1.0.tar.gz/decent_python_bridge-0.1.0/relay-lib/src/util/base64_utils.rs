use base64::{alphabet, engine::general_purpose, Engine};

pub fn bytes_to_base64(data: &[u8]) -> String {
    let engine = general_purpose::GeneralPurpose::new(
        &alphabet::URL_SAFE,
        general_purpose::NO_PAD,
    );
    engine.encode(data)
}

pub fn base64_to_bytes(data: &str) -> Result<Vec<u8>, base64::DecodeError> {
    let cleaned = data.trim().trim_end_matches('=');

    // Attempt decoding with URL_SAFE_NO_PAD (common for our protocol)
    if let Ok(bytes) = general_purpose::URL_SAFE_NO_PAD.decode(cleaned) {
        return Ok(bytes);
    }

    // Fallback to STANDARD_NO_PAD
    general_purpose::STANDARD_NO_PAD.decode(cleaned)
}

