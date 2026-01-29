//! Trend indicators.
//!
//! Includes: ADX, CCI, Aroon, Ichimoku, SuperTrend, Parabolic SAR

use super::moving_averages::EmaState;
use super::Signal;

/// Average Directional Index (ADX) state.
pub struct AdxState {
    period: usize,
    threshold: f64,
    prev_high: Option<f64>,
    prev_low: Option<f64>,
    prev_close: Option<f64>,
    tr_ema: EmaState,
    plus_dm_ema: EmaState,
    minus_dm_ema: EmaState,
    dx_ema: EmaState,
    count: usize,
    last_atr: Option<f64>,
}

impl AdxState {
    pub fn new(period: usize, threshold: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            threshold,
            prev_high: None,
            prev_low: None,
            prev_close: None,
            tr_ema: EmaState::new(period),
            plus_dm_ema: EmaState::new(period),
            minus_dm_ema: EmaState::new(period),
            dx_ema: EmaState::new(period),
            count: 0,
            last_atr: None,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        if let (Some(prev_h), Some(prev_l), Some(prev_c)) =
            (self.prev_high, self.prev_low, self.prev_close)
        {
            // Calculate True Range
            let hl = high - low;
            let hc = (high - prev_c).abs();
            let lc = (low - prev_c).abs();
            let tr = hl.max(hc).max(lc);

            // Calculate Directional Movement
            let up_move = high - prev_h;
            let down_move = prev_l - low;

            let plus_dm = if up_move > down_move && up_move > 0.0 {
                up_move
            } else {
                0.0
            };
            let minus_dm = if down_move > up_move && down_move > 0.0 {
                down_move
            } else {
                0.0
            };

            // Update EMAs
            let tr_smooth = self.tr_ema.update(tr);
            let plus_dm_smooth = self.plus_dm_ema.update(plus_dm);
            let minus_dm_smooth = self.minus_dm_ema.update(minus_dm);

            // Store ATR for external use
            self.last_atr = tr_smooth;

            if let (Some(tr_s), Some(pdm_s), Some(mdm_s)) =
                (tr_smooth, plus_dm_smooth, minus_dm_smooth)
            {
                self.count += 1;

                // Calculate +DI and -DI
                let plus_di = if tr_s > 0.0 {
                    (pdm_s / tr_s) * 100.0
                } else {
                    0.0
                };
                let minus_di = if tr_s > 0.0 {
                    (mdm_s / tr_s) * 100.0
                } else {
                    0.0
                };

                // Calculate DX
                let di_sum = plus_di + minus_di;
                let dx = if di_sum > 0.0 {
                    ((plus_di - minus_di).abs() / di_sum) * 100.0
                } else {
                    0.0
                };

                // Calculate ADX (smoothed DX)
                if let Some(adx) = self.dx_ema.update(dx) {
                    self.prev_high = Some(high);
                    self.prev_low = Some(low);
                    self.prev_close = Some(close);

                    // Signal: Strong trend when ADX > threshold
                    // Direction determined by +DI vs -DI
                    return if adx >= self.threshold {
                        Signal {
                            long: plus_di > minus_di,
                            short: minus_di > plus_di,
                        }
                    } else {
                        Signal::default()
                    };
                }
            }
        }

        self.prev_high = Some(high);
        self.prev_low = Some(low);
        self.prev_close = Some(close);
        Signal::default()
    }

    /// Get current ADX value.
    pub fn current(&self) -> Option<f64> {
        self.dx_ema.current()
    }

    /// Get current ATR value.
    pub fn current_atr(&self) -> Option<f64> {
        self.last_atr
    }
}

/// Commodity Channel Index (CCI) state.
pub struct CciState {
    period: usize,
    lower: f64,
    upper: f64,
    tp_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl CciState {
    pub fn new(period: usize, lower: f64, upper: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            lower,
            upper,
            tp_buffer: vec![0.0; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        let typical_price = (high + low + close) / 3.0;

        if self.count < self.period {
            self.tp_buffer[self.count] = typical_price;
            self.count += 1;
            return Signal::default();
        }

        self.tp_buffer[self.idx] = typical_price;
        self.idx = (self.idx + 1) % self.period;

        // Calculate SMA of typical price
        let sma: f64 = self.tp_buffer.iter().sum::<f64>() / self.period as f64;

        // Calculate Mean Deviation
        let mean_deviation: f64 = self.tp_buffer.iter().map(|tp| (tp - sma).abs()).sum::<f64>()
            / self.period as f64;

        // CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
        let cci = if mean_deviation > 0.0 {
            (typical_price - sma) / (0.015 * mean_deviation)
        } else {
            0.0
        };

        Signal {
            long: cci < self.lower,   // Oversold
            short: cci > self.upper,  // Overbought
        }
    }

    /// Get current CCI value.
    pub fn current(&self) -> Option<f64> {
        if self.count >= self.period {
            let sma: f64 = self.tp_buffer.iter().sum::<f64>() / self.period as f64;
            let latest_tp = self.tp_buffer[(self.idx + self.period - 1) % self.period];
            let mean_deviation: f64 =
                self.tp_buffer.iter().map(|tp| (tp - sma).abs()).sum::<f64>() / self.period as f64;
            if mean_deviation > 0.0 {
                Some((latest_tp - sma) / (0.015 * mean_deviation))
            } else {
                Some(0.0)
            }
        } else {
            None
        }
    }
}

/// Aroon state.
pub struct AroonState {
    period: usize,
    threshold: f64,
    high_buffer: Vec<f64>,
    low_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl AroonState {
    pub fn new(period: usize, threshold: f64) -> Self {
        let period = period.max(2);
        Self {
            period,
            threshold,
            high_buffer: vec![0.0; period + 1],
            low_buffer: vec![0.0; period + 1],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, high: f64, low: f64) -> Signal {
        let len = self.period + 1;

        if self.count < len {
            self.high_buffer[self.count] = high;
            self.low_buffer[self.count] = low;
            self.count += 1;
            return Signal::default();
        }

        self.high_buffer[self.idx] = high;
        self.low_buffer[self.idx] = low;

        // Find periods since highest high and lowest low
        let mut highest_idx = 0;
        let mut lowest_idx = 0;
        let mut highest = f64::NEG_INFINITY;
        let mut lowest = f64::INFINITY;

        for i in 0..len {
            let buf_idx = (self.idx + len - i) % len;
            if self.high_buffer[buf_idx] >= highest {
                highest = self.high_buffer[buf_idx];
                highest_idx = i;
            }
            if self.low_buffer[buf_idx] <= lowest {
                lowest = self.low_buffer[buf_idx];
                lowest_idx = i;
            }
        }

        self.idx = (self.idx + 1) % len;

        // Aroon Up = ((period - periods since highest high) / period) * 100
        // Aroon Down = ((period - periods since lowest low) / period) * 100
        let aroon_up = ((self.period - highest_idx) as f64 / self.period as f64) * 100.0;
        let aroon_down = ((self.period - lowest_idx) as f64 / self.period as f64) * 100.0;

        // Strong uptrend: Aroon Up > threshold, Aroon Down < 100 - threshold
        // Strong downtrend: Aroon Down > threshold, Aroon Up < 100 - threshold
        Signal {
            long: aroon_up > self.threshold && aroon_down < (100.0 - self.threshold),
            short: aroon_down > self.threshold && aroon_up < (100.0 - self.threshold),
        }
    }

    /// Get current Aroon values (up, down, oscillator).
    pub fn current(&self) -> Option<(f64, f64, f64)> {
        if self.count >= self.period + 1 {
            let len = self.period + 1;
            let mut highest_idx = 0;
            let mut lowest_idx = 0;
            let mut highest = f64::NEG_INFINITY;
            let mut lowest = f64::INFINITY;

            for i in 0..len {
                let buf_idx = (self.idx + len - 1 - i) % len;
                if self.high_buffer[buf_idx] >= highest {
                    highest = self.high_buffer[buf_idx];
                    highest_idx = i;
                }
                if self.low_buffer[buf_idx] <= lowest {
                    lowest = self.low_buffer[buf_idx];
                    lowest_idx = i;
                }
            }

            let aroon_up = ((self.period - highest_idx) as f64 / self.period as f64) * 100.0;
            let aroon_down = ((self.period - lowest_idx) as f64 / self.period as f64) * 100.0;
            let oscillator = aroon_up - aroon_down;
            Some((aroon_up, aroon_down, oscillator))
        } else {
            None
        }
    }
}

/// Ichimoku Cloud state.
pub struct IchimokuState {
    tenkan_period: usize,
    kijun_period: usize,
    senkou_b_period: usize,
    high_buffer: Vec<f64>,
    low_buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl IchimokuState {
    pub fn new(tenkan: usize, kijun: usize, senkou_b: usize) -> Self {
        let max_period = tenkan.max(kijun).max(senkou_b);
        Self {
            tenkan_period: tenkan,
            kijun_period: kijun,
            senkou_b_period: senkou_b,
            high_buffer: vec![0.0; max_period],
            low_buffer: vec![0.0; max_period],
            idx: 0,
            count: 0,
        }
    }

    fn calc_line(&self, period: usize) -> Option<f64> {
        if self.count < period {
            return None;
        }

        let len = self.high_buffer.len();
        let mut highest = f64::NEG_INFINITY;
        let mut lowest = f64::INFINITY;

        for i in 0..period {
            let buf_idx = (self.idx + len - 1 - i) % len;
            highest = highest.max(self.high_buffer[buf_idx]);
            lowest = lowest.min(self.low_buffer[buf_idx]);
        }

        Some((highest + lowest) / 2.0)
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        let len = self.high_buffer.len();

        if self.count < len {
            self.high_buffer[self.count] = high;
            self.low_buffer[self.count] = low;
            self.count += 1;
        } else {
            self.high_buffer[self.idx] = high;
            self.low_buffer[self.idx] = low;
            self.idx = (self.idx + 1) % len;
        }

        let tenkan = self.calc_line(self.tenkan_period);
        let kijun = self.calc_line(self.kijun_period);
        let senkou_a = tenkan.zip(kijun).map(|(t, k)| (t + k) / 2.0);
        let senkou_b = self.calc_line(self.senkou_b_period);

        // Basic Ichimoku signals:
        // Long: Tenkan > Kijun, price above cloud
        // Short: Tenkan < Kijun, price below cloud
        if let (Some(t), Some(k), Some(sa), Some(sb)) = (tenkan, kijun, senkou_a, senkou_b) {
            let cloud_top = sa.max(sb);
            let cloud_bottom = sa.min(sb);

            Signal {
                long: t > k && close > cloud_top,
                short: t < k && close < cloud_bottom,
            }
        } else {
            Signal::default()
        }
    }

    /// Get current Ichimoku values (tenkan, kijun, senkou_a, senkou_b).
    pub fn current(&self) -> Option<(f64, f64, f64, f64)> {
        let tenkan = self.calc_line(self.tenkan_period)?;
        let kijun = self.calc_line(self.kijun_period)?;
        let senkou_a = (tenkan + kijun) / 2.0;
        let senkou_b = self.calc_line(self.senkou_b_period)?;
        Some((tenkan, kijun, senkou_a, senkou_b))
    }
}

/// SuperTrend state.
pub struct SuperTrendState {
    period: usize,
    multiplier: f64,
    prev_close: Option<f64>,
    prev_high: Option<f64>,
    prev_low: Option<f64>,
    atr_sum: f64,
    tr_buffer: Vec<f64>,
    tr_idx: usize,
    tr_count: usize,
    upper_band: f64,
    lower_band: f64,
    supertrend: f64,
    trend_direction: i8, // 1 for up, -1 for down
    last_atr: Option<f64>,
}

impl SuperTrendState {
    pub fn new(period: usize, multiplier: f64) -> Self {
        let period = period.max(1);
        Self {
            period,
            multiplier,
            prev_close: None,
            prev_high: None,
            prev_low: None,
            atr_sum: 0.0,
            tr_buffer: vec![0.0; period],
            tr_idx: 0,
            tr_count: 0,
            upper_band: 0.0,
            lower_band: 0.0,
            supertrend: 0.0,
            trend_direction: 1,
            last_atr: None,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, close: f64) -> Signal {
        // Calculate True Range
        let tr = if let Some(prev_c) = self.prev_close {
            let hl = high - low;
            let hc = (high - prev_c).abs();
            let lc = (low - prev_c).abs();
            hl.max(hc).max(lc)
        } else {
            high - low
        };

        // Update ATR calculation
        if self.tr_count < self.period {
            self.tr_buffer[self.tr_count] = tr;
            self.atr_sum += tr;
            self.tr_count += 1;
        } else {
            let old_tr = self.tr_buffer[self.tr_idx];
            self.atr_sum = self.atr_sum - old_tr + tr;
            self.tr_buffer[self.tr_idx] = tr;
            self.tr_idx = (self.tr_idx + 1) % self.period;
        }

        let atr = if self.tr_count >= self.period {
            self.atr_sum / self.period as f64
        } else {
            self.prev_close = Some(close);
            self.prev_high = Some(high);
            self.prev_low = Some(low);
            return Signal::default();
        };

        self.last_atr = Some(atr);

        let hl2 = (high + low) / 2.0;
        let basic_upper = hl2 + self.multiplier * atr;
        let basic_lower = hl2 - self.multiplier * atr;

        // Calculate final upper band
        let final_upper = if let Some(prev_c) = self.prev_close {
            if basic_upper < self.upper_band || prev_c > self.upper_band {
                basic_upper
            } else {
                self.upper_band
            }
        } else {
            basic_upper
        };

        // Calculate final lower band
        let final_lower = if let Some(prev_c) = self.prev_close {
            if basic_lower > self.lower_band || prev_c < self.lower_band {
                basic_lower
            } else {
                self.lower_band
            }
        } else {
            basic_lower
        };

        // Determine trend direction
        let prev_supertrend = self.supertrend;
        let prev_direction = self.trend_direction;

        if prev_supertrend == self.upper_band {
            self.trend_direction = if close > final_upper { 1 } else { -1 };
        } else {
            self.trend_direction = if close < final_lower { -1 } else { 1 };
        }

        // Set SuperTrend value
        self.supertrend = if self.trend_direction == 1 {
            final_lower
        } else {
            final_upper
        };

        self.upper_band = final_upper;
        self.lower_band = final_lower;
        self.prev_close = Some(close);
        self.prev_high = Some(high);
        self.prev_low = Some(low);

        // Signal on trend change
        Signal {
            long: prev_direction == -1 && self.trend_direction == 1,
            short: prev_direction == 1 && self.trend_direction == -1,
        }
    }

    /// Get current SuperTrend value and direction.
    pub fn current(&self) -> Option<(f64, i8)> {
        if self.tr_count >= self.period {
            Some((self.supertrend, self.trend_direction))
        } else {
            None
        }
    }

    /// Get current ATR value.
    pub fn current_atr(&self) -> Option<f64> {
        self.last_atr
    }
}

/// Parabolic SAR state.
pub struct ParabolicSarState {
    af_start: f64,
    af_increment: f64,
    af_max: f64,
    sar: f64,
    ep: f64,      // Extreme Point
    af: f64,      // Acceleration Factor
    is_long: bool,
    prev_high: Option<f64>,
    prev_low: Option<f64>,
    initialized: bool,
}

impl ParabolicSarState {
    pub fn new(af_start: f64, af_increment: f64, af_max: f64) -> Self {
        Self {
            af_start,
            af_increment,
            af_max,
            sar: 0.0,
            ep: 0.0,
            af: af_start,
            is_long: true,
            prev_high: None,
            prev_low: None,
            initialized: false,
        }
    }

    pub fn update(&mut self, high: f64, low: f64, _close: f64) -> Signal {
        if !self.initialized {
            if let (Some(ph), Some(pl)) = (self.prev_high, self.prev_low) {
                // Initialize based on first two bars
                self.is_long = high > ph;
                if self.is_long {
                    self.sar = pl.min(low);
                    self.ep = high;
                } else {
                    self.sar = ph.max(high);
                    self.ep = low;
                }
                self.af = self.af_start;
                self.initialized = true;
            } else {
                self.prev_high = Some(high);
                self.prev_low = Some(low);
                return Signal::default();
            }
        }

        let prev_sar = self.sar;
        let prev_is_long = self.is_long;

        // Calculate new SAR
        self.sar = prev_sar + self.af * (self.ep - prev_sar);

        // Ensure SAR doesn't penetrate prior bars
        if let (Some(ph), Some(pl)) = (self.prev_high, self.prev_low) {
            if self.is_long {
                self.sar = self.sar.min(pl).min(low);
            } else {
                self.sar = self.sar.max(ph).max(high);
            }
        }

        // Check for reversal
        let mut reversed = false;
        if self.is_long {
            if low < self.sar {
                // Reverse to short
                self.is_long = false;
                self.sar = self.ep;
                self.ep = low;
                self.af = self.af_start;
                reversed = true;
            }
        } else {
            if high > self.sar {
                // Reverse to long
                self.is_long = true;
                self.sar = self.ep;
                self.ep = high;
                self.af = self.af_start;
                reversed = true;
            }
        }

        if !reversed {
            // Update EP and AF
            if self.is_long {
                if high > self.ep {
                    self.ep = high;
                    self.af = (self.af + self.af_increment).min(self.af_max);
                }
            } else {
                if low < self.ep {
                    self.ep = low;
                    self.af = (self.af + self.af_increment).min(self.af_max);
                }
            }
        }

        self.prev_high = Some(high);
        self.prev_low = Some(low);

        // Signal on reversal
        Signal {
            long: !prev_is_long && self.is_long,
            short: prev_is_long && !self.is_long,
        }
    }

    /// Get current SAR value and direction.
    pub fn current(&self) -> Option<(f64, bool)> {
        if self.initialized {
            Some((self.sar, self.is_long))
        } else {
            None
        }
    }
}

/// Linear Regression state (for trend detection).
pub struct LinearRegressionState {
    period: usize,
    buffer: Vec<f64>,
    idx: usize,
    count: usize,
}

impl LinearRegressionState {
    pub fn new(period: usize) -> Self {
        let period = period.max(2);
        Self {
            period,
            buffer: vec![0.0; period],
            idx: 0,
            count: 0,
        }
    }

    pub fn update(&mut self, value: f64) -> Option<(f64, f64)> {
        // Returns (slope, intercept)
        if self.count < self.period {
            self.buffer[self.count] = value;
            self.count += 1;
            if self.count < self.period {
                return None;
            }
        } else {
            self.buffer[self.idx] = value;
            self.idx = (self.idx + 1) % self.period;
        }

        // Calculate linear regression
        let n = self.period as f64;
        let mut sum_x = 0.0;
        let mut sum_y = 0.0;
        let mut sum_xy = 0.0;
        let mut sum_x2 = 0.0;

        for i in 0..self.period {
            let x = i as f64;
            let buf_idx = (self.idx + i) % self.period;
            let y = self.buffer[buf_idx];
            sum_x += x;
            sum_y += y;
            sum_xy += x * y;
            sum_x2 += x * x;
        }

        let denominator = n * sum_x2 - sum_x * sum_x;
        if denominator.abs() < 1e-10 {
            return None;
        }

        let slope = (n * sum_xy - sum_x * sum_y) / denominator;
        let intercept = (sum_y - slope * sum_x) / n;

        Some((slope, intercept))
    }

    /// Get projected value at offset bars from now.
    pub fn project(&self, offset: usize) -> Option<f64> {
        if self.count < self.period {
            return None;
        }

        let n = self.period as f64;
        let mut sum_x = 0.0;
        let mut sum_y = 0.0;
        let mut sum_xy = 0.0;
        let mut sum_x2 = 0.0;

        for i in 0..self.period {
            let x = i as f64;
            let buf_idx = (self.idx + i) % self.period;
            let y = self.buffer[buf_idx];
            sum_x += x;
            sum_y += y;
            sum_xy += x * y;
            sum_x2 += x * x;
        }

        let denominator = n * sum_x2 - sum_x * sum_x;
        if denominator.abs() < 1e-10 {
            return None;
        }

        let slope = (n * sum_xy - sum_x * sum_y) / denominator;
        let intercept = (sum_y - slope * sum_x) / n;

        Some(slope * (self.period + offset) as f64 + intercept)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_adx() {
        let mut adx = AdxState::new(5, 25.0);
        for i in 0..20 {
            let base = 100.0 + i as f64;
            adx.update(base + 2.0, base - 2.0, base);
        }
        assert!(adx.current().is_some());
    }

    #[test]
    fn test_cci() {
        let mut cci = CciState::new(5, -100.0, 100.0);
        for i in 0..10 {
            let base = 100.0 + i as f64;
            cci.update(base + 1.0, base - 1.0, base);
        }
        assert!(cci.current().is_some());
    }

    #[test]
    fn test_aroon() {
        let mut aroon = AroonState::new(5, 70.0);
        for i in 0..10 {
            aroon.update(100.0 + i as f64, 99.0 + i as f64);
        }
        let (up, down, osc) = aroon.current().unwrap();
        assert!(up >= 0.0 && up <= 100.0);
        assert!(down >= 0.0 && down <= 100.0);
        assert!(osc >= -100.0 && osc <= 100.0);
    }

    #[test]
    fn test_ichimoku() {
        let mut ichi = IchimokuState::new(9, 26, 52);
        for i in 0..60 {
            let base = 100.0 + (i as f64 * 0.1);
            ichi.update(base + 1.0, base - 1.0, base);
        }
        assert!(ichi.current().is_some());
    }

    #[test]
    fn test_supertrend() {
        let mut st = SuperTrendState::new(10, 3.0);
        for i in 0..20 {
            let base = 100.0 + i as f64;
            st.update(base + 2.0, base - 2.0, base);
        }
        assert!(st.current().is_some());
    }
}
