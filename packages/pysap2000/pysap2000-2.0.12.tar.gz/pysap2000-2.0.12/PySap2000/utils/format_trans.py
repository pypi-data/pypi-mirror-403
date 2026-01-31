
"""
format_trans — 
Author: JIANGYAO-AISA
Date: 2024/2/9

"""
import re
class ConvertMyString:

    @staticmethod
    def convert_to_CHS_format(string):
        # 使用正则表达式提取数字部分
        numbers = re.findall(r'\d+', string)
        if len(numbers) >= 2:
            return f"CHS {numbers[0]}/{numbers[1]}/H"
        else:
            return "Invalid input"



    @staticmethod
    def convert_to_RHSU_format(input_str):
        """
        Convert rectangular section format from "B400x300x12x16" to "RHSU 400/300/16/16/12/12".

        Parameters:
        input_str (str): The input string in the format of "B<width>x<height>x<top_bottom_thickness>x<left_right_thickness>".

        Returns:
        str: The converted string in the format of "RHSU <width>/<height>/<left_right_thickness>/<left_right_thickness>/<top_bottom_thickness>/<top_bottom_thickness>".
        """
        # 检查输入字符串是否符合预期格式
        if not input_str.startswith('B') or 'x' not in input_str:
            raise ValueError(
                "Input string format is incorrect. Expected format 'B<width>x<height>x<top_bottom_thickness>x<left_right_thickness>'.")

        # 提取宽度、高度、上下壁厚、左右壁厚
        parts = input_str[1:].split('x')
        if len(parts) != 4:
            raise ValueError(
                "Input string format is incorrect. Expected format 'B<width>x<height>x<top_bottom_thickness>x<left_right_thickness>'.")

        width, height, top_bottom_thickness, left_right_thickness = parts

        # 构造并返回RHSU格式的字符串
        return f"RHSU {width}/{height}/{left_right_thickness}/{left_right_thickness}/{top_bottom_thickness}/{top_bottom_thickness}"


if __name__ == '__main__':
    f = ConvertMyString()
    input_str1 = "P219x8"
    converted_str1 = f.convert_to_CHS_format(input_str1)
    print(converted_str1)  # 输出: CHS 219/8/H
    input_str = "B400x300x12x16"
    converted_str = f.convert_to_RHSU_format(input_str)
    print(converted_str)  # 输出: RHSU 400/300/16/16/12/12

