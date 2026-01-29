//! Data loading and bar data structures.

use std::fs::File;
use std::io::Read;
use std::path::Path;

#[cfg(feature = "parquet")]
use arrow2::array::{Array, PrimitiveArray};
#[cfg(feature = "parquet")]
use arrow2::datatypes::{DataType, TimeUnit};
#[cfg(feature = "parquet")]
use arrow2::io::parquet::read as parquet_read;
use csv_core::{ReadFieldResult, Reader as CsvReader};
use numpy::{ndarray, PyReadonlyArray2};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Column indices for bar data.
pub const BAR_TS: usize = 0;
pub const BAR_ASSET: usize = 1;
pub const BAR_OPEN: usize = 2;
pub const BAR_HIGH: usize = 3;
pub const BAR_LOW: usize = 4;
pub const BAR_CLOSE: usize = 5;
pub const BAR_VOLUME: usize = 6;

#[cfg(feature = "parquet")]
const PARQUET_COLUMNS: [&str; 7] = [
    "ts_epoch_us",
    "asset_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
];

/// Column storage that can be either Arrow arrays or Vecs.
#[cfg(feature = "parquet")]
#[derive(Clone)]
pub enum BarColumn<T: arrow2::types::NativeType> {
    Arrow(PrimitiveArray<T>),
    Vec(Vec<T>),
}

#[cfg(not(feature = "parquet"))]
#[derive(Clone)]
pub enum BarColumn<T> {
    Vec(Vec<T>),
}

#[cfg(feature = "parquet")]
impl<T: arrow2::types::NativeType> BarColumn<T> {
    pub fn len(&self) -> usize {
        match self {
            BarColumn::Arrow(array) => array.len(),
            BarColumn::Vec(values) => values.len(),
        }
    }

    pub fn values(&self) -> &[T] {
        match self {
            BarColumn::Arrow(array) => array.values().as_slice(),
            BarColumn::Vec(values) => values.as_slice(),
        }
    }
}

#[cfg(not(feature = "parquet"))]
impl<T> BarColumn<T> {
    pub fn len(&self) -> usize {
        match self {
            BarColumn::Vec(values) => values.len(),
        }
    }

    pub fn values(&self) -> &[T] {
        match self {
            BarColumn::Vec(values) => values.as_slice(),
        }
    }
}

/// A chunk of bar data (for streaming large files).
#[derive(Clone)]
pub struct BarChunk {
    pub ts: BarColumn<i64>,
    pub asset_id: BarColumn<u32>,
    pub open: BarColumn<f64>,
    pub high: BarColumn<f64>,
    pub low: BarColumn<f64>,
    pub close: BarColumn<f64>,
    pub volume: BarColumn<f64>,
    pub len: usize,
}

/// Bar data container with PyO3 bindings.
#[pyclass]
#[derive(Clone)]
pub struct BarData {
    pub chunks: Vec<BarChunk>,
    pub rows: usize,
    pub max_asset_id: u32,
}

#[pymethods]
impl BarData {
    #[getter]
    fn rows(&self) -> usize {
        self.rows
    }

    #[getter]
    fn max_asset_id(&self) -> u32 {
        self.max_asset_id
    }

    fn __len__(&self) -> usize {
        self.rows
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "BarData(rows={}, max_asset_id={})",
            self.rows, self.max_asset_id
        ))
    }
}

/// Format detection for bar files.
#[derive(Clone, Copy)]
enum BarFormat {
    Csv,
    Parquet,
}

fn detect_format(path: &Path) -> PyResult<BarFormat> {
    if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
        let ext = ext.to_ascii_lowercase();
        if ext == "csv" {
            return Ok(BarFormat::Csv);
        }
        if ext == "parquet" || ext == "parq" || ext == "pq" {
            return Ok(BarFormat::Parquet);
        }
    }

    let mut file = File::open(path).map_err(to_py_err)?;
    let mut magic = [0u8; 4];
    let read = file.read(&mut magic).map_err(to_py_err)?;
    if read == 4 && &magic == b"PAR1" {
        Ok(BarFormat::Parquet)
    } else {
        Ok(BarFormat::Csv)
    }
}

/// Load bar data from a file (CSV or Parquet, auto-detected).
#[pyfunction]
#[pyo3(signature = (path, has_header = None))]
pub fn load_bars(path: &str, has_header: Option<bool>) -> PyResult<BarData> {
    let path = Path::new(path);
    match detect_format(path)? {
        BarFormat::Csv => load_bars_csv_impl(path, has_header),
        BarFormat::Parquet => load_bars_parquet_impl(path),
    }
}

/// Load bar data from a CSV file.
#[pyfunction]
#[pyo3(signature = (path, has_header = None))]
pub fn load_bars_csv(path: &str, has_header: Option<bool>) -> PyResult<BarData> {
    load_bars_csv_impl(Path::new(path), has_header)
}

/// Load bar data from a Parquet file.
#[pyfunction]
pub fn load_bars_parquet(path: &str) -> PyResult<BarData> {
    load_bars_parquet_impl(Path::new(path))
}

/// Extract BarData from Python object (BarData or numpy array).
pub fn extract_bar_data(data: &Bound<'_, PyAny>) -> PyResult<BarData> {
    if let Ok(bars) = data.extract::<PyRef<BarData>>() {
        return Ok((*bars).clone());
    }
    if let Ok(array) = data.extract::<PyReadonlyArray2<f64>>() {
        let view = array.as_array();
        return bar_data_from_ndarray(&view);
    }
    Err(PyValueError::new_err(
        "data must be BarData or a numpy ndarray",
    ))
}

fn bar_data_from_ndarray(view: &ndarray::ArrayView2<'_, f64>) -> PyResult<BarData> {
    if view.nrows() == 0 {
        return Ok(BarData {
            chunks: vec![],
            rows: 0,
            max_asset_id: 0,
        });
    }
    let cols = view.ncols();
    if cols < 7 {
        return Err(PyValueError::new_err(
            "ndarray must have 7 columns: [ts_epoch_us, asset_id, open, high, low, close, volume]",
        ));
    }
    bar_data_from_wide_array(view)
}

fn bar_data_from_wide_array(view: &ndarray::ArrayView2<'_, f64>) -> PyResult<BarData> {
    let rows = view.nrows();
    let mut ts = Vec::with_capacity(rows);
    let mut asset = Vec::with_capacity(rows);
    let mut open = Vec::with_capacity(rows);
    let mut high = Vec::with_capacity(rows);
    let mut low = Vec::with_capacity(rows);
    let mut close = Vec::with_capacity(rows);
    let mut volume = Vec::with_capacity(rows);
    let mut max_asset_id = 0u32;
    let mut prev_ts: Option<i64> = None;

    for (row_idx, row) in view.rows().into_iter().enumerate() {
        let ts_val = to_i64(row[BAR_TS], "ts_epoch_us")?;
        let asset_val = to_u32(row[BAR_ASSET], "asset_id")?;
        let open_val = row[BAR_OPEN];
        let high_val = row[BAR_HIGH];
        let low_val = row[BAR_LOW];
        let close_val = row[BAR_CLOSE];
        let volume_val = row[BAR_VOLUME];

        // Validate OHLC consistency
        validate_ohlc(row_idx, open_val, high_val, low_val, close_val, volume_val)?;

        // Validate timestamp ordering (non-decreasing)
        if let Some(prev) = prev_ts {
            if ts_val < prev {
                return Err(PyValueError::new_err(format!(
                    "row {}: timestamp {} is before previous timestamp {}; data must be sorted by time",
                    row_idx, ts_val, prev
                )));
            }
        }
        prev_ts = Some(ts_val);

        if asset_val > max_asset_id {
            max_asset_id = asset_val;
        }
        ts.push(ts_val);
        asset.push(asset_val);
        open.push(open_val);
        high.push(high_val);
        low.push(low_val);
        close.push(close_val);
        volume.push(volume_val);
    }

    Ok(BarData {
        chunks: vec![BarChunk {
            len: rows,
            ts: BarColumn::Vec(ts),
            asset_id: BarColumn::Vec(asset),
            open: BarColumn::Vec(open),
            high: BarColumn::Vec(high),
            low: BarColumn::Vec(low),
            close: BarColumn::Vec(close),
            volume: BarColumn::Vec(volume),
        }],
        rows,
        max_asset_id,
    })
}

/// Validate OHLC bar data consistency.
fn validate_ohlc(row: usize, open: f64, high: f64, low: f64, close: f64, volume: f64) -> PyResult<()> {
    // Check for finite values
    if !open.is_finite() {
        return Err(PyValueError::new_err(format!(
            "row {}: open price must be finite, got {}",
            row, open
        )));
    }
    if !high.is_finite() {
        return Err(PyValueError::new_err(format!(
            "row {}: high price must be finite, got {}",
            row, high
        )));
    }
    if !low.is_finite() {
        return Err(PyValueError::new_err(format!(
            "row {}: low price must be finite, got {}",
            row, low
        )));
    }
    if !close.is_finite() {
        return Err(PyValueError::new_err(format!(
            "row {}: close price must be finite, got {}",
            row, close
        )));
    }
    if !volume.is_finite() {
        return Err(PyValueError::new_err(format!(
            "row {}: volume must be finite, got {}",
            row, volume
        )));
    }

    // Check for positive prices
    if open <= 0.0 {
        return Err(PyValueError::new_err(format!(
            "row {}: open price must be positive, got {}",
            row, open
        )));
    }
    if high <= 0.0 {
        return Err(PyValueError::new_err(format!(
            "row {}: high price must be positive, got {}",
            row, high
        )));
    }
    if low <= 0.0 {
        return Err(PyValueError::new_err(format!(
            "row {}: low price must be positive, got {}",
            row, low
        )));
    }
    if close <= 0.0 {
        return Err(PyValueError::new_err(format!(
            "row {}: close price must be positive, got {}",
            row, close
        )));
    }

    // Check for non-negative volume
    if volume < 0.0 {
        return Err(PyValueError::new_err(format!(
            "row {}: volume must be non-negative, got {}",
            row, volume
        )));
    }

    // Check OHLC relationships: high >= low, high >= open, high >= close, low <= open, low <= close
    if high < low {
        return Err(PyValueError::new_err(format!(
            "row {}: high ({}) must be >= low ({})",
            row, high, low
        )));
    }
    if high < open {
        return Err(PyValueError::new_err(format!(
            "row {}: high ({}) must be >= open ({})",
            row, high, open
        )));
    }
    if high < close {
        return Err(PyValueError::new_err(format!(
            "row {}: high ({}) must be >= close ({})",
            row, high, close
        )));
    }
    if low > open {
        return Err(PyValueError::new_err(format!(
            "row {}: low ({}) must be <= open ({})",
            row, low, open
        )));
    }
    if low > close {
        return Err(PyValueError::new_err(format!(
            "row {}: low ({}) must be <= close ({})",
            row, low, close
        )));
    }

    Ok(())
}

fn to_i64(value: f64, field: &str) -> PyResult<i64> {
    if !value.is_finite() {
        return Err(PyValueError::new_err(format!("{} must be finite", field)));
    }
    if value.fract() != 0.0 {
        return Err(PyValueError::new_err(format!(
            "{} must be an integer",
            field
        )));
    }
    if value < i64::MIN as f64 || value > i64::MAX as f64 {
        return Err(PyValueError::new_err(format!("{} out of range", field)));
    }
    Ok(value as i64)
}

fn to_u32(value: f64, field: &str) -> PyResult<u32> {
    if !value.is_finite() {
        return Err(PyValueError::new_err(format!("{} must be finite", field)));
    }
    if value.fract() != 0.0 {
        return Err(PyValueError::new_err(format!(
            "{} must be an integer",
            field
        )));
    }
    if value < 0.0 || value > u32::MAX as f64 {
        return Err(PyValueError::new_err(format!("{} out of range", field)));
    }
    Ok(value as u32)
}

fn parse_i64_csv(field: &str) -> Option<i64> {
    let value = field.parse::<f64>().ok()?;
    if !value.is_finite() || value.fract() != 0.0 {
        return None;
    }
    if value < i64::MIN as f64 || value > i64::MAX as f64 {
        return None;
    }
    Some(value as i64)
}

fn parse_u32_csv(field: &str) -> Option<u32> {
    let value = field.parse::<f64>().ok()?;
    if !value.is_finite() || value.fract() != 0.0 {
        return None;
    }
    if value < 0.0 || value > u32::MAX as f64 {
        return None;
    }
    Some(value as u32)
}

fn load_bars_csv_impl(path: &Path, has_header: Option<bool>) -> PyResult<BarData> {
    let data = std::fs::read(path).map_err(to_py_err)?;
    let mut rdr = CsvReader::new();
    let mut pos = 0usize;
    let mut field_buf = vec![0u8; 128];
    let mut field_len = 0usize;
    let mut field_index = 0usize;
    let mut record_index = 0usize;
    let mut header_mode = has_header;
    let mut parse_failed = false;

    let mut ts_val = 0i64;
    let mut asset_val = 0u32;
    let mut open_val = 0f64;
    let mut high_val = 0f64;
    let mut low_val = 0f64;
    let mut close_val = 0f64;
    let mut volume_val = 0f64;

    let mut ts = Vec::new();
    let mut asset = Vec::new();
    let mut open = Vec::new();
    let mut high = Vec::new();
    let mut low = Vec::new();
    let mut close = Vec::new();
    let mut volume = Vec::new();
    let mut max_asset_id = 0u32;

    loop {
        let input = if pos < data.len() { &data[pos..] } else { &[] };
        let (res, nin, nout) = rdr.read_field(input, &mut field_buf[field_len..]);
        pos += nin;
        field_len += nout;

        match res {
            ReadFieldResult::InputEmpty => {
                if !input.is_empty() {
                    continue;
                }
            }
            ReadFieldResult::OutputFull => {
                field_buf.resize(field_buf.len() * 2, 0u8);
                continue;
            }
            ReadFieldResult::Field { record_end } => {
                let field = std::str::from_utf8(&field_buf[..field_len]).map_err(to_py_err)?;
                let field = field.trim();
                if !parse_failed {
                    match field_index {
                        BAR_TS => match parse_i64_csv(field) {
                            Some(v) => ts_val = v,
                            None => parse_failed = true,
                        },
                        BAR_ASSET => match parse_u32_csv(field) {
                            Some(v) => asset_val = v,
                            None => parse_failed = true,
                        },
                        BAR_OPEN => match field.parse::<f64>() {
                            Ok(v) => open_val = v,
                            Err(_) => parse_failed = true,
                        },
                        BAR_HIGH => match field.parse::<f64>() {
                            Ok(v) => high_val = v,
                            Err(_) => parse_failed = true,
                        },
                        BAR_LOW => match field.parse::<f64>() {
                            Ok(v) => low_val = v,
                            Err(_) => parse_failed = true,
                        },
                        BAR_CLOSE => match field.parse::<f64>() {
                            Ok(v) => close_val = v,
                            Err(_) => parse_failed = true,
                        },
                        BAR_VOLUME => match field.parse::<f64>() {
                            Ok(v) => volume_val = v,
                            Err(_) => parse_failed = true,
                        },
                        _ => parse_failed = true,
                    }
                }
                field_index += 1;
                field_len = 0;

                if record_end {
                    if field_index != 7 {
                        parse_failed = true;
                    }
                    let is_header = match header_mode {
                        Some(true) => record_index == 0,
                        Some(false) => false,
                        None => parse_failed,
                    };
                    if header_mode.is_none() {
                        header_mode = Some(parse_failed);
                    }

                    if is_header {
                        // skip header row
                    } else if parse_failed {
                        return Err(PyValueError::new_err("CSV contains non-numeric fields"));
                    } else {
                        // Validate OHLC consistency
                        validate_ohlc(ts.len(), open_val, high_val, low_val, close_val, volume_val)?;

                        ts.push(ts_val);
                        asset.push(asset_val);
                        if asset_val > max_asset_id {
                            max_asset_id = asset_val;
                        }
                        open.push(open_val);
                        high.push(high_val);
                        low.push(low_val);
                        close.push(close_val);
                        volume.push(volume_val);
                    }

                    record_index += 1;
                    field_index = 0;
                    parse_failed = false;
                }
            }
            ReadFieldResult::End => break,
        }
    }

    let rows = ts.len();
    Ok(BarData {
        chunks: vec![BarChunk {
            len: rows,
            ts: BarColumn::Vec(ts),
            asset_id: BarColumn::Vec(asset),
            open: BarColumn::Vec(open),
            high: BarColumn::Vec(high),
            low: BarColumn::Vec(low),
            close: BarColumn::Vec(close),
            volume: BarColumn::Vec(volume),
        }],
        rows,
        max_asset_id,
    })
}

#[cfg(feature = "parquet")]
fn load_bars_parquet_impl(path: &Path) -> PyResult<BarData> {
    let mut file = File::open(path).map_err(to_py_err)?;
    let metadata = parquet_read::read_metadata(&mut file).map_err(to_py_err)?;
    let schema = parquet_read::infer_schema(&metadata).map_err(to_py_err)?;

    let (schema, column_map) = parquet_column_map(&schema)?;
    let row_groups = metadata.row_groups;
    let reader =
        parquet_read::FileReader::new(file, row_groups, schema, Some(1024 * 64), None, None);

    let mut chunks = Vec::new();
    let mut rows = 0usize;
    let mut max_asset_id = 0u32;

    for maybe_chunk in reader {
        let chunk = maybe_chunk.map_err(to_py_err)?;
        if chunk.is_empty() {
            continue;
        }
        let bar_chunk = chunk_to_bar_chunk(chunk, &column_map)?;
        rows += bar_chunk.len;
        let asset_values = bar_chunk.asset_id.values();
        if let Some(local_max) = asset_values.iter().copied().max() {
            if local_max > max_asset_id {
                max_asset_id = local_max;
            }
        }
        chunks.push(bar_chunk);
    }

    Ok(BarData {
        chunks,
        rows,
        max_asset_id,
    })
}

#[cfg(not(feature = "parquet"))]
fn load_bars_parquet_impl(_path: &Path) -> PyResult<BarData> {
    Err(PyValueError::new_err(
        "Parquet support disabled; enable the `parquet` feature",
    ))
}

#[cfg(feature = "parquet")]
fn parquet_column_map(
    schema: &arrow2::datatypes::Schema,
) -> PyResult<(arrow2::datatypes::Schema, [usize; 7])> {
    if schema.fields.len() < 7 {
        return Err(PyValueError::new_err(
            "Parquet file must have at least 7 columns",
        ));
    }
    let mut required = [None; 7];
    for (idx, field) in schema.fields.iter().enumerate() {
        for (req_idx, req_name) in PARQUET_COLUMNS.iter().enumerate() {
            if field.name.eq_ignore_ascii_case(req_name) {
                if required[req_idx].is_some() {
                    return Err(PyValueError::new_err(format!(
                        "Parquet column name '{}' appears multiple times",
                        req_name
                    )));
                }
                required[req_idx] = Some(idx);
            }
        }
    }
    let mut required_indices = [0usize; 7];
    for (idx, maybe_index) in required.iter().enumerate() {
        required_indices[idx] = maybe_index.ok_or_else(|| {
            PyValueError::new_err(format!(
                "Parquet file missing required column '{}'",
                PARQUET_COLUMNS[idx]
            ))
        })?;
    }

    let mut filtered_indices = required_indices.to_vec();
    filtered_indices.sort_unstable();
    filtered_indices.dedup();
    if filtered_indices.len() != 7 {
        return Err(PyValueError::new_err("Parquet columns must be unique"));
    }

    let mut keep = vec![false; schema.fields.len()];
    for idx in &filtered_indices {
        keep[*idx] = true;
    }
    let filtered_schema = schema.clone().filter(|index, _| keep[index]);

    let mut index_map = vec![None; schema.fields.len()];
    for (new_idx, orig_idx) in filtered_indices.iter().enumerate() {
        index_map[*orig_idx] = Some(new_idx);
    }

    let mut mapped = [0usize; 7];
    for (i, orig_idx) in required_indices.iter().enumerate() {
        mapped[i] = index_map[*orig_idx]
            .ok_or_else(|| PyValueError::new_err("Parquet column mapping failed"))?;
    }

    Ok((filtered_schema, mapped))
}

#[cfg(feature = "parquet")]
fn chunk_to_bar_chunk(
    chunk: arrow2::chunk::Chunk<Box<dyn Array>>,
    column_map: &[usize; 7],
) -> PyResult<BarChunk> {
    let arrays = chunk.arrays();
    if arrays.len() < 7 {
        return Err(PyValueError::new_err(
            "Parquet chunk must have 7 columns",
        ));
    }

    let ts = downcast_i64(arrays[column_map[BAR_TS]].as_ref(), "ts_epoch_us")?;
    let asset_id = downcast_u32(arrays[column_map[BAR_ASSET]].as_ref(), "asset_id")?;
    let open = downcast_f64(arrays[column_map[BAR_OPEN]].as_ref(), "open")?;
    let high = downcast_f64(arrays[column_map[BAR_HIGH]].as_ref(), "high")?;
    let low = downcast_f64(arrays[column_map[BAR_LOW]].as_ref(), "low")?;
    let close = downcast_f64(arrays[column_map[BAR_CLOSE]].as_ref(), "close")?;
    let volume = downcast_f64(arrays[column_map[BAR_VOLUME]].as_ref(), "volume")?;

    let len = ts.len();
    Ok(BarChunk {
        ts: BarColumn::Arrow(ts),
        asset_id: BarColumn::Arrow(asset_id),
        open: BarColumn::Arrow(open),
        high: BarColumn::Arrow(high),
        low: BarColumn::Arrow(low),
        close: BarColumn::Arrow(close),
        volume: BarColumn::Arrow(volume),
        len,
    })
}

#[cfg(feature = "parquet")]
fn downcast_i64(array: &dyn Array, name: &str) -> PyResult<PrimitiveArray<i64>> {
    match array.data_type() {
        DataType::Int64 | DataType::Timestamp(TimeUnit::Microsecond, _) => {}
        other => {
            return Err(PyValueError::new_err(format!(
                "{} must be int64 or timestamp(us), got {:?}",
                name, other
            )))
        }
    }
    if array.null_count() > 0 {
        return Err(PyValueError::new_err(format!("{} contains nulls", name)));
    }
    array
        .as_any()
        .downcast_ref::<PrimitiveArray<i64>>()
        .cloned()
        .ok_or_else(|| PyValueError::new_err(format!("{} must be int64", name)))
}

#[cfg(feature = "parquet")]
fn downcast_f64(array: &dyn Array, name: &str) -> PyResult<PrimitiveArray<f64>> {
    if array.data_type() != &DataType::Float64 {
        return Err(PyValueError::new_err(format!("{} must be float64", name)));
    }
    if array.null_count() > 0 {
        return Err(PyValueError::new_err(format!("{} contains nulls", name)));
    }
    array
        .as_any()
        .downcast_ref::<PrimitiveArray<f64>>()
        .cloned()
        .ok_or_else(|| PyValueError::new_err(format!("{} must be float64", name)))
}

#[cfg(feature = "parquet")]
fn downcast_u32(array: &dyn Array, name: &str) -> PyResult<PrimitiveArray<u32>> {
    if array.null_count() > 0 {
        return Err(PyValueError::new_err(format!("{} contains nulls", name)));
    }
    match array.data_type() {
        DataType::UInt32 => array
            .as_any()
            .downcast_ref::<PrimitiveArray<u32>>()
            .cloned()
            .ok_or_else(|| PyValueError::new_err(format!("{} must be u32", name))),
        DataType::Int32 => {
            let array = array
                .as_any()
                .downcast_ref::<PrimitiveArray<i32>>()
                .ok_or_else(|| PyValueError::new_err(format!("{} must be i32", name)))?;
            let mut values = Vec::with_capacity(array.len());
            for &value in array.values().iter() {
                if value < 0 {
                    return Err(PyValueError::new_err(format!(
                        "{} contains negative values",
                        name
                    )));
                }
                values.push(value as u32);
            }
            Ok(PrimitiveArray::from_vec(values))
        }
        other => Err(PyValueError::new_err(format!(
            "{} must be u32 or i32, got {:?}",
            name, other
        ))),
    }
}

fn to_py_err(err: impl std::fmt::Display) -> PyErr {
    PyValueError::new_err(err.to_string())
}
