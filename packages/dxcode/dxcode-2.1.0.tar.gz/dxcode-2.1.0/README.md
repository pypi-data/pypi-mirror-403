# dxcode - Python 实现

带有 `dx` 前缀的自定义编码算法的 Python 实现。

## 安装

```bash
pip install dxcode
```

或从源码安装：

```bash
git clone https://github.com/dogxiii/dxcode.git
cd dxcode/implementations/python
pip install -e .
```

## 使用方法

### 基本使用

```python
from dxcode import dx_encode, dx_decode, is_dx_encoded

# 编码字符串
encoded = dx_encode('你好，Dogxi！')
print(encoded)  # dxXXXX...

# 解码
decoded = dx_decode(encoded)
print(decoded)  # 你好，Dogxi！

# 检查是否为 DX 编码
print(is_dx_encoded(encoded))  # True
print(is_dx_encoded('hello'))   # False
```

### 编码字节数据

```python
from dxcode import dx_encode, dx_decode

# 编码字节
data = b'\x00\x01\x02\xfe\xff'
encoded = dx_encode(data)
print(encoded)

# 解码为字节
decoded = dx_decode(encoded, as_bytes=True)
print(decoded)  # b'\x00\x01\x02\xfe\xff'
```

### 处理文件

```python
from dxcode import dx_encode, dx_decode

# 编码文件内容
with open('secret.txt', 'rb') as f:
    encoded = dx_encode(f.read())

# 保存编码后的内容
with open('secret.dx', 'w') as f:
    f.write(encoded)

# 解码文件
with open('secret.dx', 'r') as f:
    decoded = dx_decode(f.read(), as_bytes=True)

with open('secret_decoded.txt', 'wb') as f:
    f.write(decoded)
```

## API 参考

### `dx_encode(data)`

将数据编码为 DX 格式。

**参数：**

- `data`: `str | bytes | bytearray` - 要编码的数据

**返回值：**

- `str` - 以 `dx` 为前缀的编码字符串

**示例：**

```python
dx_encode('Hello')      # 字符串
dx_encode(b'\x00\x01')  # 字节
```

### `dx_decode(encoded, as_bytes=False)`

将 DX 编码的字符串解码。

**参数：**

- `encoded`: `str` - DX 编码的字符串（必须以 `dx` 开头）
- `as_bytes`: `bool` - 是否返回字节（默认 `False`，返回字符串）

**返回值：**

- `str | bytes` - 解码后的数据

**异常：**

- `ValueError` - 如果输入不是有效的 DX 编码

**示例：**

```python
dx_decode('dxXXXX...')                    # 返回字符串
dx_decode('dxXXXX...', as_bytes=True)     # 返回字节
```

### `is_dx_encoded(s)`

检查字符串是否为有效的 DX 编码。

**参数：**

- `s`: `str` - 要检查的字符串

**返回值：**

- `bool` - 是否为有效的 DX 编码

### `get_dx_info()`

获取 DX 编码的信息。

**返回值：**

- `dict` - 包含版本、作者、字符集等信息

## 常量

```python
from dxcode import DX_CHARSET, DX_PREFIX, DX_MAGIC, DX_PADDING

print(DX_CHARSET)  # DX 字符集
print(DX_PREFIX)   # 'dx'
print(DX_MAGIC)    # 0x44
print(DX_PADDING)  # '='
```

## 命令行工具

安装后可以在命令行使用：

```bash
# 编码
echo "Hello, Dogxi!" | dx-encode

# 解码
echo "dxXXXX..." | dx-decode

# 或者直接使用
dx-encode "Hello, World!"
dx-decode "dxXXXX..."
```

## 异常处理

```python
from dxcode import dx_decode, DxEncodingError

try:
    dx_decode('invalid-string')
except DxEncodingError as e:
    print(f'解码错误: {e}')
```

## 相关

- [dxcode](https://www.npmjs.com/package/dxcode) - JavaScript/TypeScript 库
- [dxcode-cli](https://www.npmjs.com/package/dxcode-cli) - CLI 命令行工具
- [dxc.dogxi.me](https://dxc.dogxi.me) - 在线编码解码

## 兼容性

- Python >= 3.7

## 许可证

MIT License © [Dogxi](https://github.com/dogxii)
