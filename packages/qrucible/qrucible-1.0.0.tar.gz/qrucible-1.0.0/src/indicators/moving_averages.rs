//! Moving average indicators.
//!
//! Includes: SMA, EMA, WMA, DEMA, TEMA, KAMA, HMA, VWMA

use super::Signal;

/// Moving average type.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MaType {
    Sma,   // Simple Moving Average
    Ema,   // Exponential Moving Average
    Wma,   // Weighted Moving Average
    Dema,  // Double Exponential Moving Average
    Tema,  // Triple Exponential Moving Average
    Kama,  // Kaufman Adaptive Moving Average
    Hma,   // Hull Moving Average
}

impl MaType {
    pub fn from_str(s: &str) -> Self {
        match s.to_uppercase().as_str() {
            "EMA" => MaType::Ema,
            "WMA" => MaType::Wma,
            "DEMA" => MaType::Dema,
            "TEMA" => MaType::Tema,
            "KAMA" => MaType::Kama,
            "HMA" => MaType::Hma,
            _ => MaType::Sma,
        }
    }
}

/// Simple Moving Average state.
pub struct SmaState {
    period: usize,
    buffer: Vec<f64>,
    sum: f64,
    idx: usize,
    count: usize,
}

impl SmaState {
    pub fn new(period: usize) -> Self {
        Self {
            period: period.max(1),
            buffer: vec![0.0; period.max(1)],
            sum: 0.0,
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if self.period == 0 {
            return None;
        }

        self.sum += value;
        if self.count < self.period {
            self.buffer[self.count] = value;
            self.count += 1;
            if self.count == self.period {
                Some(self.sum / self.period as f64)
            } else {
                None
            }
        } else {
            let old = self.buffer[self.idx];
            self.sum -= old;
            self.buffer[self.idx] = value;
            self.idx = (self.idx + 1) % self.period;
            Some(self.sum / self.period as f64)
        }
    }

    pub fn current(&self) -> Option<f64> {
        if self.count >= self.period {
            Some(self.sum / self.period as f64)
        } else {
            None
        }
    }
}

/// Exponential Moving Average state.
pub struct EmaState {
    period: usize,
    multiplier: f64,
    ema: Option<f64>,
    count: usize,
    sum: f64,
}

impl EmaState {
    pub fn new(period: usize) -> Self {
        let period = period.max(1);
        Self {
            period,
            multiplier: 2.0 / (period as f64 + 1.0),
            ema: None,
            count: 0,
            sum: 0.0,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if let Some(ema) = self.ema {
            let new_ema = (value - ema) * self.multiplier + ema;
            self.ema = Some(new_ema);
            Some(new_ema)
        } else {
            self.sum += value;
            self.count += 1;
            if self.count >= self.period {
                let sma = self.sum / self.count as f64;
                self.ema = Some(sma);
                Some(sma)
            } else {
                None
            }
        }
    }

    pub fn current(&self) -> Option<f64> {
        self.ema
    }
}

/// Weighted Moving Average state.
pub struct WmaState {
    period: usize,
    buffer: Vec<f64>,
    idx: usize,
    count: usize,
    denominator: f64,
}

impl WmaState {
    pub fn new(period: usize) -> Self {
        let period = period.max(1);
        // Denominator = 1 + 2 + 3 + ... + n = n*(n+1)/2
        let denominator = (period * (period + 1)) as f64 / 2.0;
        Self {
            period,
            buffer: vec![0.0; period],
            idx: 0,
            count: 0,
            denominator,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if self.count < self.period {
            self.buffer[self.count] = value;
            self.count += 1;
        } else {
            self.buffer[self.idx] = value;
            self.idx = (self.idx + 1) % self.period;
        }

        if self.count >= self.period {
            let mut sum = 0.0;
            for i in 0..self.period {
                let buf_idx = (self.idx + i) % self.period;
                let weight = (i + 1) as f64;
                sum += self.buffer[buf_idx] * weight;
            }
            Some(sum / self.denominator)
        } else {
            None
        }
    }
}

/// Double Exponential Moving Average state.
pub struct DemaState {
    ema1: EmaState,
    ema2: EmaState,
}

impl DemaState {
    pub fn new(period: usize) -> Self {
        Self {
            ema1: EmaState::new(period),
            ema2: EmaState::new(period),
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if let Some(ema1) = self.ema1.update(value) {
            if let Some(ema2) = self.ema2.update(ema1) {
                // DEMA = 2 * EMA - EMA(EMA)
                return Some(2.0 * ema1 - ema2);
            }
        }
        None
    }
}

/// Triple Exponential Moving Average state.
pub struct TemaState {
    ema1: EmaState,
    ema2: EmaState,
    ema3: EmaState,
}

impl TemaState {
    pub fn new(period: usize) -> Self {
        Self {
            ema1: EmaState::new(period),
            ema2: EmaState::new(period),
            ema3: EmaState::new(period),
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if let Some(ema1) = self.ema1.update(value) {
            if let Some(ema2) = self.ema2.update(ema1) {
                if let Some(ema3) = self.ema3.update(ema2) {
                    // TEMA = 3 * EMA - 3 * EMA(EMA) + EMA(EMA(EMA))
                    return Some(3.0 * ema1 - 3.0 * ema2 + ema3);
                }
            }
        }
        None
    }
}

/// Kaufman Adaptive Moving Average state.
pub struct KamaState {
    period: usize,
    fast_sc: f64,   // Fast smoothing constant
    slow_sc: f64,   // Slow smoothing constant
    buffer: Vec<f64>,
    idx: usize,
    count: usize,
    kama: Option<f64>,
}

impl KamaState {
    pub fn new(period: usize, fast_period: usize, slow_period: usize) -> Self {
        let period = period.max(1);
        Self {
            period,
            fast_sc: 2.0 / (fast_period.max(2) as f64 + 1.0),
            slow_sc: 2.0 / (slow_period.max(2) as f64 + 1.0),
            buffer: vec![0.0; period],
            idx: 0,
            count: 0,
            kama: None,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        if self.count < self.period {
            self.buffer[self.count] = value;
            self.count += 1;
            if self.count == self.period {
                self.kama = Some(value);
            }
            return self.kama;
        }

        // Calculate Efficiency Ratio (ER)
        let oldest_idx = self.idx;
        let oldest = self.buffer[oldest_idx];
        let change = (value - oldest).abs();

        // Sum of absolute changes
        let mut volatility = 0.0;
        let mut prev = oldest;
        for i in 1..self.period {
            let buf_idx = (oldest_idx + i) % self.period;
            volatility += (self.buffer[buf_idx] - prev).abs();
            prev = self.buffer[buf_idx];
        }
        volatility += (value - prev).abs();

        let er = if volatility > 0.0 {
            change / volatility
        } else {
            0.0
        };

        // Smoothing constant = (ER * (fast_sc - slow_sc) + slow_sc)^2
        let sc = (er * (self.fast_sc - self.slow_sc) + self.slow_sc).powi(2);

        // Update buffer
        self.buffer[self.idx] = value;
        self.idx = (self.idx + 1) % self.period;

        // Update KAMA
        if let Some(prev_kama) = self.kama {
            let new_kama = prev_kama + sc * (value - prev_kama);
            self.kama = Some(new_kama);
        }

        self.kama
    }
}

/// Hull Moving Average state.
pub struct HmaState {
    half_wma: WmaState,
    full_wma: WmaState,
    sqrt_wma: WmaState,
    period: usize,
}

impl HmaState {
    pub fn new(period: usize) -> Self {
        let period = period.max(2);
        let half_period = period / 2;
        let sqrt_period = (period as f64).sqrt() as usize;
        Self {
            half_wma: WmaState::new(half_period.max(1)),
            full_wma: WmaState::new(period),
            sqrt_wma: WmaState::new(sqrt_period.max(1)),
            period,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        let half = self.half_wma.update(value);
        let full = self.full_wma.update(value);

        if let (Some(h), Some(f)) = (half, full) {
            // HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
            let raw = 2.0 * h - f;
            self.sqrt_wma.update(raw)
        } else {
            None
        }
    }
}

/// Generic moving average wrapper.
pub enum MovingAverage {
    Sma(SmaState),
    Ema(EmaState),
    Wma(WmaState),
    Dema(DemaState),
    Tema(TemaState),
    Kama(KamaState),
    Hma(HmaState),
}

impl MovingAverage {
    pub fn new(ma_type: MaType, period: usize) -> Self {
        match ma_type {
            MaType::Sma => MovingAverage::Sma(SmaState::new(period)),
            MaType::Ema => MovingAverage::Ema(EmaState::new(period)),
            MaType::Wma => MovingAverage::Wma(WmaState::new(period)),
            MaType::Dema => MovingAverage::Dema(DemaState::new(period)),
            MaType::Tema => MovingAverage::Tema(TemaState::new(period)),
            MaType::Kama => MovingAverage::Kama(KamaState::new(period, 2, 30)),
            MaType::Hma => MovingAverage::Hma(HmaState::new(period)),
        }
    }

    pub fn update(&mut self, value: f64) -> Option<f64> {
        match self {
            MovingAverage::Sma(state) => state.update(value),
            MovingAverage::Ema(state) => state.update(value),
            MovingAverage::Wma(state) => state.update(value),
            MovingAverage::Dema(state) => state.update(value),
            MovingAverage::Tema(state) => state.update(value),
            MovingAverage::Kama(state) => state.update(value),
            MovingAverage::Hma(state) => state.update(value),
        }
    }
}

/// Moving Average Crossover state.
pub struct MaCrossState {
    fast_ma: MovingAverage,
    slow_ma: MovingAverage,
    prev_fast: Option<f64>,
    prev_slow: Option<f64>,
}

impl MaCrossState {
    pub fn new(fast_window: usize, slow_window: usize, ma_type: &str) -> Self {
        let ma_type = MaType::from_str(ma_type);
        Self {
            fast_ma: MovingAverage::new(ma_type, fast_window),
            slow_ma: MovingAverage::new(ma_type, slow_window),
            prev_fast: None,
            prev_slow: None,
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        let fast = self.fast_ma.update(close);
        let slow = self.slow_ma.update(close);

        let signal = if let (Some(f), Some(s)) = (fast, slow) {
            // Generate signals based on crossover or position
            let long = f > s;
            let short = f < s;
            Signal { long, short }
        } else {
            Signal::default()
        };

        self.prev_fast = fast;
        self.prev_slow = slow;
        signal
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sma() {
        let mut sma = SmaState::new(3);
        assert!(sma.update(1.0).is_none());
        assert!(sma.update(2.0).is_none());
        assert_eq!(sma.update(3.0), Some(2.0)); // (1+2+3)/3 = 2
        assert_eq!(sma.update(4.0), Some(3.0)); // (2+3+4)/3 = 3
    }

    #[test]
    fn test_ema() {
        let mut ema = EmaState::new(3);
        assert!(ema.update(1.0).is_none());
        assert!(ema.update(2.0).is_none());
        let e1 = ema.update(3.0).unwrap(); // First value = SMA
        assert!((e1 - 2.0).abs() < 1e-10);
    }

    #[test]
    fn test_ma_cross() {
        let mut state = MaCrossState::new(2, 3, "SMA");
        let signal = state.update(1.0);
        assert!(!signal.long && !signal.short);
        let signal = state.update(2.0);
        assert!(!signal.long && !signal.short);
        let signal = state.update(3.0);
        assert!(signal.long);
        assert!(!signal.short);
    }
}
