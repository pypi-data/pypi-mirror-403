//! 定时器装饰器模块
//!
//! 提供 `@timer(frequency_hz)` 普通定时器和 `@precision_timer(frequency_hz)` 高精度定时器

use pyo3::prelude::*;
use pyo3::types::PyTuple;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;
use tokio::task::JoinHandle;

use crate::core::manager::{next_task_id, TaskType, TASK_MANAGER};
use crate::runtime::RUNTIME;

type PyObjectType = Py<PyAny>;

/// Spin-wait 阈值：当剩余时间小于此值时，使用忙等待
const SPIN_THRESHOLD: Duration = Duration::from_micros(100);

/// 高精度 sleep：结合 tokio sleep 和 spin-wait
async fn precision_sleep(duration: Duration) {
    if duration <= SPIN_THRESHOLD {
        // 短时间直接 spin-wait
        spin_wait(duration);
        return;
    }

    // 大部分时间用 tokio sleep，预留 spin 时间
    let sleep_duration = duration.saturating_sub(SPIN_THRESHOLD);
    if !sleep_duration.is_zero() {
        tokio::time::sleep(sleep_duration).await;
    }

    // 最后使用 spin-wait 精确等待
    let target = Instant::now() + SPIN_THRESHOLD;
    while Instant::now() < target {
        std::hint::spin_loop();
    }
}

/// 纯 spin-wait（忙等待）
#[inline]
fn spin_wait(duration: Duration) {
    let target = Instant::now() + duration;
    while Instant::now() < target {
        std::hint::spin_loop();
    }
}

/// 定时器精度模式
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum TimerPrecision {
    /// 普通模式：使用 tokio::time::sleep，精度约 1-10ms
    Normal,
    /// 高精度模式：使用 interval + spin-wait，精度约 10-100μs
    High,
    /// 最高精度模式：独立线程 + spin-wait，精度约 1-10μs（CPU 密集）
    Realtime,
}

// ============================================================================
// TimerHandle - 定时器句柄
// ============================================================================

/// 定时器任务句柄
///
/// 用于控制定时执行的函数
#[pyclass]
pub struct TimerHandle {
    task_id: u64,
    running: Arc<AtomicBool>,
    #[allow(dead_code)]
    handle: Arc<Mutex<Option<JoinHandle<()>>>>,
    #[allow(dead_code)]
    thread_handle: Arc<std::sync::Mutex<Option<std::thread::JoinHandle<()>>>>,
    frequency_hz: f64,
    precision: TimerPrecision,
    /// 统计：实际执行次数
    tick_count: Arc<std::sync::atomic::AtomicU64>,
    /// 统计：启动时间
    start_time: Instant,
}

impl Drop for TimerHandle {
    fn drop(&mut self) {
        // 停止定时器并从管理器注销
        self.running.store(false, Ordering::SeqCst);
        TASK_MANAGER.unregister(self.task_id);
    }
}

#[pymethods]
impl TimerHandle {
    /// 获取任务 ID
    #[getter]
    fn task_id(&self) -> u64 {
        self.task_id
    }

    /// 停止定时器
    fn stop(&self) {
        self.running.store(false, Ordering::SeqCst);
    }

    /// 检查定时器是否正在运行
    fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// 获取执行频率
    fn frequency(&self) -> f64 {
        self.frequency_hz
    }

    /// 获取精度模式
    fn precision_mode(&self) -> &'static str {
        match self.precision {
            TimerPrecision::Normal => "normal",
            TimerPrecision::High => "high",
            TimerPrecision::Realtime => "realtime",
        }
    }

    /// 获取已执行的 tick 次数
    fn tick_count(&self) -> u64 {
        self.tick_count.load(Ordering::Relaxed)
    }

    /// 获取实际平均频率（Hz）
    fn actual_frequency(&self) -> f64 {
        let ticks = self.tick_count.load(Ordering::Relaxed);
        let elapsed = self.start_time.elapsed().as_secs_f64();
        if elapsed > 0.0 {
            ticks as f64 / elapsed
        } else {
            0.0
        }
    }

    /// 获取运行时间（秒）
    fn elapsed_secs(&self) -> f64 {
        self.start_time.elapsed().as_secs_f64()
    }

    fn __repr__(&self) -> String {
        format!(
            "TimerHandle(id={}, freq={:.1}Hz, actual={:.1}Hz, mode={}, ticks={}, running={})",
            self.task_id,
            self.frequency_hz,
            self.actual_frequency(),
            self.precision_mode(),
            self.tick_count(),
            self.is_running()
        )
    }
}

// ============================================================================
// Timer - 普通定时器装饰器
// ============================================================================

/// 普通定时器装饰器
///
/// 以固定频率重复执行被装饰的函数（精度约 1-10ms）
///
/// Args:
///     frequency_hz: 执行频率（Hz），例如 10.0 表示每秒执行 10 次
///
/// Example:
///     >>> @timer(10.0)  # 每秒执行 10 次
///     ... def update():
///     ...     print("tick")
///     ...
///     >>> handle = update()  # 启动定时器
///     >>> handle.stop()       # 停止定时器
#[pyclass]
pub struct Timer {
    frequency_hz: f64,
}

#[pymethods]
impl Timer {
    #[new]
    fn new(frequency_hz: f64) -> PyResult<Self> {
        if frequency_hz <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "frequency_hz must be positive",
            ));
        }
        Ok(Self { frequency_hz })
    }

    fn __call__(&self, py: Python<'_>, func: PyObjectType) -> PyResult<TimerWrapper> {
        if !func.bind(py).is_callable() {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "timer decorator requires a callable",
            ));
        }
        Ok(TimerWrapper {
            func,
            frequency_hz: self.frequency_hz,
            precision: TimerPrecision::Normal,
        })
    }
}

// ============================================================================
// PrecisionTimer - 高精度定时器装饰器
// ============================================================================

/// 高精度定时器装饰器
///
/// 以固定频率重复执行被装饰的函数（精度约 10-100μs）
///
/// Args:
///     frequency_hz: 执行频率（Hz），例如 100.0 表示每秒执行 100 次
///     realtime: 是否使用实时模式（独立线程，精度更高但 CPU 密集）
///
/// Example:
///     >>> @precision_timer(100.0)  # 每秒执行 100 次，高精度模式
///     ... def control_loop():
///     ...     pass
///     ...
///     >>> @precision_timer(1000.0, realtime=True)  # 1kHz 实时模式
///     ... def realtime_control():
///     ...     pass
#[pyclass]
pub struct PrecisionTimer {
    frequency_hz: f64,
    realtime: bool,
}

#[pymethods]
impl PrecisionTimer {
    #[new]
    #[pyo3(signature = (frequency_hz, realtime=false))]
    fn new(frequency_hz: f64, realtime: bool) -> PyResult<Self> {
        if frequency_hz <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "frequency_hz must be positive",
            ));
        }
        if frequency_hz > 10000.0 && !realtime {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "frequency > 10kHz requires realtime=True",
            ));
        }
        Ok(Self {
            frequency_hz,
            realtime,
        })
    }

    fn __call__(&self, py: Python<'_>, func: PyObjectType) -> PyResult<TimerWrapper> {
        if !func.bind(py).is_callable() {
            return Err(pyo3::exceptions::PyTypeError::new_err(
                "precision_timer decorator requires a callable",
            ));
        }
        let precision = if self.realtime {
            TimerPrecision::Realtime
        } else {
            TimerPrecision::High
        };
        Ok(TimerWrapper {
            func,
            frequency_hz: self.frequency_hz,
            precision,
        })
    }
}

// ============================================================================
// TimerWrapper - 包装后的定时器函数
// ============================================================================

/// 包装后的定时器函数
#[pyclass]
pub struct TimerWrapper {
    func: PyObjectType,
    frequency_hz: f64,
    precision: TimerPrecision,
}

#[pymethods]
impl TimerWrapper {
    #[pyo3(signature = (*args))]
    fn __call__(&self, py: Python<'_>, args: &Bound<'_, PyTuple>) -> PyResult<TimerHandle> {
        let task_id = next_task_id();
        let func = self.func.clone_ref(py);
        let args: PyObjectType = args.clone().unbind().into();
        let frequency_hz = self.frequency_hz;
        let precision = self.precision;
        let period = Duration::from_secs_f64(1.0 / frequency_hz);

        let running = Arc::new(AtomicBool::new(true));
        let tick_count = Arc::new(std::sync::atomic::AtomicU64::new(0));
        let start_time = Instant::now();

        let tokio_handle: Arc<Mutex<Option<JoinHandle<()>>>> = Arc::new(Mutex::new(None));
        let thread_handle: Arc<std::sync::Mutex<Option<std::thread::JoinHandle<()>>>> =
            Arc::new(std::sync::Mutex::new(None));

        match precision {
            TimerPrecision::Normal => {
                let running_clone = running.clone();
                let tick_count_clone = tick_count.clone();

                let handle = RUNTIME.spawn(async move {
                    let mut interval = tokio::time::interval(period);
                    interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);

                    while running_clone.load(Ordering::SeqCst) {
                        interval.tick().await;

                        if TASK_MANAGER.is_shutdown_requested() {
                            running_clone.store(false, Ordering::SeqCst);
                            break;
                        }

                        Python::attach(|py| {
                            let args_tuple = args.bind(py).cast::<PyTuple>().unwrap();
                            if let Err(e) = func.call1(py, args_tuple) {
                                eprintln!("Timer function error: {}", e);
                            }
                        });

                        tick_count_clone.fetch_add(1, Ordering::Relaxed);
                    }
                });

                *tokio_handle.blocking_lock() = Some(handle);
            }

            TimerPrecision::High => {
                let running_clone = running.clone();
                let tick_count_clone = tick_count.clone();

                let handle = RUNTIME.spawn(async move {
                    let mut next_tick = Instant::now() + period;

                    while running_clone.load(Ordering::SeqCst) {
                        if TASK_MANAGER.is_shutdown_requested() {
                            running_clone.store(false, Ordering::SeqCst);
                            break;
                        }

                        // 执行函数
                        Python::attach(|py| {
                            let args_tuple = args.bind(py).cast::<PyTuple>().unwrap();
                            if let Err(e) = func.call1(py, args_tuple) {
                                eprintln!("Timer function error: {}", e);
                            }
                        });

                        tick_count_clone.fetch_add(1, Ordering::Relaxed);

                        // 高精度等待到下一个 tick
                        let now = Instant::now();
                        if now < next_tick {
                            precision_sleep(next_tick - now).await;
                        }

                        // 计算下一个 tick 时间（防止累积漂移）
                        next_tick += period;
                        if next_tick < Instant::now() {
                            // 如果已经落后，重置到当前时间
                            next_tick = Instant::now() + period;
                        }
                    }
                });

                *tokio_handle.blocking_lock() = Some(handle);
            }

            TimerPrecision::Realtime => {
                let running_clone = running.clone();
                let tick_count_clone = tick_count.clone();
                let thread_handle_clone = thread_handle.clone();

                // 在独立线程中运行，绕过 tokio 调度
                let handle = std::thread::Builder::new()
                    .name(format!("timer-{}", task_id))
                    .spawn(move || {
                        let mut next_tick = Instant::now() + period;

                        while running_clone.load(Ordering::SeqCst) {
                            if TASK_MANAGER.is_shutdown_requested() {
                                running_clone.store(false, Ordering::SeqCst);
                                break;
                            }

                            // 执行函数
                            Python::attach(|py| {
                                let args_tuple = args.bind(py).cast::<PyTuple>().unwrap();
                                if let Err(e) = func.call1(py, args_tuple) {
                                    eprintln!("Timer function error: {}", e);
                                }
                            });

                            tick_count_clone.fetch_add(1, Ordering::Relaxed);

                            // 精确等待：大部分时间 sleep，最后 spin-wait
                            let now = Instant::now();
                            if now < next_tick {
                                let remaining = next_tick - now;
                                if remaining > SPIN_THRESHOLD {
                                    std::thread::sleep(remaining - SPIN_THRESHOLD);
                                }
                                // Spin-wait 到精确时间
                                while Instant::now() < next_tick {
                                    std::hint::spin_loop();
                                }
                            }

                            // 计算下一个 tick 时间
                            next_tick += period;
                            if next_tick < Instant::now() {
                                next_tick = Instant::now() + period;
                            }
                        }
                    })
                    .expect("Failed to spawn timer thread");

                *thread_handle_clone.lock().unwrap() = Some(handle);
            }
        }

        // 注册到任务管理器
        TASK_MANAGER.register(
            task_id,
            running.clone(),
            tokio_handle.clone(),
            TaskType::Timer,
            None,
        );

        Ok(TimerHandle {
            task_id,
            running,
            handle: tokio_handle,
            thread_handle,
            frequency_hz,
            precision,
            tick_count,
            start_time,
        })
    }

    fn __repr__(&self) -> String {
        let mode = match self.precision {
            TimerPrecision::Normal => "normal",
            TimerPrecision::High => "high",
            TimerPrecision::Realtime => "realtime",
        };
        format!("TimerWrapper(frequency={}Hz, mode={})", self.frequency_hz, mode)
    }
}

// ============================================================================
// 便捷函数
// ============================================================================

/// 普通定时器装饰器
///
/// Example:
///     >>> @timer(10.0)
///     ... def my_func():
///     ...     pass
#[pyfunction(name = "timer")]
pub fn timer_decorator(frequency_hz: f64) -> PyResult<Timer> {
    Timer::new(frequency_hz)
}

/// 高精度定时器装饰器
///
/// Args:
///     frequency_hz: 执行频率（Hz）
///     realtime: 是否使用实时模式（独立线程，CPU 密集但精度最高）
///
/// Example:
///     >>> @precision_timer(100.0)  # 高精度模式
///     ... def control():
///     ...     pass
///     ...
///     >>> @precision_timer(1000.0, realtime=True)  # 实时模式
///     ... def realtime_control():
///     ...     pass
#[pyfunction]
#[pyo3(signature = (frequency_hz, realtime=false))]
pub fn precision_timer(frequency_hz: f64, realtime: bool) -> PyResult<PrecisionTimer> {
    PrecisionTimer::new(frequency_hz, realtime)
}
