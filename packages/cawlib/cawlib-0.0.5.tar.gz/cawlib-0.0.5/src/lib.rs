use pyo3::exceptions::PyIOError;
use pyo3::prelude::*;
mod comm;
mod core;
mod instance;
mod runtime;

use comm::can::{CanDeviceAsync, CanDeviceSync};
use core::{
    block_all, block_until, get_task_manager, precision_timer, run_async, shutdown_all,
    timer_decorator, AsyncHandle, PrecisionTimer, PyTaskManager, RunAsync, Timer, TimerHandle,
    TimerWrapper,
};
use instance::motor::Motor as RustMotor;
use runtime::RUNTIME;

/// 简单模式 CAN 设备（阻塞 API）
///
/// 这个版本使用同步 API，适合简单场景
#[pyclass]
struct CanDevice {
    inner: CanDeviceSync,
}

#[pymethods]
impl CanDevice {
    /// Create a new CAN device (simple/blocking mode)
    ///
    /// Args:
    ///     interface: CAN interface name (e.g., "can0")
    #[new]
    fn new(interface: &str) -> PyResult<Self> {
        let inner = CanDeviceSync::new(interface).map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    /// Send a CAN frame (blocking)
    ///
    /// Args:
    ///     id: CAN frame ID
    ///     data: Data bytes to send (up to 8 bytes)
    fn send(&mut self, id: u32, data: Vec<u8>) -> PyResult<()> {
        self.inner
            .send(id, &data)
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// Receive a CAN frame (blocking)
    ///
    /// Returns:
    ///     Tuple of (id, data) where id is u32 and data is bytes
    fn receive(&mut self) -> PyResult<(u32, Vec<u8>)> {
        self.inner
            .receive()
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// Get the interface name
    fn interface(&self) -> &str {
        self.inner.interface()
    }
}

/// 高级异步 CAN 设备（非阻塞 API）
///
/// 使用后台 Tokio 任务处理 CAN 通信，提供非阻塞 API
#[pyclass]
struct CanDeviceNonBlocking {
    inner: CanDeviceAsync,
}

#[pymethods]
impl CanDeviceNonBlocking {
    /// Create a new CAN device with background task
    ///
    /// Args:
    ///     interface: CAN interface name (e.g., "can0")
    #[new]
    fn new(interface: &str) -> PyResult<Self> {
        let inner =
            CanDeviceAsync::new(interface).map_err(|e| PyIOError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }

    /// Send a CAN frame (non-blocking)
    ///
    /// Args:
    ///     id: CAN frame ID
    ///     data: Data bytes to send (up to 8 bytes)
    fn send(&self, id: u32, data: Vec<u8>) -> PyResult<()> {
        self.inner
            .send_nonblocking(id, data)
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// Try to receive a CAN frame (non-blocking)
    ///
    /// Returns:
    ///     Tuple of (id, data) if message available, None otherwise
    fn try_receive(&self) -> Option<(u32, Vec<u8>)> {
        self.inner.try_receive().map(|msg| (msg.id, msg.data))
    }

    /// Receive a CAN frame with timeout
    ///
    /// Args:
    ///     timeout_ms: Timeout in milliseconds
    ///
    /// Returns:
    ///     Tuple of (id, data) if message received, None if timeout
    fn receive_timeout(&self, timeout_ms: u64) -> Option<(u32, Vec<u8>)> {
        self.inner
            .receive_timeout(timeout_ms)
            .map(|msg| (msg.id, msg.data))
    }

    /// Get the interface name
    fn interface(&self) -> &str {
        self.inner.interface()
    }
}

/// 电机控制器
///
/// 用于控制通过 CAN 总线连接的电机，自动在后台接收反馈数据
#[pyclass]
struct Motor {
    inner: RustMotor,
}

#[pymethods]
impl Motor {
    /// 创建新的电机实例
    ///
    /// Args:
    ///     interface: CAN 接口名称（例如 "can0"）
    ///     control_id: 控制指令 CAN ID（可选，默认 0x123）
    ///     feedback_id: 反馈数据 CAN ID（可选，默认 0x124）
    ///
    /// Returns:
    ///     Motor 实例
    ///
    /// Example:
    ///     >>> motor = Motor("can0")
    ///     >>> motor = Motor("can0", control_id=0x200, feedback_id=0x201)
    #[new]
    #[pyo3(signature = (interface, control_id=None, feedback_id=None))]
    fn new(interface: &str, control_id: Option<u32>, feedback_id: Option<u32>) -> PyResult<Self> {
        let inner = if let (Some(ctrl_id), Some(fb_id)) = (control_id, feedback_id) {
            RustMotor::new_with_ids(interface, ctrl_id, fb_id)
                .map_err(|e| PyIOError::new_err(e.to_string()))?
        } else {
            RustMotor::new(interface).map_err(|e| PyIOError::new_err(e.to_string()))?
        };

        Ok(Self { inner })
    }

    /// 设置电机扭矩
    ///
    /// Args:
    ///     torque: 目标扭矩值（单位取决于电机控制器配置）
    ///
    /// Example:
    ///     >>> motor.set_torque(10.0)
    fn set_torque(&self, torque: f32) -> PyResult<()> {
        self.inner.set_torque(torque).map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// 设置电机速度
    ///
    /// Args:
    ///     speed: 目标速度值（单位取决于电机控制器配置）
    ///
    /// Example:
    ///     >>> motor.set_speed(1500.0)
    fn set_speed(&self, speed: f32) -> PyResult<()> {
        self.inner
            .set_speed(speed)
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// 设置电机位置
    ///
    /// Args:
    ///     position: 目标位置值（单位取决于电机控制器配置）
    ///
    /// Example:
    ///     >>> motor.set_position(90.0)
    fn set_position(&self, position: f32) -> PyResult<()> {
        self.inner
            .set_position(position)
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// 执行编码器归零
    ///
    /// 将当前位置设置为编码器的零点
    ///
    /// Example:
    ///     >>> motor.set_encoder_zeroing()
    fn set_encoder_zeroing(&self) -> PyResult<()> {
        self.inner
            .set_encoder_zeroing()
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// 设置空闲模式
    ///
    /// Example:
    ///     >>> motor.set_idle()
    fn set_idle(&self) -> PyResult<()> {
        self.inner
            .set_idle()
            .map_err(|e| PyIOError::new_err(e.to_string()))
    }

    /// 获取当前的监控数据
    ///
    /// Returns:
    ///     字典包含: mode, target, position, speed, current, voltage
    ///
    /// Example:
    ///     >>> data = motor.get_watch_data()
    ///     >>> print(f"Speed: {data['speed']}, Position: {data['position']}")
    fn get_watch_data(&self) -> PyResult<pyo3::Py<pyo3::types::PyDict>> {
        use pyo3::Python;

        // 使用 block_in_place 允许在 tokio runtime 内部阻塞
        // 这样在定时器回调中调用此函数也不会 panic
        let watch_data = tokio::task::block_in_place(|| {
            RUNTIME.block_on(async { self.inner.get_watch_data().await })
        });

        Python::attach(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("mode", format!("{:?}", watch_data.mode))?;
            dict.set_item("target", watch_data.target)?;
            dict.set_item("position", watch_data.position)?;
            dict.set_item("speed", watch_data.speed)?;
            dict.set_item("current", watch_data.current)?;
            dict.set_item("voltage", watch_data.voltage)?;
            Ok(dict.unbind())
        })
    }

    /// 获取控制 CAN ID
    fn control_id(&self) -> u32 {
        self.inner.control_id()
    }

    /// 获取反馈 CAN ID
    fn feedback_id(&self) -> u32 {
        self.inner.feedback_id()
    }

    /// 获取电机描述信息
    fn __repr__(&self) -> String {
        format!(
            "Motor(control_id=0x{:03X}, feedback_id=0x{:03X})",
            self.inner.control_id(),
            self.inner.feedback_id()
        )
    }
}

/// A Python module implemented in Rust.
#[pymodule]
mod cawlib {
    #[pymodule_export]
    use super::{
        AsyncHandle, CanDevice, CanDeviceNonBlocking, Motor, PrecisionTimer, PyTaskManager,
        RunAsync, Timer, TimerHandle, TimerWrapper,
    };

    /// 普通定时器装饰器（精度约 1-10ms）
    ///
    /// 以固定频率重复执行被装饰的函数
    ///
    /// Args:
    ///     frequency_hz: 执行频率（Hz）
    ///
    /// Example:
    ///     >>> @timer(10.0)  # 每秒执行 10 次
    ///     ... def update():
    ///     ...     print("tick")
    ///     ...
    ///     >>> handle = update()  # 启动定时器
    ///     >>> handle.stop()       # 停止定时器
    #[pymodule_export]
    use super::timer_decorator;

    /// 高精度定时器装饰器（精度约 10-100μs）
    ///
    /// Args:
    ///     frequency_hz: 执行频率（Hz）
    ///     realtime: 是否使用实时模式（独立线程，精度最高但 CPU 密集）
    ///
    /// Example:
    ///     >>> @precision_timer(100.0)  # 高精度模式
    ///     ... def control():
    ///     ...     pass
    ///     ...
    ///     >>> @precision_timer(1000.0, realtime=True)  # 1kHz 实时模式
    ///     ... def realtime_control():
    ///     ...     pass
    #[pymodule_export]
    use super::precision_timer;

    /// 异步任务装饰器
    ///
    /// 将被装饰的函数放到独立的异步任务中执行
    ///
    /// Example:
    ///     >>> @run_async
    ///     ... def heavy_task(x):
    ///     ...     import time
    ///     ...     time.sleep(1)
    ///     ...     return x * 2
    ///     ...
    ///     >>> handle = heavy_task(21)
    ///     >>> result = handle.wait()  # 等待结果: 42
    #[pymodule_export]
    use super::run_async;

    /// 获取全局任务管理器
    ///
    /// Returns:
    ///     TaskManager: 全局任务管理器实例
    ///
    /// Example:
    ///     >>> manager = get_task_manager()
    ///     >>> print(manager.running_count)
    #[pymodule_export]
    use super::get_task_manager;

    /// 优雅关闭所有任务
    ///
    /// Args:
    ///     timeout_ms: 超时时间（毫秒），None 表示无限等待
    ///
    /// Returns:
    ///     bool: 如果所有任务完成返回 True，超时返回 False
    ///
    /// Example:
    ///     >>> shutdown_all(timeout_ms=5000)
    #[pymodule_export]
    use super::shutdown_all;

    /// 阻塞等待系统退出信号，然后优雅关闭所有任务
    ///
    /// 此函数会阻塞当前线程，直到收到系统退出信号（SIGINT/Ctrl+C 或 SIGTERM），
    /// 然后自动执行优雅关闭。
    ///
    /// Args:
    ///     timeout_ms: 收到信号后等待任务完成的超时时间（毫秒）
    ///
    /// Returns:
    ///     str: 收到的信号名称
    ///
    /// Example:
    ///     >>> handle = my_timer()
    ///     >>> signal = block_all(timeout_ms=5000)  # 阻塞直到 Ctrl+C
    ///     >>> print(f"Received {signal}")
    #[pymodule_export]
    use super::block_all;

    /// 阻塞等待指定时间或退出信号，然后优雅关闭
    ///
    /// Args:
    ///     wait_ms: 最长等待时间（毫秒），None 表示无限等待
    ///     shutdown_timeout_ms: 关闭时等待任务完成的超时时间（毫秒）
    ///
    /// Returns:
    ///     tuple: (原因, 是否成功关闭)
    ///
    /// Example:
    ///     >>> reason, success = block_until(wait_ms=10000)  # 最多运行 10 秒
    #[pymodule_export]
    use super::block_until;
}
