# 编译linux，windows，macos的wheel
# 使用 --find-interpreter 自动检测并为所有可用的Python版本构建
maturin build --release --target x86_64-unknown-linux-gnu --find-interpreter
#maturin build --release --target x86_64-pc-windows-msvc --find-interpreter
#maturin build --release --target aarch64-apple-darwin --find-interpreter

# 上传到pypi
maturin upload target/wheels/cawlib-*.whl