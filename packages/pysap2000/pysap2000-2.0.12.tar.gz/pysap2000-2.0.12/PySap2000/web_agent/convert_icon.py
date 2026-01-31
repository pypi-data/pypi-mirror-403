"""
将 PNG 图标转换为 ICO 格式
"""
from PIL import Image

# 读取 PNG 图标
png_path = "../../icon1/sap-agent.png"
ico_path = "sap-agent.ico"

# 打开图片
img = Image.open(png_path)

# 转换为 RGBA 模式（如果不是的话）
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# 保存为 ICO 格式，包含多个尺寸
img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print(f"✓ 图标转换完成: {ico_path}")
