//! 异步任务装饰器模块
//!
//! 提供 `@run_async` 装饰器，将函数放到独立的异步任务中执行

use pyo3::prelude::*;
use pyo3::types::PyTuple;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::task::JoinHandle;

use crate::core::manager::{next_task_id, TaskType, TASK_MANAGER};
use crate::runtime::RUNTIME;

type PyObjectType = Py<PyAny>;

/// 异步任务句柄
///
/// 用于查询和控制异步执行的函数
#[pyclass]
pub struct AsyncHandle {
    task_id: u64,
    completed: Arc<AtomicBool>,
    cancelled: Arc<AtomicBool>,
    result: Arc<Mutex<Option<PyObjectType>>>,
    error: Arc<Mutex<Option<String>>>,
    #[allow(dead_code)]
    handle: Arc<Mutex<Option<JoinHandle<()>>>>,
}

impl AsyncHandle {
    /// 内部检查是否完成
    fn check_done(&self) -> bool {
        self.completed.load(Ordering::SeqCst) || self.cancelled.load(Ordering::SeqCst)
    }
}

impl Drop for AsyncHandle {
    fn drop(&mut self) {
        // 任务完成后从管理器注销
        TASK_MANAGER.unregister(self.task_id);
    }
}

#[pymethods]
impl AsyncHandle {
    /// 获取任务 ID
    ///
    /// Returns:
    ///     int: 任务唯一标识符
    #[getter]
    fn task_id(&self) -> u64 {
        self.task_id
    }

    /// 检查任务是否已完成
    ///
    /// Returns:
    ///     bool: 任务是否已完成（包括成功或失败）
    fn is_done(&self) -> bool {
        self.check_done()
    }

    /// 检查任务是否成功完成
    ///
    /// Returns:
    ///     bool: 任务是否成功完成
    fn is_completed(&self) -> bool {
        self.completed.load(Ordering::SeqCst)
    }

    /// 检查任务是否被取消
    ///
    /// Returns:
    ///     bool: 任务是否被取消
    fn is_cancelled(&self) -> bool {
        self.cancelled.load(Ordering::SeqCst)
    }

    /// 取消任务
    ///
    /// 注意：这只会标记任务为已取消，不会中断正在执行的代码
    fn cancel(&self) {
        self.cancelled.store(true, Ordering::SeqCst);
    }

    /// 获取任务结果（非阻塞）
    ///
    /// Returns:
    ///     任务返回值，如果任务未完成则返回 None
    ///
    /// Raises:
    ///     RuntimeError: 如果任务执行出错
    fn try_result(&self, py: Python<'_>) -> PyResult<Option<PyObjectType>> {
        // 使用 block_in_place 允许在 tokio runtime 内部调用
        tokio::task::block_in_place(|| {
            // 检查是否有错误
            let error_guard = RUNTIME.block_on(async { self.error.lock().await });
            if let Some(ref err) = *error_guard {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(err.clone()));
            }
            drop(error_guard);

            // 获取结果
            let result_guard = RUNTIME.block_on(async { self.result.lock().await });
            Ok(result_guard.as_ref().map(|r| r.clone_ref(py)))
        })
    }

    /// 等待任务完成并获取结果（阻塞）
    ///
    /// Args:
    ///     timeout_ms: 超时时间（毫秒），None 表示无限等待
    ///
    /// Returns:
    ///     任务返回值
    ///
    /// Raises:
    ///     TimeoutError: 如果等待超时
    ///     RuntimeError: 如果任务执行出错
    #[pyo3(signature = (timeout_ms=None))]
    fn wait(&self, py: Python<'_>, timeout_ms: Option<u64>) -> PyResult<PyObjectType> {
        let start = std::time::Instant::now();
        let timeout = timeout_ms.map(std::time::Duration::from_millis);

        loop {
            if self.check_done() {
                break;
            }

            if let Some(t) = timeout {
                if start.elapsed() >= t {
                    return Err(pyo3::exceptions::PyTimeoutError::new_err(
                        "Async task wait timed out",
                    ));
                }
            }

            // 短暂释放 GIL 让其他线程有机会执行
            py.detach(|| std::thread::sleep(std::time::Duration::from_millis(1)));
        }

        // 使用 block_in_place 允许在 tokio runtime 内部调用
        tokio::task::block_in_place(|| {
            // 检查错误
            let error_guard = RUNTIME.block_on(async { self.error.lock().await });
            if let Some(ref err) = *error_guard {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(err.clone()));
            }
            drop(error_guard);

            // 返回结果
            let result_guard = RUNTIME.block_on(async { self.result.lock().await });
            Ok(result_guard
                .as_ref()
                .map(|r| r.clone_ref(py))
                .unwrap_or_else(|| py.None().into()))
        })
    }

    fn __repr__(&self) -> String {
        let status = if self.is_cancelled() {
            "cancelled"
        } else if self.is_completed() {
            "completed"
        } else {
            "running"
        };
        format!("AsyncHandle(id={}, status={})", self.task_id, status)
    }
}

/// 异步任务装饰器
///
/// 将被装饰的函数放到独立的异步任务中执行
///
/// Example:
///     >>> @run_async
///     ... def heavy_computation(x):
///     ...     import time
///     ...     time.sleep(1)
///     ...     return x * 2
///     ...
///     >>> handle = heavy_computation(21)
///     >>> # 做其他事情...
///     >>> result = handle.wait()  # 等待结果
///     >>> print(result)  # 42
#[pyclass]
pub struct RunAsync {
    func: PyObjectType,
}

#[pymethods]
impl RunAsync {
    #[new]
    fn new(func: PyObjectType) -> Self {
        Self { func }
    }

    /// 调用包装后的函数，启动异步任务
    ///
    /// Args:
    ///     *args: 传递给被装饰函数的参数
    ///
    /// Returns:
    ///     AsyncHandle: 异步任务控制句柄
    #[pyo3(signature = (*args))]
    fn __call__(&self, py: Python<'_>, args: &Bound<'_, PyTuple>) -> PyResult<AsyncHandle> {
        let task_id = next_task_id();
        let func = self.func.clone_ref(py);
        let args: PyObjectType = args.clone().unbind().into();

        let completed = Arc::new(AtomicBool::new(false));
        let cancelled = Arc::new(AtomicBool::new(false));
        let result: Arc<Mutex<Option<PyObjectType>>> = Arc::new(Mutex::new(None));
        let error: Arc<Mutex<Option<String>>> = Arc::new(Mutex::new(None));

        let completed_clone = completed.clone();
        let cancelled_clone = cancelled.clone();
        let result_clone = result.clone();
        let error_clone = error.clone();

        // 创建一个 running 标志用于任务管理器
        let running = Arc::new(AtomicBool::new(true));
        let running_clone = running.clone();

        let handle = RUNTIME.spawn(async move {
            // 检查是否已取消或管理器请求关闭
            if cancelled_clone.load(Ordering::SeqCst) || !running_clone.load(Ordering::SeqCst) {
                completed_clone.store(true, Ordering::SeqCst);
                running_clone.store(false, Ordering::SeqCst);
                return;
            }

            // 在 Python GIL 中执行函数
            let exec_result = Python::attach(|py| {
                let args_tuple = args.bind(py).cast::<PyTuple>().unwrap();
                func.call1(py, args_tuple)
            });

            match exec_result {
                Ok(res) => {
                    let mut result_guard = result_clone.lock().await;
                    *result_guard = Some(res);
                }
                Err(e) => {
                    let mut error_guard = error_clone.lock().await;
                    *error_guard = Some(e.to_string());
                }
            }

            completed_clone.store(true, Ordering::SeqCst);
            running_clone.store(false, Ordering::SeqCst);
        });

        let handle_arc = Arc::new(Mutex::new(Some(handle)));

        // 注册到任务管理器
        TASK_MANAGER.register(
            task_id,
            running,
            handle_arc.clone(),
            TaskType::Async,
            None,
        );

        Ok(AsyncHandle {
            task_id,
            completed,
            cancelled,
            result,
            error,
            handle: handle_arc,
        })
    }

    fn __repr__(&self) -> String {
        "RunAsync(...)".to_string()
    }
}

/// 便捷函数：创建异步任务装饰器
///
/// 这个函数本身就是装饰器，直接使用 @run_async
///
/// Example:
///     >>> @run_async
///     ... def my_func():
///     ...     pass
#[pyfunction]
pub fn run_async(func: PyObjectType) -> RunAsync {
    RunAsync::new(func)
}
