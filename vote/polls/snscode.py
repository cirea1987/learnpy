import random
import re
TEL_PATTERN = re.compile(r'1[3-9]\d{9}')
def check_tel(tel):
    """检查手机号"""
    return TEL_PATTERN.fullmatch(tel) is not None


def random_code(length=6):
    """生成随机短信验证码"""
    return ''.join(random.choices('0123456789', k=length))