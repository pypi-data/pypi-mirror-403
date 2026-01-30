/// 全局共享的 Tokio runtime 模块
///
/// 所有异步操作都应该使用这个 runtime，避免创建多个 runtime 导致冲突
use once_cell::sync::Lazy;
use tokio::runtime::Runtime;

/// 全局 Tokio runtime，被整个 crate 共享
pub static RUNTIME: Lazy<Runtime> = Lazy::new(|| {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .expect("Failed to create Tokio runtime")
});
