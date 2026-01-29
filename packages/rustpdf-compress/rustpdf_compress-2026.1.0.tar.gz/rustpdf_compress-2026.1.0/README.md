# rustpdf-compress

基于 Rust 的高性能 PDF 压缩库，支持 Python 调用。

## 安装

```bash
pip install rustpdf-compress
```

## 使用方法

### 压缩文件

```python
import rustpdf_compress

# 压缩文件，返回 (原始大小, 压缩后大小, 压缩率)
original, compressed, reduction = rustpdf_compress.compress_file(
    "input.pdf",
    "output.pdf",
    level="recommended"  # extreme / recommended / low
)
print(f"压缩了 {reduction:.1f}%")
```

### 压缩字节数据

```python
import rustpdf_compress

with open("input.pdf", "rb") as f:
    data = f.read()

compressed = rustpdf_compress.compress(data, level="recommended")

with open("output.pdf", "wb") as f:
    f.write(compressed)
```

## 压缩级别

| 级别 | 说明 | 图片质量 | 缩放比例 |
|------|------|---------|---------|
| `extreme` | 极限压缩 | 30% | 50% |
| `recommended` | 推荐（默认） | 60% | 75% |
| `low` | 低压缩 | 85% | 100% |

## 特性

- 🚀 基于 Rust，性能优异
- 📦 支持 Python 3.8+
- 🖥️ 支持 macOS (ARM64) 和 Linux (x86_64)
- 🔧 三种压缩级别可选

## License

MIT
