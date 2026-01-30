use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[repr(u16)]
pub enum CanCtlMode {
    Idle = 0,
    Torque = 1,
    Speed = 2,
    Position = 3,
    EncoderZeroing = 4,
}

impl From<u16> for CanCtlMode {
    fn from(value: u16) -> Self {
        match value {
            0 => Self::Idle,
            1 => Self::Torque,
            2 => Self::Speed,
            3 => Self::Position,
            4 => Self::EncoderZeroing,
            _ => Self::Idle,
        }
    }
}

impl CanCtlMode {
    /// 将枚举值转换为小端字节序
    pub fn to_le_bytes(self) -> [u8; 2] {
        (self as u16).to_le_bytes()
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CanCtlProtocol {
    mode: CanCtlMode,
    data: f32,
}

impl CanCtlProtocol {
    /// 创建新的 CAN 控制协议消息
    pub fn new(mode: CanCtlMode, data: f32) -> Self {
        Self { mode, data }
    }

    /// 获取控制模式
    pub fn mode(&self) -> CanCtlMode {
        self.mode
    }

    /// 获取数据
    pub fn data(&self) -> f32 {
        self.data
    }

    /// 转换为字节数组（8字节，后2字节为保留位）
    pub fn to_bytes(&self) -> [u8; 8] {
        let mode = self.mode.to_le_bytes(); // 2 bytes
        let data = self.data.to_le_bytes(); // 4 bytes
        [
            mode[0], mode[1], // bytes 0-1: mode
            data[0], data[1], // bytes 2-3: data (part 1)
            data[2], data[3], // bytes 4-5: data (part 2)
            0x00, 0x00, // bytes 6-7: reserved/padding
        ]
    }

    /// 从字节数组创建
    pub fn from_bytes(bytes: [u8; 8]) -> Self {
        Self {
            mode: CanCtlMode::from(u16::from_le_bytes([bytes[0], bytes[1]])),
            data: f32::from_le_bytes([bytes[2], bytes[3], bytes[4], bytes[5]]),
        }
    }
}

// 实现 From trait 用于类型转换
impl From<[u8; 8]> for CanCtlProtocol {
    fn from(bytes: [u8; 8]) -> Self {
        Self::from_bytes(bytes)
    }
}

impl From<CanCtlProtocol> for [u8; 8] {
    fn from(protocol: CanCtlProtocol) -> [u8; 8] {
        protocol.to_bytes()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct WatchData {
    pub mode: CanCtlMode,
    pub target: f32,
    pub position: f32,
    pub speed: f32,
    pub current: f32,
    pub voltage: f32,
}

impl WatchData {
    pub fn new(
        mode: CanCtlMode,
        target: f32,
        position: f32,
        speed: f32,
        current: f32,
        voltage: f32,
    ) -> Self {
        Self {
            mode,
            target,
            position,
            speed,
            current,
            voltage,
        }
    }
}

impl Default for WatchData {
    fn default() -> Self {
        Self {
            mode: CanCtlMode::Idle,
            target: 0.0,
            position: 0.0,
            speed: 0.0,
            current: 0.0,
            voltage: 0.0,
        }
    }
}
