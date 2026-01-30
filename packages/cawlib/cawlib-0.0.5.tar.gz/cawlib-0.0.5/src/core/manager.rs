//! 任务管理器模块
//!
//! 提供统一的任务管理，支持优雅关闭所有 timer 和 async task

use once_cell::sync::Lazy;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, RwLock};
use tokio::task::JoinHandle;

use crate::runtime::RUNTIME;

/// 全局任务 ID 计数器
static TASK_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

/// 生成唯一的任务 ID
pub fn next_task_id() -> u64 {
    TASK_ID_COUNTER.fetch_add(1, Ordering::SeqCst)
}

/// 任务类型
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum TaskType {
    Timer,
    Async,
}

/// 内部任务条目
struct TaskEntry {
    running: Arc<AtomicBool>,
    #[allow(dead_code)]
    handle: Arc<tokio::sync::Mutex<Option<JoinHandle<()>>>>,
    task_type: TaskType,
    #[allow(dead_code)]
    name: Option<String>,
}

/// 全局任务管理器
pub struct TaskManager {
    tasks: RwLock<HashMap<u64, TaskEntry>>,
    shutdown_flag: AtomicBool,
}

impl TaskManager {
    /// 创建新的任务管理器
    pub fn new() -> Self {
        Self {
            tasks: RwLock::new(HashMap::new()),
            shutdown_flag: AtomicBool::new(false),
        }
    }

    /// 检查是否已请求关闭
    pub fn is_shutdown_requested(&self) -> bool {
        self.shutdown_flag.load(Ordering::SeqCst)
    }

    /// 注册任务
    pub fn register(
        &self,
        task_id: u64,
        running: Arc<AtomicBool>,
        handle: Arc<tokio::sync::Mutex<Option<JoinHandle<()>>>>,
        task_type: TaskType,
        name: Option<String>,
    ) {
        let mut tasks = self.tasks.write().unwrap();
        tasks.insert(
            task_id,
            TaskEntry {
                running,
                handle,
                task_type,
                name,
            },
        );
    }

    /// 注销任务
    pub fn unregister(&self, task_id: u64) {
        let mut tasks = self.tasks.write().unwrap();
        tasks.remove(&task_id);
    }

    /// 获取运行中的任务数量
    pub fn running_count(&self) -> usize {
        let tasks = self.tasks.read().unwrap();
        tasks.values().filter(|t| t.running.load(Ordering::SeqCst)).count()
    }

    /// 获取所有任务数量
    pub fn total_count(&self) -> usize {
        let tasks = self.tasks.read().unwrap();
        tasks.len()
    }

    /// 获取运行中的定时器数量
    pub fn timer_count(&self) -> usize {
        let tasks = self.tasks.read().unwrap();
        tasks
            .values()
            .filter(|t| t.task_type == TaskType::Timer && t.running.load(Ordering::SeqCst))
            .count()
    }

    /// 获取运行中的异步任务数量
    pub fn async_task_count(&self) -> usize {
        let tasks = self.tasks.read().unwrap();
        tasks
            .values()
            .filter(|t| t.task_type == TaskType::Async && t.running.load(Ordering::SeqCst))
            .count()
    }

    /// 停止所有任务
    pub fn stop_all(&self) {
        self.shutdown_flag.store(true, Ordering::SeqCst);

        let tasks = self.tasks.read().unwrap();
        for entry in tasks.values() {
            entry.running.store(false, Ordering::SeqCst);
        }
    }

    /// 等待所有任务完成
    pub fn wait_all(&self, timeout_ms: Option<u64>) -> bool {
        let start = std::time::Instant::now();
        let timeout = timeout_ms.map(std::time::Duration::from_millis);

        loop {
            if self.running_count() == 0 {
                return true;
            }

            if let Some(t) = timeout {
                if start.elapsed() >= t {
                    return false;
                }
            }

            std::thread::sleep(std::time::Duration::from_millis(10));
        }
    }

    /// 优雅关闭：停止所有任务并等待完成
    pub fn shutdown(&self, timeout_ms: Option<u64>) -> bool {
        self.stop_all();
        self.wait_all(timeout_ms)
    }

    /// 重置关闭标志（用于重新启动任务）
    #[allow(dead_code)]
    pub fn reset_shutdown_flag(&self) {
        self.shutdown_flag.store(false, Ordering::SeqCst);
    }

    /// 清理已完成的任务
    pub fn cleanup(&self) {
        let mut tasks = self.tasks.write().unwrap();
        tasks.retain(|_, entry| entry.running.load(Ordering::SeqCst));
    }

    /// 获取任务状态摘要
    pub fn status_summary(&self) -> TaskStatusSummary {
        let tasks = self.tasks.read().unwrap();
        let mut running_timers = 0;
        let mut running_tasks = 0;
        let mut stopped = 0;

        for entry in tasks.values() {
            if entry.running.load(Ordering::SeqCst) {
                match entry.task_type {
                    TaskType::Timer => running_timers += 1,
                    TaskType::Async => running_tasks += 1,
                }
            } else {
                stopped += 1;
            }
        }

        TaskStatusSummary {
            running_timers,
            running_tasks,
            stopped,
            total: tasks.len(),
        }
    }
}

impl Default for TaskManager {
    fn default() -> Self {
        Self::new()
    }
}

/// 任务状态摘要
#[derive(Clone, Debug)]
pub struct TaskStatusSummary {
    pub running_timers: usize,
    pub running_tasks: usize,
    pub stopped: usize,
    pub total: usize,
}

/// 全局任务管理器实例
pub static TASK_MANAGER: Lazy<TaskManager> = Lazy::new(TaskManager::new);

// ============================================================================
// Python 绑定
// ============================================================================

/// Python 可访问的任务管理器
#[pyclass(name = "TaskManager")]
pub struct PyTaskManager;

#[pymethods]
impl PyTaskManager {
    #[new]
    fn new() -> Self {
        Self
    }

    /// 获取运行中的任务数量
    ///
    /// Returns:
    ///     int: 运行中的任务数量
    #[getter]
    fn running_count(&self) -> usize {
        TASK_MANAGER.running_count()
    }

    /// 获取所有任务数量
    ///
    /// Returns:
    ///     int: 所有任务数量
    #[getter]
    fn total_count(&self) -> usize {
        TASK_MANAGER.total_count()
    }

    /// 获取运行中的定时器数量
    ///
    /// Returns:
    ///     int: 运行中的定时器数量
    #[getter]
    fn timer_count(&self) -> usize {
        TASK_MANAGER.timer_count()
    }

    /// 获取运行中的异步任务数量
    ///
    /// Returns:
    ///     int: 运行中的异步任务数量
    #[getter]
    fn async_task_count(&self) -> usize {
        TASK_MANAGER.async_task_count()
    }

    /// 停止所有任务
    ///
    /// Example:
    ///     >>> manager.stop_all()
    fn stop_all(&self) {
        TASK_MANAGER.stop_all();
    }

    /// 等待所有任务完成
    ///
    /// Args:
    ///     timeout_ms: 超时时间（毫秒），None 表示无限等待
    ///
    /// Returns:
    ///     bool: 如果所有任务完成返回 True，超时返回 False
    ///
    /// Example:
    ///     >>> success = manager.wait_all(timeout_ms=5000)
    #[pyo3(signature = (timeout_ms=None))]
    fn wait_all(&self, py: Python<'_>, timeout_ms: Option<u64>) -> bool {
        py.detach(|| TASK_MANAGER.wait_all(timeout_ms))
    }

    /// 优雅关闭所有任务
    ///
    /// 先停止所有任务，然后等待它们完成
    ///
    /// Args:
    ///     timeout_ms: 超时时间（毫秒），None 表示无限等待
    ///
    /// Returns:
    ///     bool: 如果所有任务完成返回 True，超时返回 False
    ///
    /// Example:
    ///     >>> success = manager.shutdown(timeout_ms=5000)
    #[pyo3(signature = (timeout_ms=None))]
    fn shutdown(&self, py: Python<'_>, timeout_ms: Option<u64>) -> bool {
        py.detach(|| TASK_MANAGER.shutdown(timeout_ms))
    }

    /// 清理已完成的任务
    ///
    /// Example:
    ///     >>> manager.cleanup()
    fn cleanup(&self) {
        TASK_MANAGER.cleanup();
    }

    /// 获取任务状态
    ///
    /// Returns:
    ///     dict: 包含 running_timers, running_tasks, stopped, total
    fn status(&self) -> pyo3::Py<pyo3::types::PyDict> {
        let summary = TASK_MANAGER.status_summary();
        Python::attach(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("running_timers", summary.running_timers).unwrap();
            dict.set_item("running_tasks", summary.running_tasks).unwrap();
            dict.set_item("stopped", summary.stopped).unwrap();
            dict.set_item("total", summary.total).unwrap();
            dict.unbind()
        })
    }

    fn __repr__(&self) -> String {
        let summary = TASK_MANAGER.status_summary();
        format!(
            "TaskManager(timers={}, tasks={}, stopped={}, total={})",
            summary.running_timers, summary.running_tasks, summary.stopped, summary.total
        )
    }
}

/// 获取全局任务管理器
///
/// Returns:
///     TaskManager: 全局任务管理器实例
///
/// Example:
///     >>> manager = get_task_manager()
///     >>> print(manager.running_count)
#[pyfunction]
pub fn get_task_manager() -> PyTaskManager {
    PyTaskManager
}

/// 优雅关闭所有任务的便捷函数
///
/// Args:
///     timeout_ms: 超时时间（毫秒），None 表示无限等待
///
/// Returns:
///     bool: 如果所有任务完成返回 True，超时返回 False
///
/// Example:
///     >>> shutdown_all(timeout_ms=5000)
#[pyfunction]
#[pyo3(signature = (timeout_ms=None))]
pub fn shutdown_all(py: Python<'_>, timeout_ms: Option<u64>) -> bool {
    py.detach(|| TASK_MANAGER.shutdown(timeout_ms))
}

/// 阻塞等待系统退出信号
///
/// 此函数会阻塞当前线程，直到收到系统退出信号（SIGINT/Ctrl+C 或 SIGTERM），
/// 然后自动执行优雅关闭，停止所有定时器和任务。
///
/// Args:
///     timeout_ms: 收到信号后，等待任务完成的超时时间（毫秒），None 表示无限等待
///
/// Returns:
///     str: 收到的信号名称 ("SIGINT", "SIGTERM", 或 "unknown")
///
/// Example:
///     >>> # 启动定时器和任务
///     >>> handle = my_timer()
///     >>>
///     >>> # 阻塞等待 Ctrl+C，收到后自动关闭所有任务
///     >>> signal = block_all(timeout_ms=5000)
///     >>> print(f"Received {signal}, all tasks stopped")
#[pyfunction]
#[pyo3(signature = (timeout_ms=None))]
pub fn block_all(py: Python<'_>, timeout_ms: Option<u64>) -> PyResult<String> {
    // 在释放 GIL 的情况下等待信号
    let signal_name = py.detach(|| {
        RUNTIME.block_on(async {
            let signal_name = wait_for_shutdown_signal().await;

            // 打印信号信息
            eprintln!("\n[cawlib] Received {}, initiating graceful shutdown...", signal_name);

            // 执行优雅关闭
            TASK_MANAGER.stop_all();

            signal_name
        })
    });

    // 等待所有任务完成
    let success = py.detach(|| TASK_MANAGER.wait_all(timeout_ms));

    if success {
        eprintln!("[cawlib] All tasks stopped successfully");
    } else {
        eprintln!("[cawlib] Shutdown timed out, some tasks may still be running");
    }

    // 清除 Python 的待处理中断信号，防止抛出 KeyboardInterrupt
    // 因为我们已经正确处理了信号
    unsafe {
        if pyo3::ffi::PyErr_CheckSignals() == -1 {
            pyo3::ffi::PyErr_Clear();
        }
    }

    Ok(signal_name)
}

/// 等待系统退出信号（内部异步函数）
async fn wait_for_shutdown_signal() -> String {
    #[cfg(unix)]
    {
        use tokio::signal::unix::{signal, SignalKind};

        let mut sigint = signal(SignalKind::interrupt()).expect("Failed to register SIGINT handler");
        let mut sigterm = signal(SignalKind::terminate()).expect("Failed to register SIGTERM handler");

        tokio::select! {
            _ = sigint.recv() => "SIGINT".to_string(),
            _ = sigterm.recv() => "SIGTERM".to_string(),
        }
    }

    #[cfg(windows)]
    {
        use tokio::signal::ctrl_c;

        ctrl_c().await.expect("Failed to listen for Ctrl+C");
        "CTRL_C".to_string()
    }
}

/// 阻塞等待指定时间或直到收到退出信号
///
/// 此函数会阻塞当前线程，直到：
/// 1. 收到系统退出信号（SIGINT/Ctrl+C 或 SIGTERM）
/// 2. 或者超过指定的等待时间
///
/// 无论哪种情况，都会执行优雅关闭。
///
/// Args:
///     wait_ms: 最长等待时间（毫秒），None 表示无限等待
///     shutdown_timeout_ms: 关闭时等待任务完成的超时时间（毫秒）
///
/// Returns:
///     tuple: (原因, 是否成功关闭) - 原因为 "signal:SIGINT"、"signal:SIGTERM"、"timeout" 之一
///
/// Example:
///     >>> # 最多运行 10 秒，或者收到 Ctrl+C
///     >>> reason, success = block_until(wait_ms=10000, shutdown_timeout_ms=5000)
///     >>> print(f"Stopped: {reason}, clean shutdown: {success}")
#[pyfunction]
#[pyo3(signature = (wait_ms=None, shutdown_timeout_ms=None))]
pub fn block_until(
    py: Python<'_>,
    wait_ms: Option<u64>,
    shutdown_timeout_ms: Option<u64>,
) -> PyResult<(String, bool)> {
    let (reason, success) = py.detach(|| {
        RUNTIME.block_on(async {
            let reason = if let Some(ms) = wait_ms {
                let timeout = std::time::Duration::from_millis(ms);

                tokio::select! {
                    signal = wait_for_shutdown_signal() => {
                        format!("signal:{}", signal)
                    }
                    _ = tokio::time::sleep(timeout) => {
                        "timeout".to_string()
                    }
                }
            } else {
                let signal = wait_for_shutdown_signal().await;
                format!("signal:{}", signal)
            };

            eprintln!("\n[cawlib] Stopping (reason: {}), initiating graceful shutdown...", reason);

            // 执行优雅关闭
            TASK_MANAGER.stop_all();
            let success = TASK_MANAGER.wait_all(shutdown_timeout_ms);

            if success {
                eprintln!("[cawlib] All tasks stopped successfully");
            } else {
                eprintln!("[cawlib] Shutdown timed out, some tasks may still be running");
            }

            (reason, success)
        })
    });

    // 如果是因为信号退出，清除 Python 的待处理中断信号
    if reason.starts_with("signal:") {
        unsafe {
            if pyo3::ffi::PyErr_CheckSignals() == -1 {
                pyo3::ffi::PyErr_Clear();
            }
        }
    }

    Ok((reason, success))
}
