//! Volatility indicators.
//!
//! Includes: Bollinger Bands, ATR, Keltner Channels, Donchian Channels, Standard Deviation

use super::moving_averages::{EmaState, SmaState};
use super::Signal;

/// Bollinger Bands state.
pub struct BollingerState {
    period: usize,
    std_mult: f64,
    idx: usize,
    count: usize,
    sum: f64,
    sumsq: f64,
    buffer: Vec<f64>,
}

impl BollingerState {
    pub fn new(period: usize, std_mult: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            std_mult,
            idx: 0,
            count: 0,
            sum: 0.0,
            sumsq: 0.0,
            buffer: vec![0.0; period],
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        if self.period == 0 {
            return Signal::default();
        }

        if self.count < self.period {
            self.buffer[self.count] = close;
            self.sum += close;
            self.sumsq += close * close;
            self.count += 1;
            if self.count < self.period {
                return Signal::default();
            }
        } else {
            let old = self.buffer[self.idx];
            self.sum -= old;
            self.sumsq -= old * old;
            self.buffer[self.idx] = close;
            self.sum += close;
            self.sumsq += close * close;
            self.idx = (self.idx + 1) % self.period;
        }

        let period_f = self.period as f64;
        let mean = self.sum / period_f;
        let mut variance = (self.sumsq / period_f) - (mean * mean);
        if variance < 0.0 {
            variance = 0.0;
        }
        let std = variance.sqrt();
        let upper = mean + self.std_mult * std;
        let lower = mean - self.std_mult * std;

        Signal {
            long: close < lower,
            short: close > upper,
        }
    }

    /// Get current Bollinger Bands values (middle, upper, lower).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        if self.count >= self.period {
            let period_f = self.period as f64;
            let mean = self.sum / period_f;
            let mut variance = (self.sumsq / period_f) - (mean * mean);
            if variance < 0.0 {
                variance = 0.0;
            }
            let std = variance.sqrt();
            let upper = mean + self.std_mult * std;
            let lower = mean - self.std_mult * std;
            Some((mean, upper, lower))
        } else {
            None
        }
    }
}

/// Average True Range (ATR) state.
pub struct AtrState {
    period: usize,
    multiplier: f64,
    prev_close: Option<f64>,
    atr: Option<f64>,
    tr_sum: f64,
    count: usize,
}

impl AtrState {
    pub fn new(period: usize, multiplier: f64) -> Self {
        Self {
            period: period.max(1),
            multiplier,
            prev_close: None,
            atr: None,
            tr_sum: 0.0,
            count: 0,
        }
    }

    /// Calculate True Range for a bar.
    fn true_range(high: f64, low: f64, prev_close: Option<f64>) -> f64 {
        let hl = high - low;
        if let Some(pc) = prev_close {
            let hc = (high - pc).abs();
            let lc = (low - pc).abs();
            hl.max(hc).max(lc)
        } else {
            hl
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        let tr = Self::true_range(high, low, self.prev_close);
        self.prev_close = Some(close);

        if let Some(atr) = self.atr.as_mut() {
            // Wilder's smoothing: ATR = ((period-1) * prev_ATR + TR) / period
            *atr = ((*atr * (self.period as f64 - 1.0)) + tr) / self.period as f64;
        } else {
            self.tr_sum += tr;
            self.count += 1;
            if self.count >= self.period {
                self.atr = Some(self.tr_sum / self.period as f64);
            }
        }

        // ATR itself doesn't generate signals; used for stops and position sizing
        // Return signal based on volatility expansion/contraction
        Signal::default()
    }

    /// Get current ATR value.
    pub fn current_atr(&self) -> Option<f64> {
        self.atr
    }

    /// Get ATR-based stop distance.
    pub fn stop_distance(&self) -> Option<f64> {
        self.atr.map(|atr| atr * self.multiplier)
    }
}

/// Keltner Channel state.
pub struct KeltnerState {
    ema: EmaState,
    atr: AtrState,
    atr_mult: f64,
}

impl KeltnerState {
    pub fn new(period: usize, atr_mult: f64) -> Self {
        Self {
            ema: EmaState::new(period),
            atr: AtrState::new(period, 1.0),
            atr_mult,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        let typical_price = (high + low + close) / 3.0;
        self.atr.update(high, low, close);
        let ema = self.ema.update(typical_price);

        if let (Some(middle), Some(atr)) = (ema, self.atr.current_atr()) {
            let upper = middle + self.atr_mult * atr;
            let lower = middle - self.atr_mult * atr;

            Signal {
                long: close < lower,
                short: close > upper,
            }
        } else {
            Signal::default()
        }
    }

    /// Get current Keltner Channel values (middle, upper, lower).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        let middle = self.ema.current()?;
        let atr = self.atr.current_atr()?;
        let upper = middle + self.atr_mult * atr;
        let lower = middle - self.atr_mult * atr;
        Some((middle, upper, lower))
    }

    /// Get current ATR value.
    pub fn current_atr(&self) -> Option<f64> {
        self.atr.current_atr()
    }
}

/// Donchian Channel state.
pub struct DonchianState {
    period: usize,
    high_buffer: Vec<f64>,
    low_buffer: Vec<f64>,
    idx: usize,
    count: usize,
    prev_close: Option<f64>,
}

impl DonchianState {
    pub fn new(period: usize) -> Self {
        let period = period.max(2);
        Self {
            period,
            high_buffer: vec![f64::NEG_INFINITY; period],
            low_buffer: vec![f64::INFINITY; period],
            idx: 0,
            count: 0,
            prev_close: None,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        // Update buffers
        if self.count < self.period {
            self.high_buffer[self.count] = high;
            self.low_buffer[self.count] = low;
            self.count += 1;
        } else {
            self.high_buffer[self.idx] = high;
            self.low_buffer[self.idx] = low;
            self.idx = (self.idx + 1) % self.period;
        }

        if self.count < self.period {
            self.prev_close = Some(close);
            return Signal::default();
        }

        let upper = self.high_buffer.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let lower = self.low_buffer.iter().cloned().fold(f64::INFINITY, f64::min);

        // Breakout signals
        let signal = if let Some(prev) = self.prev_close {
            Signal {
                long: prev < upper && close >= upper,   // Breakout above upper channel
                short: prev > lower && close <= lower,  // Breakout below lower channel
            }
        } else {
            Signal::default()
        };

        self.prev_close = Some(close);
        signal
    }

    /// Get current Donchian Channel values (upper, middle, lower).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        if self.count >= self.period {
            let upper = self.high_buffer.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let lower = self.low_buffer.iter().cloned().fold(f64::INFINITY, f64::min);
            let middle = (upper + lower) / 2.0;
            Some((upper, middle, lower))
        } else {
            None
        }
    }
}

/// Standard Deviation state.
pub struct StdDevState {
    period: usize,
    buffer: Vec<f64>,
    sum: f64,
    sumsq: f64,
    idx: usize,
    count: usize,
}

impl StdDevState {
    pub fn new(period: usize) -> Self {
        let period = period.max(2);
        Self {
            period,
            buffer: vec![0.0; period],
            sum: 0.0,
            sumsq: 0.0,
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if self.count < self.period {
            self.buffer[self.count] = value;
            self.sum += value;
            self.sumsq += value * value;
            self.count += 1;
            if self.count < self.period {
                return None;
            }
        } else {
            let old = self.buffer[self.idx];
            self.sum -= old;
            self.sumsq -= old * old;
            self.buffer[self.idx] = value;
            self.sum += value;
            self.sumsq += value * value;
            self.idx = (self.idx + 1) % self.period;
        }

        let mean = self.sum / self.period as f64;
        let mut variance = (self.sumsq / self.period as f64) - (mean * mean);
        if variance < 0.0 {
            variance = 0.0;
        }
        Some(variance.sqrt())
    }
}

/// Volatility Percentage state (measures relative volatility).
pub struct VolatilityPctState {
    atr: AtrState,
    sma: SmaState,
}

impl VolatilityPctState {
    pub fn new(period: usize) -> Self {
        Self {
            atr: AtrState::new(period, 1.0),
            sma: SmaState::new(period),
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Option<f64> {
        self.atr.update(high, low, close);
        self.sma.update(close);

        if let (Some(atr), Some(sma)) = (self.atr.current_atr(), self.sma.current()) {
            if sma > 0.0 {
                Some((atr / sma) * 100.0)
            } else {
                None
            }
        } else {
            None
        }
    }
}

/// Historical Volatility state (annualized standard deviation of returns).
pub struct HistoricalVolState {
    period: usize,
    periods_per_year: f64,
    prev_close: Option<f64>,
    returns_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl HistoricalVolState {
    pub fn new(period: usize, periods_per_year: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            periods_per_year,
            prev_close: None,
            returns_buffer: vec![0.0; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, close: f64) -> Option<f64> {
        let log_return = if let Some(prev) = self.prev_close {
            if prev > 0.0 && close > 0.0 {
                (close / prev).ln()
            } else {
                0.0
            }
        } else {
            self.prev_close = Some(close);
            return None;
        };
        self.prev_close = Some(close);

        if self.count < self.period {
            self.returns_buffer[self.count] = log_return;
            self.count += 1;
            if self.count < self.period {
                return None;
            }
        } else {
            self.returns_buffer[self.idx] = log_return;
            self.idx = (self.idx + 1) % self.period;
        }

        // Calculate standard deviation of returns
        let sum: f64 = self.returns_buffer.iter().sum();
        let mean = sum / self.period as f64;
        let variance: f64 = self.returns_buffer
            .iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>()
            / (self.period - 1) as f64;
        
        let std_dev = variance.sqrt();
        
        // Annualize
        Some(std_dev * self.periods_per_year.sqrt())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bollinger() {
        let mut boll = BollingerState::new(2, 0.5);
        assert!(!boll.update(1.0).short);
        let signal = boll.update(3.0);
        assert!(signal.short);
        assert!(!signal.long);

        let mut boll_long = BollingerState::new(2, 0.5);
        assert!(!boll_long.update(3.0).long);
        let signal = boll_long.update(1.0);
        assert!(signal.long);
        assert!(!signal.short);
    }

    #[test]
    fn test_atr() {
        let mut atr = AtrState::new(3, 2.0);
        atr.update(102.0, 98.0, 100.0);
        atr.update(103.0, 99.0, 101.0);
        atr.update(104.0, 100.0, 102.0);
        assert!(atr.current_atr().is_some());
    }

    #[test]
    fn test_keltner() {
        let mut kelt = KeltnerState::new(3, 2.0);
        for i in 0..5 {
            let price = 100.0 + i as f64;
            kelt.update(price + 1.0, price - 1.0, price);
        }
        assert!(kelt.current().is_some());
    }

    #[test]
    fn test_donchian() {
        let mut don = DonchianState::new(3);
        don.update(102.0, 98.0, 100.0);
        don.update(103.0, 99.0, 101.0);
        don.update(104.0, 100.0, 102.0);
        let (upper, _middle, lower) = don.current().unwrap();
        assert_eq!(upper, 104.0);
        assert_eq!(lower, 98.0);
    }
}
