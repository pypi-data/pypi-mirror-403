use futures::sink::SinkExt;
use futures::stream::StreamExt;
use std::io;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::sync::mpsc::{self, UnboundedReceiver, UnboundedSender};
use tokio_socketcan::{CANFrame, CANSocket};

use crate::runtime::RUNTIME;

/// CAN 消息类型
#[derive(Debug, Clone)]
pub struct CanMessage {
    pub id: u32,
    pub data: Vec<u8>,
}

/// 异步 CAN 设备（内部使用）
struct CanDevice {
    socket: CANSocket,
}

impl CanDevice {
    async fn new(interface: &str) -> io::Result<Self> {
        let socket =
            CANSocket::open(interface).map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
        Ok(Self { socket })
    }

    async fn send(&mut self, id: u32, data: &[u8]) -> io::Result<()> {
        let frame = CANFrame::new(id, data, false, false)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidInput, e))?;
        self.socket
            .send(frame)
            .await
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
        Ok(())
    }

    async fn receive(&mut self) -> io::Result<CANFrame> {
        match self.socket.next().await {
            Some(Ok(frame)) => Ok(frame),
            Some(Err(e)) => Err(io::Error::new(io::ErrorKind::Other, e)),
            None => Err(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                "CAN socket closed",
            )),
        }
    }
}

/// 同步 CAN 设备 - 简单模式（兼容旧 API）
pub struct CanDeviceSync {
    device: Option<CanDevice>,
    interface: String,
}

impl CanDeviceSync {
    /// 创建新的 CAN 设备
    pub fn new(interface: &str) -> io::Result<Self> {
        let interface_owned = interface.to_string();
        // 使用 block_in_place 允许在 tokio runtime 内部调用
        let device = tokio::task::block_in_place(|| {
            RUNTIME.block_on(async { CanDevice::new(&interface_owned).await })
        })?;
        Ok(Self {
            device: Some(device),
            interface: interface_owned,
        })
    }

    /// 发送 CAN 帧
    pub fn send(&mut self, id: u32, data: &[u8]) -> io::Result<()> {
        if let Some(ref mut device) = self.device {
            // 使用 block_in_place 允许在 tokio runtime 内部调用
            tokio::task::block_in_place(|| {
                RUNTIME.block_on(async { device.send(id, data).await })
            })
        } else {
            Err(io::Error::new(
                io::ErrorKind::NotConnected,
                "Device not initialized",
            ))
        }
    }

    /// 接收 CAN 帧，返回 (id, data)
    pub fn receive(&mut self) -> io::Result<(u32, Vec<u8>)> {
        if let Some(ref mut device) = self.device {
            // 使用 block_in_place 允许在 tokio runtime 内部调用
            let frame = tokio::task::block_in_place(|| {
                RUNTIME.block_on(async { device.receive().await })
            })?;
            Ok((frame.id(), frame.data().to_vec()))
        } else {
            Err(io::Error::new(
                io::ErrorKind::NotConnected,
                "Device not initialized",
            ))
        }
    }

    /// 获取接口名称
    pub fn interface(&self) -> &str {
        &self.interface
    }
}

/// 异步 CAN 设备 - 高级模式（后台任务 + 通道）
pub struct CanDeviceAsync {
    interface: String,
    tx_send: UnboundedSender<CanMessage>,
    rx_recv: Arc<Mutex<UnboundedReceiver<CanMessage>>>,
    _handle: tokio::task::JoinHandle<()>,
}

impl CanDeviceAsync {
    /// 创建新的异步 CAN 设备
    ///
    /// 这会启动一个后台 Tokio 任务来处理 CAN 通信
    pub fn new(interface: &str) -> io::Result<Self> {
        let interface_owned = interface.to_string();
        let (tx_send, mut rx_send) = mpsc::unbounded_channel::<CanMessage>();
        let (tx_recv, rx_recv) = mpsc::unbounded_channel::<CanMessage>();

        let interface_clone = interface_owned.clone();

        // 在 Tokio runtime 中启动后台任务
        let handle = RUNTIME.spawn(async move {
            // 打开 CAN socket
            let mut device = match CanDevice::new(&interface_clone).await {
                Ok(dev) => dev,
                Err(e) => {
                    eprintln!("Failed to open CAN device {}: {}", interface_clone, e);
                    return;
                }
            };

            loop {
                tokio::select! {
                    // 从发送通道接收要发送的消息
                    Some(msg) = rx_send.recv() => {
                        if let Err(e) = device.send(msg.id, &msg.data).await {
                            eprintln!("Failed to send CAN frame: {}", e);
                        }
                    }

                    // 从 CAN socket 接收消息
                    result = device.receive() => {
                        match result {
                            Ok(frame) => {
                                let msg = CanMessage {
                                    id: frame.id(),
                                    data: frame.data().to_vec(),
                                };
                                // 发送到接收通道
                                if tx_recv.send(msg).is_err() {
                                    // 接收端已关闭，退出循环
                                    break;
                                }
                            }
                            Err(e) => {
                                eprintln!("Failed to receive CAN frame: {}", e);
                                tokio::time::sleep(Duration::from_millis(100)).await;
                            }
                        }
                    }
                }
            }
        });

        Ok(Self {
            interface: interface_owned,
            tx_send,
            rx_recv: Arc::new(Mutex::new(rx_recv)),
            _handle: handle,
        })
    }

    /// 非阻塞发送 CAN 帧
    pub fn send_nonblocking(&self, id: u32, data: Vec<u8>) -> io::Result<()> {
        let msg = CanMessage { id, data };
        self.tx_send
            .send(msg)
            .map_err(|e| io::Error::new(io::ErrorKind::BrokenPipe, e.to_string()))
    }

    /// 尝试接收 CAN 帧（非阻塞）
    ///
    /// 返回 None 如果没有消息可用
    pub fn try_receive(&self) -> Option<CanMessage> {
        let rx = self.rx_recv.clone();
        // 使用 block_in_place 允许在 tokio runtime 内部调用
        tokio::task::block_in_place(|| {
            RUNTIME.block_on(async {
                let mut rx = rx.lock().await;
                rx.try_recv().ok()
            })
        })
    }

    /// 接收 CAN 帧（带超时）
    ///
    /// 如果超时仍没有消息，返回 None
    pub fn receive_timeout(&self, timeout_ms: u64) -> Option<CanMessage> {
        let rx = self.rx_recv.clone();
        // 使用 block_in_place 允许在 tokio runtime 内部调用
        tokio::task::block_in_place(|| {
            RUNTIME.block_on(async {
                let mut rx = rx.lock().await;
                tokio::time::timeout(Duration::from_millis(timeout_ms), rx.recv())
                    .await
                    .ok()
                    .flatten()
            })
        })
    }

    /// 异步接收 CAN 帧（带超时）
    ///
    /// 这是真正的异步版本，可以在异步上下文中安全调用
    pub async fn receive_timeout_async(&self, timeout_ms: u64) -> Option<CanMessage> {
        let mut rx = self.rx_recv.lock().await;
        tokio::time::timeout(Duration::from_millis(timeout_ms), rx.recv())
            .await
            .ok()
            .flatten()
    }

    /// 获取接口名称
    pub fn interface(&self) -> &str {
        &self.interface
    }
}
