import hashlib
from typing import Dict, Any, List


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


def render_markdown_report(result: Dict[str, Any]) -> str:
    """
        将包含分析结果的字典渲染成一个格式化的 Markdown 报告字符串。

        这个函数的主要职责是作为“视图”层，它不关心数据是如何计算的，
        只关心如何将传入的结构化数据（字典）转换成
        人类可读的、格式优美的 Markdown 文本。

        Args:
            result (Dict[str, Any]): 一个包含报告数据的字典。
                预期的键 (keys) 包括:
                - "match_score" (int | str): 匹配分数。
                - "advantages" (List[str]): 优势点列表。
                - "risks" (List[str]): 风险点列表。
                - "advice" (str): 综合建议。

        Returns:
            str: 一个多行的、格式化后的 Markdown 字符串。
        """
    # --- 1. 安全地从字典中提取数据 ---
    # 使用 .get() 方法可以防止因键(key)不存在而引发的 KeyError。

    # "match_score"：获取匹配度，如果不存在则默认为 0，并确保转换为整数。
    score = int(result.get("match_score", 0))
    # "advantages"：获取优势列表，如果不存在则默认为一个空列表 []。
    advantages = result.get("advantages", [])
    # "risks"：获取风险列表，如果不存在则默认为一个空列表 []。
    risks = result.get("risks", [])
    # "advice"：获取建议文本，如果不存在则默认为一个空字符串 ""。
    advice = result.get("advice", "")

    def bullets(items: List[str]) -> str:
        """将一个字符串列表转换为 Markdown 的项目符号列表（bullet points）。"""

        # 这是一个三元运算符：
        # 1. (if items): 检查列表是否为非空。
        # 2. (True):  使用列表推导式在每项前加上 "* "，然后用换行符 "\n" 连接成一个字符串。
        # 3. (False/else): 如果列表为空，返回一个表示“无”的斜体字符串 ("_（无）_")。
        return "\n".join([f"* {i}" for i in items]) if items else "_（无）_"

    # --- 3. 使用 F-string 模板构建 Markdown 字符串 ---
    # f"""...""" (多行f-string) 允许我们以所见即所得的方式定义模板，
    # 并使用 {variable} 语法轻松地将 Python 变量嵌入其中。
    md = f"""### 匹配度：**{score}%**

**候选人优势**
{bullets(advantages)}

**潜在风险**
{bullets(risks)}

**综合建议**
{advice}
"""
    return md