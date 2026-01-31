use pyo3::exceptions::{PyIOError, PyValueError};
use pyo3::prelude::*;
use regex::Regex;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::io::{Read, Seek, SeekFrom};

/// Backwards search for the "1 f =" block, then extract ALL cm-1 matches with captures_iter.
/// Returns (freqs_cm, has_imag).
#[pyfunction]
fn extract_frequencies_backwards(path: &str) -> PyResult<(Vec<f64>, bool)> {
    const CHUNK_SIZE: usize = 64 * 1024; // 64 KiB

    // open file and get length
    let mut f = File::open(path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open '{}': {}", path, e)))?;
    let file_len = f
        .metadata()
        .map_err(|e| PyIOError::new_err(format!("Failed to stat '{}': {}", path, e)))?
        .len();
    if file_len == 0 {
        return Ok((Vec::new(), false));
    }

    // IMPORTANT: (?mi) -> multiline + case-insensitive so ^ matches every line
    let line_re =
        Regex::new(r"(?mi)^\s*\d+\s+f\s*=.*?([+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)\s*cm-1")
            .map_err(|e| PyValueError::new_err(format!("Invalid line regex: {}", e)))?;
    let start_re = Regex::new(r"(?m)^[ \t]*1[ \t]+f[ \t]*=")
        .map_err(|e| PyValueError::new_err(format!("Invalid start regex: {}", e)))?;

    // accumulate suffix bytes
    let mut acc: Vec<u8> = Vec::new();
    let mut acc_offset: i64 = file_len as i64;

    // read backwards in chunks until we find start marker or reach file start
    while (acc_offset as u64) > 0 {
        let read_size = std::cmp::min(acc_offset as usize, CHUNK_SIZE);
        let new_offset = acc_offset - read_size as i64;
        f.seek(SeekFrom::Start(new_offset as u64))
            .map_err(|e| PyIOError::new_err(format!("Seek error '{}': {}", path, e)))?;
        let mut tmp = vec![0u8; read_size];
        f.read_exact(&mut tmp)
            .map_err(|e| PyIOError::new_err(format!("Read error '{}': {}", path, e)))?;

        // prepend tmp into acc (tmp earlier in file)
        if acc.is_empty() {
            acc = tmp;
        } else {
            let mut new_acc = Vec::with_capacity(tmp.len() + acc.len());
            new_acc.extend_from_slice(&tmp);
            new_acc.extend_from_slice(&acc);
            acc = new_acc;
        }
        acc_offset = new_offset;

        // search for start marker in acc (lossy conversion is fine for ASCII OUTCAR)
        let acc_text = String::from_utf8_lossy(&acc);
        if let Some(m) = start_re.find_iter(&acc_text).last() {
            // start is in acc; take substring from match start to end and extract all matches
            let start_pos = m.start();
            let tail_text = &acc_text[start_pos..];

            // If the tail contains "f/i" anywhere, mark has_imag true.
            let mut has_imag = tail_text.to_lowercase().contains("f/i");

            let mut freqs: Vec<f64> = Vec::new();
            for cap in line_re.captures_iter(tail_text) {
                // captured numeric field (cm-1)
                if let Some(num_m) = cap.get(1) {
                    let num_str = num_m.as_str();
                    match num_str.parse::<f64>() {
                        Ok(v) => {
                            if v > 0.0 {
                                freqs.push(v);
                            } else {
                                // non-positive frequency: mark imaginary, don't append
                                has_imag = true;
                            }
                        }
                        Err(e) => {
                            return Err(PyValueError::new_err(format!(
                                "Failed to parse '{}' as float: {}",
                                num_str, e
                            )));
                        }
                    }
                }
            }
            return Ok((freqs, has_imag));
        }

        if acc_offset == 0 {
            break;
        }
    }

    // fallback: read whole file and search
    let mut full_text = String::new();
    f.seek(SeekFrom::Start(0))
        .map_err(|e| PyIOError::new_err(format!("Seek error '{}': {}", path, e)))?;
    f.read_to_string(&mut full_text)
        .map_err(|e| PyIOError::new_err(format!("Read error '{}': {}", path, e)))?;
    if let Some(m) = start_re.find_iter(&full_text).last() {
        let tail_text = &full_text[m.start()..];
        let mut has_imag = tail_text.to_lowercase().contains("f/i");
        let mut freqs: Vec<f64> = Vec::new();
        for cap in line_re.captures_iter(tail_text) {
            if let Some(num_m) = cap.get(1) {
                let num_str = num_m.as_str();
                match num_str.parse::<f64>() {
                    Ok(v) => {
                        if v > 0.0 {
                            freqs.push(v);
                        } else {
                            has_imag = true;
                        }
                    }
                    Err(e) => {
                        return Err(PyValueError::new_err(format!(
                            "Failed to parse '{}' as float: {}",
                            num_str, e
                        )));
                    }
                }
            }
        }
        return Ok((freqs, has_imag));
    }

    Ok((Vec::new(), false))
}

/// extract_frequencies(path: str) -> (List[float], bool)
#[pyfunction]
fn extract_frequencies(path: &str) -> PyResult<(Vec<f64>, bool)> {
    let file = File::open(path)
        .map_err(|e| PyIOError::new_err(format!("Failed to open '{}': {}", path, e)))?;
    let reader = BufReader::new(file);

    let freq_re = Regex::new(r"([+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)\s*cm-1")
        .map_err(|e| PyValueError::new_err(format!("Invalid regex: {}", e)))?;

    let mut freqs: Vec<f64> = Vec::new();
    let mut has_imag = false;

    for line_res in reader.lines() {
        let line = line_res.map_err(|e| PyIOError::new_err(format!("Read error: {}", e)))?;
        if line.to_lowercase().contains("f/i") {
            has_imag = true;
            continue;
        }
        for cap in freq_re.captures_iter(&line) {
            let s = &cap[1];
            match s.parse::<f64>() {
                Ok(val) => {
                    if val > 0.0 {
                        freqs.push(val);
                    } else {
                        has_imag = true;
                    }
                }
                Err(e) => {
                    return Err(PyValueError::new_err(format!(
                        "Failed to parse frequency '{}': {}",
                        s, e
                    )));
                }
            }
        }
    }

    Ok((freqs, has_imag))
}

/// A Python module implemented in Rust.
#[pymodule]
#[pyo3(name = "_frequency_extraction")]
mod frequency_extraction {
    #[pymodule_export]
    use super::{extract_frequencies, extract_frequencies_backwards};
}
