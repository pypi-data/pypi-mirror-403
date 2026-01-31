import base64
from io import BytesIO
from PIL import Image


def get_image_format(data):
    """
    判断图片格式
    :param data: bytes 或 base64 字符串（支持 data URI 格式如 data:image/png;base64,xxx）
    :return: 图片格式字符串 (如 'JPEG', 'PNG') 或错误信息
    """
    try:
        image_bytes = None

        # 情况 1：Base64 字符串（包括标准 base64 和 data URI）
        if isinstance(data, str):
            # 处理 data URI（如 "data:image/png;base64,iVBORw0KGgo..."）
            if ',' in data:
                data = data.split(',')[1]

            # 解码 base64
            image_bytes = base64.b64decode(data)

        # 情况 2：直接是 bytes
        elif isinstance(data, bytes):
            image_bytes = data

        else:
            return "错误: 不支持的类型，请提供 bytes 或 base64 字符串"

        # 用 BytesIO 包装成文件流
        file_stream = BytesIO(image_bytes)

        # 用 Pillow 识别格式
        with Image.open(file_stream) as img:
            return img.format  # 返回如 'JPEG', 'PNG', 'GIF', 'WEBP'

    except base64.binascii.Error:
        return "错误: 无效的 Base64 编码"
    except Exception as e:
        return f"错误: {e}"


# ==================== 使用示例 ====================

# # 示例 1：传入文件 bytes
# with open("test.png", "rb") as f:
#     file_bytes = f.read()
# print(get_image_format(file_bytes))  # 输出: PNG
#
# # 示例 2：传入标准 base64 字符串（无头）
# import base64
#
# b64_string = base64.b64encode(open("test.jpg", "rb").read()).decode()
# print(get_image_format(b64_string))  # 输出: JPEG
#
# # 示例 3：传入 Data URI（常见于网页上传）
# data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
# print(get_image_format(data_uri))  # 输出: PNG
#
# # 示例 4：传入无效数据
# print(get_image_format("invalid_base64!!!"))  # 输出: 错误: 无效的 Base64 编码