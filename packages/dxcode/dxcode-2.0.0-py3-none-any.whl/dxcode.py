"""
DX Encoding - 带有 `dx` 前缀的自定义编码算法

Python 实现

作者: Dogxi
版本: 2.0.0
许可证: MIT

v2.0 新增: CRC16-CCITT 校验和支持
"""

from typing import Tuple, Union

# DX 字符集 - 以 DXdx 开头作为签名，共64个字符
DX_CHARSET = "DXdx0123456789ABCEFGHIJKLMNOPQRSTUVWYZabcefghijklmnopqrstuvwyz-_"

# 魔数 - 用于 XOR 变换，'D' 的 ASCII 值
MAGIC = 0x44

# 前缀
PREFIX = "dx"

# 填充字符
PADDING = "="

# 头部大小（2字节 CRC16）
HEADER_SIZE = 2

# 构建反向查找表
DX_DECODE_MAP = {char: idx for idx, char in enumerate(DX_CHARSET)}

# CRC16-CCITT 查找表
CRC16_TABLE = []
for i in range(256):
    crc = i << 8
    for _ in range(8):
        if crc & 0x8000:
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF
        else:
            crc = (crc << 1) & 0xFFFF
    CRC16_TABLE.append(crc)


class DxEncodingError(Exception):
    """DX 编码错误"""

    pass


class DxChecksumError(DxEncodingError):
    """DX 校验和错误"""

    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual
        super().__init__(f"校验和不匹配：期望 0x{expected:04X}，实际 0x{actual:04X}")


def crc16(data: bytes) -> int:
    """
    计算 CRC16-CCITT 校验和

    参数:
        data: 输入字节数据

    返回:
        16位校验和
    """
    crc = 0xFFFF
    for byte in data:
        index = ((crc >> 8) ^ byte) & 0xFF
        crc = ((crc << 8) ^ CRC16_TABLE[index]) & 0xFFFF
    return crc


def _encode_raw(data: bytes) -> str:
    """
    内部编码函数（不带前缀）

    参数:
        data: 要编码的字节数据

    返回:
        编码后的字符串（不含前缀）
    """
    if len(data) == 0:
        return ""

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

    return "".join(result)


def _decode_raw(data: str) -> bytes:
    """
    内部解码函数（不带前缀验证）

    参数:
        data: 编码数据（不含前缀）

    返回:
        解码后的字节数据
    """
    if len(data) == 0:
        return b""

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

    return bytes(result)


def dx_encode(data: Union[str, bytes, bytearray]) -> str:
    """
    将数据编码为 DX 格式（带 CRC16 校验和）

    参数:
        data: 要编码的数据（字符串、bytes 或 bytearray）

    返回:
        以 'dx' 为前缀的编码字符串（包含校验和）

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

    # 计算 CRC16
    checksum = crc16(data)

    # 构建头部（2字节 CRC16，大端序）
    header = bytes([checksum >> 8, checksum & 0xFF])

    # 合并头部和数据
    combined = header + data

    # 编码
    return PREFIX + _encode_raw(combined)


def dx_decode(encoded: str, as_string: bool = True) -> Union[str, bytes]:
    """
    将 DX 编码的字符串解码（带校验和验证）

    参数:
        encoded: DX 编码的字符串（必须以 'dx' 开头）
        as_string: 是否返回字符串（默认 True）

    返回:
        解码后的字符串或字节

    异常:
        DxEncodingError: 如果输入不是有效的 DX 编码
        DxChecksumError: 如果校验和不匹配

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

    # 解码
    combined = _decode_raw(data)

    # 验证长度
    if len(combined) < HEADER_SIZE:
        raise DxEncodingError("无效的格式头部")

    # 提取头部
    expected_checksum = (combined[0] << 8) | combined[1]

    # 提取数据
    payload = combined[HEADER_SIZE:]

    # 验证校验和
    actual_checksum = crc16(payload)
    if expected_checksum != actual_checksum:
        raise DxChecksumError(expected_checksum, actual_checksum)

    if as_string:
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as e:
            raise DxEncodingError(f"解码后的数据不是有效的 UTF-8: {e}")

    return payload


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

    # 检查长度（至少需要头部）
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


def dx_verify(encoded: str) -> bool:
    """
    验证 DX 编码的校验和（不返回解码数据）

    参数:
        encoded: DX 编码的字符串

    返回:
        校验和是否匹配

    异常:
        DxEncodingError: 如果格式无效（非校验和错误）

    示例:
        >>> dx_verify('dxXXXX...')
        True
    """
    try:
        dx_decode(encoded, as_string=False)
        return True
    except DxChecksumError:
        return False


def get_checksum(encoded: str) -> Tuple[int, int]:
    """
    获取 DX 编码的校验和信息

    参数:
        encoded: DX 编码的字符串

    返回:
        (存储的校验和, 计算的校验和) 元组

    异常:
        DxEncodingError: 如果输入不是有效的 DX 编码

    示例:
        >>> stored, computed = get_checksum('dxXXXX...')
        >>> stored == computed
        True
    """
    # 验证前缀
    if not encoded or not encoded.startswith(PREFIX):
        raise DxEncodingError("无效的 DX 编码：缺少 dx 前缀")

    # 移除前缀
    data = encoded[len(PREFIX) :]

    # 解码
    combined = _decode_raw(data)

    # 验证长度
    if len(combined) < HEADER_SIZE:
        raise DxEncodingError("无效的格式头部")

    # 提取校验和
    stored = (combined[0] << 8) | combined[1]
    payload = combined[HEADER_SIZE:]
    computed = crc16(payload)

    return (stored, computed)


def get_dx_info() -> dict:
    """
    获取 DX 编码的信息

    返回:
        包含版本、作者、字符集等信息的字典
    """
    return {
        "name": "DX Encoding",
        "version": "2.0.0",
        "author": "Dogxi",
        "charset": DX_CHARSET,
        "prefix": PREFIX,
        "magic": MAGIC,
        "padding": PADDING,
        "checksum": "CRC16-CCITT",
    }


# 别名，方便使用
encode = dx_encode
decode = dx_decode
is_encoded = is_dx_encoded
verify = dx_verify
info = get_dx_info


def __main__():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("DX Encoding - 由 Dogxi 创造 (v2.0 带校验和)")
        print()
        print("用法:")
        print("  python dxcode.py encode <文本>")
        print("  python dxcode.py decode <编码>")
        print("  python dxcode.py verify <编码>")
        print("  python dxcode.py info")
        print()
        print("示例:")
        print("  python dxcode.py encode 'Hello, Dogxi!'")
        print("  python dxcode.py decode 'dxXXXX...'")
        print("  python dxcode.py verify 'dxXXXX...'")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "info":
        info_data = get_dx_info()
        print(f"名称: {info_data['name']}")
        print(f"版本: {info_data['version']}")
        print(f"作者: {info_data['author']}")
        print(f"前缀: {info_data['prefix']}")
        print(f"魔数: 0x{info_data['magic']:02X}")
        print(f"校验和: {info_data['checksum']}")
        print(f"字符集: {info_data['charset']}")
    elif command == "encode":
        if len(sys.argv) < 3:
            print("错误: 请提供要编码的文本", file=sys.stderr)
            sys.exit(1)
        text = sys.argv[2]
        encoded = dx_encode(text)
        print(encoded)
    elif command == "decode":
        if len(sys.argv) < 3:
            print("错误: 请提供要解码的字符串", file=sys.stderr)
            sys.exit(1)
        encoded = sys.argv[2]
        try:
            decoded = dx_decode(encoded)
            print(decoded)
        except DxEncodingError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "verify":
        if len(sys.argv) < 3:
            print("错误: 请提供要验证的字符串", file=sys.stderr)
            sys.exit(1)
        encoded = sys.argv[2]
        try:
            if dx_verify(encoded):
                stored, _ = get_checksum(encoded)
                print(f"✅ 校验和验证通过")
                print(f"   CRC16: 0x{stored:04X}")
            else:
                stored, computed = get_checksum(encoded)
                print(f"❌ 校验和验证失败")
                print(f"   存储的 CRC16: 0x{stored:04X}")
                print(f"   计算的 CRC16: 0x{computed:04X}")
                sys.exit(1)
        except DxEncodingError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"未知命令: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    __main__()
