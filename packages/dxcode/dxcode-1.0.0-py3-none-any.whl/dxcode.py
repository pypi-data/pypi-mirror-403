"""
DX Encoding - 由 Dogxi 创造的独特编码算法

Python 实现

作者: Dogxi
版本: 1.0.0
许可证: MIT
"""

from typing import Union

# DX 字符集 - 以 DXdx 开头作为签名，共64个字符
DX_CHARSET = "DXdx0123456789ABCEFGHIJKLMNOPQRSTUVWYZabcefghijklmnopqrstuvwyz-_"

# 魔数 - 用于 XOR 变换，'D' 的 ASCII 值
MAGIC = 0x44

# 前缀
PREFIX = "dx"

# 填充字符
PADDING = "="

# 构建反向查找表
DX_DECODE_MAP = {char: idx for idx, char in enumerate(DX_CHARSET)}


class DxEncodingError(Exception):
    """DX 编码错误"""

    pass


def dx_encode(data: Union[str, bytes, bytearray]) -> str:
    """
    将数据编码为 DX 格式

    参数:
        data: 要编码的数据（字符串、bytes 或 bytearray）

    返回:
        以 'dx' 为前缀的编码字符串

    示例:
        >>> dx_encode('Hello, Dogxi!')
        'dxXXXX...'
        >>> dx_encode(b'\\x00\\x01\\x02')
        'dxXXXX...'
    """
    # 将输入转换为字节
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif isinstance(data, bytearray):
        data = bytes(data)
    elif not isinstance(data, bytes):
        raise DxEncodingError("输入必须是 str、bytes 或 bytearray")

    result = []
    length = len(data)

    # 每 3 字节处理一组
    for i in range(0, length, 3):
        b0 = data[i]
        b1 = data[i + 1] if i + 1 < length else 0
        b2 = data[i + 2] if i + 2 < length else 0

        # 将 3 字节（24位）分成 4 个 6 位组
        v0 = (b0 >> 2) & 0x3F
        v1 = ((b0 & 0x03) << 4 | (b1 >> 4)) & 0x3F
        v2 = ((b1 & 0x0F) << 2 | (b2 >> 6)) & 0x3F
        v3 = b2 & 0x3F

        # XOR 变换并映射到字符
        result.append(DX_CHARSET[(v0 ^ MAGIC) & 0x3F])
        result.append(DX_CHARSET[(v1 ^ MAGIC) & 0x3F])

        if i + 1 < length:
            result.append(DX_CHARSET[(v2 ^ MAGIC) & 0x3F])
        else:
            result.append(PADDING)

        if i + 2 < length:
            result.append(DX_CHARSET[(v3 ^ MAGIC) & 0x3F])
        else:
            result.append(PADDING)

    return PREFIX + "".join(result)


def dx_decode(encoded: str, as_string: bool = True) -> Union[str, bytes]:
    """
    将 DX 编码的字符串解码

    参数:
        encoded: DX 编码的字符串（必须以 'dx' 开头）
        as_string: 是否返回字符串（默认 True）

    返回:
        解码后的字符串或字节

    异常:
        DxEncodingError: 如果输入不是有效的 DX 编码

    示例:
        >>> dx_decode('dxXXXX...')
        'Hello, Dogxi!'
        >>> dx_decode('dxXXXX...', as_string=False)
        b'Hello, Dogxi!'
    """
    # 验证前缀
    if not encoded or not encoded.startswith(PREFIX):
        raise DxEncodingError("无效的 DX 编码：缺少 dx 前缀")

    # 移除前缀
    data = encoded[len(PREFIX) :]

    if len(data) == 0:
        return "" if as_string else b""

    # 验证长度
    if len(data) % 4 != 0:
        raise DxEncodingError("无效的 DX 编码：长度不正确")

    # 计算填充数量
    padding_count = 0
    if data.endswith(PADDING + PADDING):
        padding_count = 2
    elif data.endswith(PADDING):
        padding_count = 1

    # 计算输出长度
    output_len = (len(data) // 4) * 3 - padding_count
    result = bytearray(output_len)

    result_idx = 0

    # 每 4 字符处理一组
    for i in range(0, len(data), 4):
        c0 = data[i]
        c1 = data[i + 1]
        c2 = data[i + 2]
        c3 = data[i + 3]

        # 字符转索引
        try:
            i0 = DX_DECODE_MAP[c0]
            i1 = DX_DECODE_MAP[c1]
            i2 = 0 if c2 == PADDING else DX_DECODE_MAP[c2]
            i3 = 0 if c3 == PADDING else DX_DECODE_MAP[c3]
        except KeyError as e:
            raise DxEncodingError(f"无效的 DX 编码：包含非法字符 {e}")

        # XOR 逆变换
        v0 = (i0 ^ MAGIC) & 0x3F
        v1 = (i1 ^ MAGIC) & 0x3F
        v2 = (i2 ^ MAGIC) & 0x3F
        v3 = (i3 ^ MAGIC) & 0x3F

        # 重建字节
        b0 = (v0 << 2) | (v1 >> 4)
        b1 = ((v1 & 0x0F) << 4) | (v2 >> 2)
        b2 = ((v2 & 0x03) << 6) | v3

        if result_idx < output_len:
            result[result_idx] = b0
            result_idx += 1
        if result_idx < output_len:
            result[result_idx] = b1
            result_idx += 1
        if result_idx < output_len:
            result[result_idx] = b2
            result_idx += 1

    result_bytes = bytes(result)

    if as_string:
        try:
            return result_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise DxEncodingError(f"解码后的数据不是有效的 UTF-8: {e}")

    return result_bytes


def is_dx_encoded(s: str) -> bool:
    """
    检查字符串是否为有效的 DX 编码

    参数:
        s: 要检查的字符串

    返回:
        如果是有效的 DX 编码返回 True，否则返回 False

    示例:
        >>> is_dx_encoded('dxXXXX...')
        True
        >>> is_dx_encoded('hello')
        False
    """
    if not s or not isinstance(s, str):
        return False

    if not s.startswith(PREFIX):
        return False

    data = s[len(PREFIX) :]

    # 检查长度
    if len(data) == 0 or len(data) % 4 != 0:
        return False

    # 检查字符
    for i, char in enumerate(data):
        if char == PADDING:
            # 填充只能在末尾
            if i < len(data) - 2:
                return False
        elif char not in DX_DECODE_MAP:
            return False

    return True


def get_dx_info() -> dict:
    """
    获取 DX 编码的信息

    返回:
        包含版本、作者、字符集等信息的字典
    """
    return {
        "name": "DX Encoding",
        "version": "1.0.0",
        "author": "Dogxi",
        "charset": DX_CHARSET,
        "prefix": PREFIX,
        "magic": MAGIC,
        "padding": PADDING,
    }


# 别名，方便使用
encode = dx_encode
decode = dx_decode
is_encoded = is_dx_encoded
info = get_dx_info


def __main__():
    """命令行入口"""
    import sys

    if len(sys.argv) < 3:
        print("DX Encoding - 由 Dogxi 创造")
        print()
        print("用法:")
        print("  python dx_encoding.py encode <文本>")
        print("  python dx_encoding.py decode <编码>")
        print("  python dx_encoding.py info")
        print()
        print("示例:")
        print("  python dx_encoding.py encode 'Hello, Dogxi!'")
        print("  python dx_encoding.py decode 'dxXXXX...'")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "info":
        info_data = get_dx_info()
        print(f"名称: {info_data['name']}")
        print(f"版本: {info_data['version']}")
        print(f"作者: {info_data['author']}")
        print(f"前缀: {info_data['prefix']}")
        print(f"魔数: 0x{info_data['magic']:02X}")
        print(f"字符集: {info_data['charset']}")
    elif command == "encode":
        text = sys.argv[2]
        encoded = dx_encode(text)
        print(encoded)
    elif command == "decode":
        encoded = sys.argv[2]
        try:
            decoded = dx_decode(encoded)
            print(decoded)
        except DxEncodingError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"未知命令: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    __main__()
