//! Core 模块
//!
//! 提供核心的装饰器、任务管理和工具函数

pub mod manager;
pub mod task;
pub mod timer;

pub use manager::{block_all, block_until, get_task_manager, shutdown_all, PyTaskManager};
pub use task::{run_async, AsyncHandle, RunAsync};
pub use timer::{precision_timer, timer_decorator, PrecisionTimer, Timer, TimerHandle, TimerWrapper};
