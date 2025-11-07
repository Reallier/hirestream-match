import hashlib

def hash_inputs(jd_text: str, resume_text: str) -> str:
    """
    计算两段文本的 SHA256 哈希，用于判断输入内容是否变化。

    保留该方法的理由：
    - 比较哈希值比直接比对长字符串更高效（O(1) vs O(n)）。
    - 可作为防抖机制，避免重复触发昂贵的分析逻辑。
    - SHA256 哈希稳定、碰撞概率极低，适合做缓存键或变更检测。
    - 性能损耗极小（微秒级），相对整体分析逻辑可忽略。

    参数:
        jd_text (str): 职位描述文本。
        resume_text (str): 简历文本。

    返回:
        str: 两段文本拼接后的 SHA256 哈希值（十六进制字符串）。
    """
    h = hashlib.sha256()
    h.update(jd_text.encode("utf-8", errors="ignore"))
    h.update(b"\n----\n")
    h.update(resume_text.encode("utf-8", errors="ignore"))
    return h.hexdigest()