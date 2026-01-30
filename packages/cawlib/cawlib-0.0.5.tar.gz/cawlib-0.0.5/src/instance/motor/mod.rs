pub mod protocol;

use tokio::sync::Mutex;
use tokio::task::JoinHandle;

use crate::{
    comm::{can::CanDeviceAsync, transmit::CanReceiver},
    instance::motor::protocol::{CanCtlMode, CanCtlProtocol, WatchData},
    runtime::RUNTIME,
};
use std::{io, sync::Arc};

/// CAN ID 配置
const MOTOR_CONTROL_ID: u32 = 0x123; // 控制指令 ID
const MOTOR_FEEDBACK_ID: u32 = 0x124; // 反馈数据 ID

pub struct Motor {
    can_device: Arc<CanDeviceAsync>,
    watch_data: Arc<Mutex<WatchData>>,
    receive_task_handle: Option<JoinHandle<()>>,
    control_id: u32,
    feedback_id: u32,
}

impl Motor {
    /// 创建新的电机实例
    ///
    /// # Arguments
    /// * `interface` - CAN 接口名称（如 "can0"）
    ///
    /// # Returns
    /// * `Ok(Motor)` - 成功创建的电机实例
    /// * `Err(io::Error)` - 创建失败
    pub fn new(interface: &str) -> Result<Self, io::Error> {
        Self::new_with_ids(interface, MOTOR_CONTROL_ID, MOTOR_FEEDBACK_ID)
    }

    /// 创建新的电机实例（指定 CAN ID）
    ///
    /// # Arguments
    /// * `interface` - CAN 接口名称
    /// * `control_id` - 控制指令 CAN ID
    /// * `feedback_id` - 反馈数据 CAN ID
    pub fn new_with_ids(
        interface: &str,
        control_id: u32,
        feedback_id: u32,
    ) -> Result<Self, io::Error> {
        let can_device = Arc::new(CanDeviceAsync::new(interface)?);
        let watch_data = Arc::new(Mutex::new(WatchData::default()));
        let receive_task_handle =
            Self::start_receive_task(watch_data.clone(), can_device.clone(), feedback_id);

        Ok(Self {
            can_device,
            watch_data,
            receive_task_handle: Some(receive_task_handle),
            control_id,
            feedback_id,
        })
    }

    /// 启动后台接收任务
    fn start_receive_task(
        watch_data: Arc<Mutex<WatchData>>,
        can_device: Arc<CanDeviceAsync>,
        feedback_id: u32,
    ) -> JoinHandle<()> {
        RUNTIME.spawn(async move {
            let mut can_receiver = CanReceiver::new(feedback_id as u16);

            loop {
                // 接收 CAN 消息（100ms 超时）
                // 注意：不再需要获取 Mutex 锁，因为 CanDeviceAsync 内部已经是线程安全的
                let message = can_device.receive_timeout_async(100).await;

                if let Some(message) = message {
                    // 只处理反馈 ID 的消息
                    if message.id != feedback_id {
                        continue;
                    }
                    // 转换 Vec<u8> 为 [u8; 8]
                    if message.data.len() != 8 {
                        eprintln!(
                            "Warning: Received CAN message with invalid length: {}",
                            message.data.len()
                        );
                        continue;
                    }
                    let mut data_array = [0u8; 8];
                    data_array.copy_from_slice(&message.data[..8]);

                    // 尝试解析 WatchData
                    match can_receiver.receive::<WatchData>(data_array) {
                        Ok(received_watch_data) => {
                            // 更新 watch_data
                            let mut watch_data = watch_data.lock().await;
                            *watch_data = received_watch_data;
                        }
                        Err(crate::comm::transmit::ReceiveError::Incomplete) => {
                            // 数据不完整，继续接收
                        }
                        Err(e) => {
                            eprintln!("Failed to parse WatchData: {:?}", e);
                        }
                    }
                }
            }
        })
    }

    /// 获取当前的 watch_data（克隆）
    pub async fn get_watch_data(&self) -> WatchData {
        *self.watch_data.lock().await
    }

    /// 设置扭矩
    pub fn set_torque(&self, value: f32) -> Result<(), io::Error> {
        let protocol = CanCtlProtocol::new(CanCtlMode::Torque, value);
        self.can_device
            .send_nonblocking(self.control_id, protocol.to_bytes().to_vec())
    }

    /// 设置速度
    pub fn set_speed(&self, value: f32) -> Result<(), io::Error> {
        let protocol = CanCtlProtocol::new(CanCtlMode::Speed, value);
        self.can_device
            .send_nonblocking(self.control_id, protocol.to_bytes().to_vec())
    }

    /// 设置位置
    pub fn set_position(&self, value: f32) -> Result<(), io::Error> {
        let protocol = CanCtlProtocol::new(CanCtlMode::Position, value);
        self.can_device
            .send_nonblocking(self.control_id, protocol.to_bytes().to_vec())
    }

    /// 执行编码器归零
    pub fn set_encoder_zeroing(&self) -> Result<(), io::Error> {
        let protocol = CanCtlProtocol::new(CanCtlMode::EncoderZeroing, 0.0);
        self.can_device
            .send_nonblocking(self.control_id, protocol.to_bytes().to_vec())
    }

    /// 设置空闲模式
    pub fn set_idle(&self) -> Result<(), io::Error> {
        let protocol = CanCtlProtocol::new(CanCtlMode::Idle, 0.0);
        self.can_device
            .send_nonblocking(self.control_id, protocol.to_bytes().to_vec())
    }

    /// 获取控制 CAN ID
    pub fn control_id(&self) -> u32 {
        self.control_id
    }

    /// 获取反馈 CAN ID
    pub fn feedback_id(&self) -> u32 {
        self.feedback_id
    }
}

impl Drop for Motor {
    fn drop(&mut self) {
        // 停止接收任务
        if let Some(handle) = self.receive_task_handle.take() {
            handle.abort();
        }
    }
}
