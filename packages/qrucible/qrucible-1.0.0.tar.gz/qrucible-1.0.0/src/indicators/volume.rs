//! Volume indicators.
//!
//! Includes: OBV, VWAP, A/D Line, Chaikin Money Flow, Force Index

use super::moving_averages::{EmaState, SmaState};
use super::Signal;

/// On-Balance Volume (OBV) state.
pub struct ObvState {
    obv: f64,
    prev_close: Option<f64>,
    obv_ma: SmaState,
    prev_obv_ma: Option<f64>,
}

impl ObvState {
    pub fn new(ma_period: usize) -> Self {
        Self {
            obv: 0.0,
            prev_close: None,
            obv_ma: SmaState::new(ma_period),
            prev_obv_ma: None,
        }
    }

    pub fn update(&mut self, close: f64, volume: f64) -> Signal {
        if let Some(prev) = self.prev_close {
            if close > prev {
                self.obv += volume;
            } else if close < prev {
                self.obv -= volume;
            }
            // If close == prev, OBV stays the same
        }
        self.prev_close = Some(close);

        // Generate signal based on OBV vs its MA
        let obv_ma = self.obv_ma.update(self.obv);

        let signal = if let (Some(ma), Some(prev_ma)) = (obv_ma, self.prev_obv_ma) {
            Signal {
                long: self.obv > ma && self.obv > prev_ma,   // OBV breaking above MA
                short: self.obv < ma && self.obv < prev_ma,  // OBV breaking below MA
            }
        } else {
            Signal::default()
        };

        self.prev_obv_ma = obv_ma;
        signal
    }

    /// Get current OBV value.
    pub fn current(&self) -> f64 {
        self.obv
    }
}

/// Volume Weighted Average Price (VWAP) state.
pub struct VwapState {
    cumulative_volume: f64,
    cumulative_pv: f64,      // price * volume
    cumulative_pv2: f64,     // price^2 * volume (for standard deviation)
    std_mult: f64,
    session_start: bool,
}

impl VwapState {
    pub fn new(std_mult: f64) -> Self {
        Self {
            cumulative_volume: 0.0,
            cumulative_pv: 0.0,
            cumulative_pv2: 0.0,
            std_mult,
            session_start: true,
        }
    }

    /// Reset VWAP for new session.
    pub fn reset(&mut self) {
        self.cumulative_volume = 0.0;
        self.cumulative_pv = 0.0;
        self.cumulative_pv2 = 0.0;
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> Signal {
        let typical_price = (high + low + close) / 3.0;

        self.cumulative_volume += volume;
        self.cumulative_pv += typical_price * volume;
        self.cumulative_pv2 += typical_price * typical_price * volume;

        if self.cumulative_volume == 0.0 {
            return Signal::default();
        }

        let vwap = self.cumulative_pv / self.cumulative_volume;

        // Calculate VWAP standard deviation bands
        let variance = (self.cumulative_pv2 / self.cumulative_volume) - (vwap * vwap);
        let std = if variance > 0.0 { variance.sqrt() } else { 0.0 };

        let upper_band = vwap + self.std_mult * std;
        let lower_band = vwap - self.std_mult * std;

        Signal {
            long: close < lower_band,
            short: close > upper_band,
        }
    }

    /// Get current VWAP and bands (vwap, upper, lower).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        if self.cumulative_volume > 0.0 {
            let vwap = self.cumulative_pv / self.cumulative_volume;
            let variance = (self.cumulative_pv2 / self.cumulative_volume) - (vwap * vwap);
            let std = if variance > 0.0 { variance.sqrt() } else { 0.0 };
            let upper = vwap + self.std_mult * std;
            let lower = vwap - self.std_mult * std;
            Some((vwap, upper, lower))
        } else {
            None
        }
    }
}

/// Accumulation/Distribution Line state.
pub struct AdLineState {
    ad: f64,
    ad_ma: EmaState,
    prev_ad: Option<f64>,
}

impl AdLineState {
    pub fn new(ma_period: usize) -> Self {
        Self {
            ad: 0.0,
            ad_ma: EmaState::new(ma_period),
            prev_ad: None,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> Signal {
        let range = high - low;
        let money_flow_multiplier = if range > 0.0 {
            ((close - low) - (high - close)) / range
        } else {
            0.0
        };

        let money_flow_volume = money_flow_multiplier * volume;
        self.ad += money_flow_volume;

        // Generate signal based on A/D vs its MA
        let ad_ma = self.ad_ma.update(self.ad);

        let signal = if let (Some(ma), Some(prev)) = (ad_ma, self.prev_ad) {
            // Look for divergence or crossover
            Signal {
                long: self.ad > ma && prev <= ad_ma.unwrap_or(0.0),
                short: self.ad < ma && prev >= ad_ma.unwrap_or(0.0),
            }
        } else {
            Signal::default()
        };

        self.prev_ad = Some(self.ad);
        signal
    }

    /// Get current A/D value.
    pub fn current(&self) -> f64 {
        self.ad
    }
}

/// Chaikin Money Flow (CMF) state.
pub struct CmfState {
    period: usize,
    mfv_buffer: Vec<f64>,
    vol_buffer: Vec<f64>,
    idx: usize,
    count: usize,
    upper: f64,
    lower: f64,
}

impl CmfState {
    pub fn new(period: usize, lower: f64, upper: f64) -> Self {
        let period = period.max(1);
        Self {
            period,
            mfv_buffer: vec![0.0; period],
            vol_buffer: vec![0.0; period],
            idx: 0,
            count: 0,
            upper,
            lower,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> Signal {
        let range = high - low;
        let money_flow_multiplier = if range > 0.0 {
            ((close - low) - (high - close)) / range
        } else {
            0.0
        };
        let money_flow_volume = money_flow_multiplier * volume;

        if self.count < self.period {
            self.mfv_buffer[self.count] = money_flow_volume;
            self.vol_buffer[self.count] = volume;
            self.count += 1;
        } else {
            self.mfv_buffer[self.idx] = money_flow_volume;
            self.vol_buffer[self.idx] = volume;
            self.idx = (self.idx + 1) % self.period;
        }

        if self.count < self.period {
            return Signal::default();
        }

        let mfv_sum: f64 = self.mfv_buffer.iter().sum();
        let vol_sum: f64 = self.vol_buffer.iter().sum();

        let cmf = if vol_sum > 0.0 {
            mfv_sum / vol_sum
        } else {
            0.0
        };

        // CMF ranges from -1 to +1
        Signal {
            long: cmf > self.upper,
            short: cmf < self.lower,
        }
    }

    /// Get current CMF value.
    pub fn current(&self) -> Option<f64> {
        if self.count >= self.period {
            let mfv_sum: f64 = self.mfv_buffer.iter().sum();
            let vol_sum: f64 = self.vol_buffer.iter().sum();
            Some(if vol_sum > 0.0 { mfv_sum / vol_sum } else { 0.0 })
        } else {
            None
        }
    }
}

/// Force Index state.
pub struct ForceIndexState {
    prev_close: Option<f64>,
    ema: EmaState,
    prev_fi: Option<f64>,
}

impl ForceIndexState {
    pub fn new(period: usize) -> Self {
        Self {
            prev_close: None,
            ema: EmaState::new(period),
            prev_fi: None,
        }
    }

    pub fn update(&mut self, close: f64, volume: f64) -> Signal {
        let force = if let Some(prev) = self.prev_close {
            (close - prev) * volume
        } else {
            self.prev_close = Some(close);
            return Signal::default();
        };
        self.prev_close = Some(close);

        let fi_smoothed = self.ema.update(force);

        let signal = if let (Some(fi), Some(prev_fi)) = (fi_smoothed, self.prev_fi) {
            Signal {
                long: prev_fi <= 0.0 && fi > 0.0,   // Cross above zero
                short: prev_fi >= 0.0 && fi < 0.0,  // Cross below zero
            }
        } else {
            Signal::default()
        };

        self.prev_fi = fi_smoothed;
        signal
    }

    /// Get current Force Index value.
    pub fn current(&self) -> Option<f64> {
        self.ema.current()
    }
}

/// Ease of Movement (EMV) state.
pub struct EmvState {
    period: usize,
    prev_high: Option<f64>,
    prev_low: Option<f64>,
    ema: EmaState,
    prev_emv: Option<f64>,
}

impl EmvState {
    pub fn new(period: usize) -> Self {
        Self {
            period,
            prev_high: None,
            prev_low: None,
            ema: EmaState::new(period),
            prev_emv: None,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, volume: f64) -> Signal {
        let emv = if let (Some(prev_h), Some(prev_l)) = (self.prev_high, self.prev_low) {
            let distance_moved = ((high + low) / 2.0) - ((prev_h + prev_l) / 2.0);
            let box_ratio = if high != low && volume > 0.0 {
                (volume / 10000.0) / (high - low)
            } else {
                0.0
            };
            if box_ratio > 0.0 {
                distance_moved / box_ratio
            } else {
                0.0
            }
        } else {
            self.prev_high = Some(high);
            self.prev_low = Some(low);
            return Signal::default();
        };

        self.prev_high = Some(high);
        self.prev_low = Some(low);

        let emv_smoothed = self.ema.update(emv);

        let signal = if let (Some(e), Some(prev_e)) = (emv_smoothed, self.prev_emv) {
            Signal {
                long: prev_e <= 0.0 && e > 0.0,
                short: prev_e >= 0.0 && e < 0.0,
            }
        } else {
            Signal::default()
        };

        self.prev_emv = emv_smoothed;
        signal
    }
}

/// Volume Rate of Change state.
pub struct VrocState {
    period: usize,
    buffer: Vec<f64>,
    idx: usize,
    count: usize,
    threshold: f64,
}

impl VrocState {
    pub fn new(period: usize, threshold: f64) -> Self {
        let period = period.max(1);
        Self {
            period,
            buffer: vec![0.0; period],
            idx: 0,
            count: 0,
            threshold,
        }
    }

    pub fn update(&mut self, volume: f64) -> Signal {
        let old_volume = if self.count < self.period {
            self.buffer[self.count] = volume;
            self.count += 1;
            return Signal::default();
        } else {
            let old = self.buffer[self.idx];
            self.buffer[self.idx] = volume;
            self.idx = (self.idx + 1) % self.period;
            old
        };

        let vroc = if old_volume > 0.0 {
            ((volume - old_volume) / old_volume) * 100.0
        } else {
            0.0
        };

        // High VROC can indicate potential breakout
        Signal {
            long: vroc > self.threshold,
            short: vroc < -self.threshold,
        }
    }
}

/// Positive Volume Index (PVI) state.
pub struct PviState {
    pvi: f64,
    prev_close: Option<f64>,
    prev_volume: Option<f64>,
    pvi_ma: EmaState,
}

impl PviState {
    pub fn new(ma_period: usize) -> Self {
        Self {
            pvi: 1000.0,  // Start at 1000 (standard)
            prev_close: None,
            prev_volume: None,
            pvi_ma: EmaState::new(ma_period),
        }
    }

    pub fn update(&mut self, close: f64, volume: f64) -> Signal {
        if let (Some(prev_c), Some(prev_v)) = (self.prev_close, self.prev_volume) {
            if volume > prev_v && prev_c > 0.0 {
                // Volume increased, update PVI
                let roc = (close - prev_c) / prev_c;
                self.pvi *= 1.0 + roc;
            }
            // If volume decreased or stayed same, PVI unchanged
        }

        self.prev_close = Some(close);
        self.prev_volume = Some(volume);

        let pvi_ma = self.pvi_ma.update(self.pvi);

        if let Some(ma) = pvi_ma {
            Signal {
                long: self.pvi > ma,
                short: self.pvi < ma,
            }
        } else {
            Signal::default()
        }
    }
}

/// Negative Volume Index (NVI) state.
pub struct NviState {
    nvi: f64,
    prev_close: Option<f64>,
    prev_volume: Option<f64>,
    nvi_ma: EmaState,
}

impl NviState {
    pub fn new(ma_period: usize) -> Self {
        Self {
            nvi: 1000.0,  // Start at 1000 (standard)
            prev_close: None,
            prev_volume: None,
            nvi_ma: EmaState::new(ma_period),
        }
    }

    pub fn update(&mut self, close: f64, volume: f64) -> Signal {
        if let (Some(prev_c), Some(prev_v)) = (self.prev_close, self.prev_volume) {
            if volume < prev_v && prev_c > 0.0 {
                // Volume decreased, update NVI
                let roc = (close - prev_c) / prev_c;
                self.nvi *= 1.0 + roc;
            }
            // If volume increased or stayed same, NVI unchanged
        }

        self.prev_close = Some(close);
        self.prev_volume = Some(volume);

        let nvi_ma = self.nvi_ma.update(self.nvi);

        if let Some(ma) = nvi_ma {
            Signal {
                long: self.nvi > ma,
                short: self.nvi < ma,
            }
        } else {
            Signal::default()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_obv() {
        let mut obv = ObvState::new(3);
        obv.update(100.0, 1000.0);
        obv.update(101.0, 1500.0);  // Price up, add volume
        assert_eq!(obv.current(), 1500.0);
        obv.update(100.0, 2000.0);  // Price down, subtract volume
        assert_eq!(obv.current(), -500.0);
    }

    #[test]
    fn test_vwap() {
        let mut vwap = VwapState::new(2.0);
        vwap.update(101.0, 99.0, 100.0, 1000.0);
        vwap.update(102.0, 100.0, 101.0, 1500.0);
        let (v, _, _) = vwap.current().unwrap();
        assert!(v > 99.0 && v < 102.0);
    }

    #[test]
    fn test_cmf() {
        let mut cmf = CmfState::new(3, -0.25, 0.25);
        cmf.update(101.0, 99.0, 100.0, 1000.0);
        cmf.update(102.0, 100.0, 101.0, 1500.0);
        cmf.update(103.0, 101.0, 102.0, 2000.0);
        assert!(cmf.current().is_some());
    }
}
