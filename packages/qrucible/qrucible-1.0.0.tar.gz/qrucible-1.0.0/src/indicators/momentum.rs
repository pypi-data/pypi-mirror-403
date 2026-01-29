//! Momentum indicators.
//!
//! Includes: RSI, Stochastic, Williams %R, ROC, MFI, TSI, Ultimate Oscillator, MACD

use super::moving_averages::EmaState;
use super::Signal;

/// Relative Strength Index (RSI) state.
pub struct RsiState {
    period: usize,
    lower: f64,
    upper: f64,
    prev_close: Option<f64>,
    gain_sum: f64,
    loss_sum: f64,
    avg_gain: f64,
    avg_loss: f64,
    count: usize,
}

impl RsiState {
    pub fn new(period: usize, lower: f64, upper: f64) -> Self {
        Self {
            period: period.max(2),
            lower,
            upper,
            prev_close: None,
            gain_sum: 0.0,
            loss_sum: 0.0,
            avg_gain: 0.0,
            avg_loss: 0.0,
            count: 0,
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        if let Some(prev) = self.prev_close {
            let delta = close - prev;
            let gain = if delta > 0.0 { delta } else { 0.0 };
            let loss = if delta < 0.0 { -delta } else { 0.0 };

            if self.count < self.period {
                self.gain_sum += gain;
                self.loss_sum += loss;
                self.count += 1;
                if self.count == self.period {
                    let period_f = self.period as f64;
                    self.avg_gain = self.gain_sum / period_f;
                    self.avg_loss = self.loss_sum / period_f;
                }
            } else {
                let period_f = self.period as f64;
                self.avg_gain = (self.avg_gain * (period_f - 1.0) + gain) / period_f;
                self.avg_loss = (self.avg_loss * (period_f - 1.0) + loss) / period_f;
            }
        }
        self.prev_close = Some(close);

        if self.count >= self.period {
            let rsi = if self.avg_loss == 0.0 {
                100.0
            } else {
                let rs = self.avg_gain / self.avg_loss;
                100.0 - (100.0 / (1.0 + rs))
            };
            Signal {
                long: rsi < self.lower,
                short: rsi > self.upper,
            }
        } else {
            Signal::default()
        }
    }

    /// Get current RSI value.
    pub fn current(&self) -> Option<f64> {
        if self.count >= self.period {
            let rsi = if self.avg_loss == 0.0 {
                100.0
            } else {
                let rs = self.avg_gain / self.avg_loss;
                100.0 - (100.0 / (1.0 + rs))
            };
            Some(rsi)
        } else {
            None
        }
    }
}

/// MACD (Moving Average Convergence Divergence) state.
pub struct MacdState {
    fast_ema: EmaState,
    slow_ema: EmaState,
    signal_ema: EmaState,
    prev_histogram: Option<f64>,
}

impl MacdState {
    pub fn new(fast_period: usize, slow_period: usize, signal_period: usize) -> Self {
        Self {
            fast_ema: EmaState::new(fast_period),
            slow_ema: EmaState::new(slow_period),
            signal_ema: EmaState::new(signal_period),
            prev_histogram: None,
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        let fast = self.fast_ema.update(close);
        let slow = self.slow_ema.update(close);

        if let (Some(f), Some(s)) = (fast, slow) {
            let macd_line = f - s;
            if let Some(signal_line) = self.signal_ema.update(macd_line) {
                let histogram = macd_line - signal_line;

                // Signal on histogram crossover or direction
                let signal = if let Some(prev) = self.prev_histogram {
                    Signal {
                        long: prev <= 0.0 && histogram > 0.0,
                        short: prev >= 0.0 && histogram < 0.0,
                    }
                } else {
                    Signal::default()
                };

                self.prev_histogram = Some(histogram);
                return signal;
            }
        }

        Signal::default()
    }

    /// Get current MACD values (line, signal, histogram).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        let fast = self.fast_ema.current()?;
        let slow = self.slow_ema.current()?;
        let macd_line = fast - slow;
        let signal_line = self.signal_ema.current()?;
        Some((macd_line, signal_line, macd_line - signal_line))
    }
}

/// Stochastic Oscillator state.
pub struct StochasticState {
    k_period: usize,
    d_period: usize,
    lower: f64,
    upper: f64,
    high_buffer: Vec<f64>,
    low_buffer: Vec<f64>,
    k_buffer: Vec<f64>,
    idx: usize,
    k_idx: usize,
    count: usize,
    k_count: usize,
}

impl StochasticState {
    pub fn new(k_period: usize, d_period: usize, lower: f64, upper: f64) -> Self {
        let k_period = k_period.max(2);
        let d_period = d_period.max(1);
        Self {
            k_period,
            d_period,
            lower,
            upper,
            high_buffer: vec![f64::NEG_INFINITY; k_period],
            low_buffer: vec![f64::INFINITY; k_period],
            k_buffer: vec![0.0; d_period],
            idx: 0,
            k_idx: 0,
            count: 0,
            k_count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        // Update buffers
        if self.count < self.k_period {
            self.high_buffer[self.count] = high;
            self.low_buffer[self.count] = low;
            self.count += 1;
        } else {
            self.high_buffer[self.idx] = high;
            self.low_buffer[self.idx] = low;
            self.idx = (self.idx + 1) % self.k_period;
        }

        if self.count < self.k_period {
            return Signal::default();
        }

        // Calculate %K
        let highest = self.high_buffer.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let lowest = self.low_buffer.iter().cloned().fold(f64::INFINITY, f64::min);
        let range = highest - lowest;

        let k = if range > 0.0 {
            ((close - lowest) / range) * 100.0
        } else {
            50.0
        };

        // Update K buffer for %D
        if self.k_count < self.d_period {
            self.k_buffer[self.k_count] = k;
            self.k_count += 1;
        } else {
            self.k_buffer[self.k_idx] = k;
            self.k_idx = (self.k_idx + 1) % self.d_period;
        }

        if self.k_count < self.d_period {
            return Signal::default();
        }

        // Calculate %D (SMA of %K)
        let d: f64 = self.k_buffer.iter().sum::<f64>() / self.d_period as f64;

        Signal {
            long: k < self.lower && d < self.lower,
            short: k > self.upper && d > self.upper,
        }
    }

    /// Get current K and D values.
    pub fn current(&self) -> Option<(f64, f64)> {
        if self.count >= self.k_period && self.k_count >= self.d_period {
            let k = self.k_buffer[(self.k_idx + self.d_period - 1) % self.d_period];
            let d = self.k_buffer.iter().sum::<f64>() / self.d_period as f64;
            Some((k, d))
        } else {
            None
        }
    }
}

/// Williams %R state.
pub struct WilliamsState {
    period: usize,
    lower: f64,
    upper: f64,
    high_buffer: Vec<f64>,
    low_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl WilliamsState {
    pub fn new(period: usize, lower: f64, upper: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            lower,
            upper,
            high_buffer: vec![f64::NEG_INFINITY; period],
            low_buffer: vec![f64::INFINITY; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
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
            return Signal::default();
        }

        let highest = self.high_buffer.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let lowest = self.low_buffer.iter().cloned().fold(f64::INFINITY, f64::min);
        let range = highest - lowest;

        let williams_r = if range > 0.0 {
            ((highest - close) / range) * -100.0
        } else {
            -50.0
        };

        // Williams %R ranges from -100 to 0
        // Oversold: < -80 (lower), Overbought: > -20 (upper)
        Signal {
            long: williams_r < self.lower,
            short: williams_r > self.upper,
        }
    }
}

/// Rate of Change (ROC) state.
pub struct RocState {
    period: usize,
    threshold: f64,
    buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl RocState {
    pub fn new(period: usize, threshold: f64) -> Self {
        let period = period.max(1);
        Self {
            period,
            threshold,
            buffer: vec![0.0; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        let old_close = if self.count < self.period {
            self.buffer[self.count] = close;
            self.count += 1;
            return Signal::default();
        } else {
            let old = self.buffer[self.idx];
            self.buffer[self.idx] = close;
            self.idx = (self.idx + 1) % self.period;
            old
        };

        let roc = if old_close != 0.0 {
            ((close - old_close) / old_close) * 100.0
        } else {
            0.0
        };

        Signal {
            long: roc > self.threshold,
            short: roc < -self.threshold,
        }
    }
}

/// Money Flow Index (MFI) state.
pub struct MfiState {
    period: usize,
    lower: f64,
    upper: f64,
    prev_typical_price: Option<f64>,
    positive_flow_buffer: Vec<f64>,
    negative_flow_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl MfiState {
    pub fn new(period: usize, lower: f64, upper: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            lower,
            upper,
            prev_typical_price: None,
            positive_flow_buffer: vec![0.0; period],
            negative_flow_buffer: vec![0.0; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64, volume: f64) -> Signal {
        let typical_price = (high + low + close) / 3.0;
        let raw_money_flow = typical_price * volume;

        let (positive_flow, negative_flow) = if let Some(prev_tp) = self.prev_typical_price {
            if typical_price > prev_tp {
                (raw_money_flow, 0.0)
            } else if typical_price < prev_tp {
                (0.0, raw_money_flow)
            } else {
                (0.0, 0.0)
            }
        } else {
            self.prev_typical_price = Some(typical_price);
            return Signal::default();
        };

        self.prev_typical_price = Some(typical_price);

        if self.count < self.period {
            self.positive_flow_buffer[self.count] = positive_flow;
            self.negative_flow_buffer[self.count] = negative_flow;
            self.count += 1;
            return Signal::default();
        } else {
            self.positive_flow_buffer[self.idx] = positive_flow;
            self.negative_flow_buffer[self.idx] = negative_flow;
            self.idx = (self.idx + 1) % self.period;
        }

        let positive_sum: f64 = self.positive_flow_buffer.iter().sum();
        let negative_sum: f64 = self.negative_flow_buffer.iter().sum();

        let mfi = if negative_sum > 0.0 {
            let money_ratio = positive_sum / negative_sum;
            100.0 - (100.0 / (1.0 + money_ratio))
        } else {
            100.0
        };

        Signal {
            long: mfi < self.lower,
            short: mfi > self.upper,
        }
    }
}

/// True Strength Index (TSI) state.
pub struct TsiState {
    prev_close: Option<f64>,
    pc_ema1: EmaState,  // Price change EMA (long)
    pc_ema2: EmaState,  // Price change EMA (short)
    apc_ema1: EmaState, // Absolute price change EMA (long)
    apc_ema2: EmaState, // Absolute price change EMA (short)
    signal_ema: EmaState,
    prev_tsi: Option<f64>,
}

impl TsiState {
    pub fn new(long_period: usize, short_period: usize, signal_period: usize) -> Self {
        Self {
            prev_close: None,
            pc_ema1: EmaState::new(long_period),
            pc_ema2: EmaState::new(short_period),
            apc_ema1: EmaState::new(long_period),
            apc_ema2: EmaState::new(short_period),
            signal_ema: EmaState::new(signal_period),
            prev_tsi: None,
        }
    }

    pub fn update(&mut self, close: f64) -> Signal {
        let price_change = if let Some(prev) = self.prev_close {
            close - prev
        } else {
            self.prev_close = Some(close);
            return Signal::default();
        };
        self.prev_close = Some(close);

        let abs_price_change = price_change.abs();

        // Double-smoothed price change
        let pc_smooth1 = self.pc_ema1.update(price_change);
        let apc_smooth1 = self.apc_ema1.update(abs_price_change);

        if let (Some(pc1), Some(apc1)) = (pc_smooth1, apc_smooth1) {
            let pc_smooth2 = self.pc_ema2.update(pc1);
            let apc_smooth2 = self.apc_ema2.update(apc1);

            if let (Some(pc2), Some(apc2)) = (pc_smooth2, apc_smooth2) {
                let tsi = if apc2 != 0.0 {
                    (pc2 / apc2) * 100.0
                } else {
                    0.0
                };

                if let Some(signal_line) = self.signal_ema.update(tsi) {
                    let signal = if let Some(prev) = self.prev_tsi {
                        // Signal on TSI crossing signal line
                        Signal {
                            long: prev <= signal_line && tsi > signal_line,
                            short: prev >= signal_line && tsi < signal_line,
                        }
                    } else {
                        Signal::default()
                    };
                    self.prev_tsi = Some(tsi);
                    return signal;
                }
            }
        }

        Signal::default()
    }
}

/// Ultimate Oscillator state.
pub struct UltimateOscillatorState {
    period1: usize,
    period2: usize,
    period3: usize,
    lower: f64,
    upper: f64,
    prev_close: Option<f64>,
    bp_buffer: Vec<f64>,  // Buying Pressure
    tr_buffer: Vec<f64>,  // True Range
    idx: usize,
    count: usize,
}

impl UltimateOscillatorState {
    pub fn new(period1: usize, period2: usize, period3: usize, lower: f64, upper: f64) -> Self {
        let max_period = period1.max(period2).max(period3);
        Self {
            period1: period1.max(1),
            period2: period2.max(1),
            period3: period3.max(1),
            lower,
            upper,
            prev_close: None,
            bp_buffer: vec![0.0; max_period],
            tr_buffer: vec![0.0; max_period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        let (bp, tr) = if let Some(prev_close) = self.prev_close {
            let true_low = low.min(prev_close);
            let true_high = high.max(prev_close);
            let bp = close - true_low;
            let tr = true_high - true_low;
            (bp, tr)
        } else {
            self.prev_close = Some(close);
            return Signal::default();
        };
        self.prev_close = Some(close);

        let max_period = self.bp_buffer.len();
        if self.count < max_period {
            self.bp_buffer[self.count] = bp;
            self.tr_buffer[self.count] = tr;
            self.count += 1;
            if self.count < self.period3 {
                return Signal::default();
            }
        } else {
            self.bp_buffer[self.idx] = bp;
            self.tr_buffer[self.idx] = tr;
            self.idx = (self.idx + 1) % max_period;
        }

        // Calculate sums for each period
        let calc_avg = |period: usize| -> f64 {
            let mut bp_sum = 0.0;
            let mut tr_sum = 0.0;
            for i in 0..period {
                let buf_idx = (self.idx + max_period - 1 - i) % max_period;
                bp_sum += self.bp_buffer[buf_idx];
                tr_sum += self.tr_buffer[buf_idx];
            }
            if tr_sum > 0.0 { bp_sum / tr_sum } else { 0.0 }
        };

        let avg1 = calc_avg(self.period1);
        let avg2 = calc_avg(self.period2);
        let avg3 = calc_avg(self.period3);

        // UO = 100 * (4*Avg1 + 2*Avg2 + Avg3) / 7
        let uo = 100.0 * (4.0 * avg1 + 2.0 * avg2 + avg3) / 7.0;

        Signal {
            long: uo < self.lower,
            short: uo > self.upper,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rsi_rising() {
        let mut rsi = RsiState::new(3, 30.0, 70.0);
        assert!(!rsi.update(1.0).short);
        assert!(!rsi.update(2.0).short);
        assert!(!rsi.update(3.0).short);
        let signal = rsi.update(4.0);
        assert!(signal.short);
        assert!(!signal.long);
    }

    #[test]
    fn test_rsi_falling() {
        let mut rsi = RsiState::new(3, 30.0, 70.0);
        assert!(!rsi.update(4.0).long);
        assert!(!rsi.update(3.0).long);
        assert!(!rsi.update(2.0).long);
        let signal = rsi.update(1.0);
        assert!(signal.long);
        assert!(!signal.short);
    }

    #[test]
    fn test_macd() {
        let mut macd = MacdState::new(3, 5, 2);
        // Feed some values
        for i in 0..10 {
            macd.update(100.0 + i as f64);
        }
        // After enough data, should have valid state
        assert!(macd.current().is_some());
    }

    #[test]
    fn test_stochastic() {
        let mut stoch = StochasticState::new(5, 3, 20.0, 80.0);
        for _ in 0..10 {
            stoch.update(100.0, 95.0, 98.0);
        }
        assert!(stoch.current().is_some());
    }
}
