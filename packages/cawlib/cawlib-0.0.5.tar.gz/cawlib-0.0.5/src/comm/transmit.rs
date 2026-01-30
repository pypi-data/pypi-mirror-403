use serde::de::DeserializeOwned;

#[derive(Copy, Clone, Default)]
pub struct TransmitData {
    flag: u8,
    block_info: u8,
    data: [u8; 6],
}

impl From<[u8; 8]> for TransmitData {
    fn from(data: [u8; 8]) -> Self {
        Self {
            flag: data[0],
            block_info: data[1],
            data: data[2..8]
                .try_into()
                .expect("Slice length must be 6 for conversion to [u8; 6]"),
        }
    }
}

impl From<TransmitData> for [u8; 8] {
    fn from(val: TransmitData) -> [u8; 8] {
        [
            val.flag,
            val.block_info,
            val.data[0],
            val.data[1],
            val.data[2],
            val.data[3],
            val.data[4],
            val.data[5],
        ]
    }
}

#[derive(Debug)]
pub enum ReceiveError {
    Busy,
    Incomplete,
    DeserializationFailed,
    TooLarge,
    ReceiveFailed,
}

pub struct CanReceiver {
    rx_id: u16,
    blocks: [TransmitData; 10],
    read_index: usize,
    total_size: usize,
    total_blocks: usize,
}

impl CanReceiver {
    pub fn new(rx_id: u16) -> Self {
        Self {
            rx_id,
            blocks: [TransmitData::default(); 10],
            read_index: 0,
            total_size: 0,
            total_blocks: 0,
        }
    }

    fn reset(&mut self) {
        self.read_index = 0;
        self.total_size = 0;
        self.total_blocks = 0;
    }

    pub fn receive<T: DeserializeOwned>(&mut self, data: [u8; 8]) -> Result<T, ReceiveError> {
        if data[0] == 0xff {
            self.blocks[0] = TransmitData::from(data);
            self.read_index = 1;
            self.total_size = data[1] as usize;

            // 检查大小是否超出缓冲区
            if self.total_size > 60 {
                self.reset();
                return Err(ReceiveError::TooLarge);
            }

            self.total_blocks = (self.total_size + 5) / 6; // 等价于 ceil(total_size / 6)
        } else if data[0] == 0xfe {
            if data[1] as usize != self.read_index {
                self.reset();
                return Err(ReceiveError::ReceiveFailed);
            }
            self.blocks[self.read_index] = TransmitData::from(data);
            self.read_index += 1;
        } else {
            self.reset();
            return Err(ReceiveError::ReceiveFailed);
        }

        if self.read_index == self.total_blocks {
            // 使用固定大小缓冲区：10 blocks * 6 bytes = 60 bytes
            let mut buffer = [0u8; 60];

            // 复制所有块的数据
            for i in 0..self.total_blocks {
                let start = i * 6;
                let end = core::cmp::min(start + 6, self.total_size);
                let len = end - start;
                buffer[start..end].copy_from_slice(&self.blocks[i].data[..len]);
            }
            let result: T = postcard::from_bytes(&buffer[..self.total_size])
                .map_err(|_| ReceiveError::DeserializationFailed)?;
            self.reset();
            Ok(result)
        } else {
            Err(ReceiveError::Incomplete)
        }
    }
}
