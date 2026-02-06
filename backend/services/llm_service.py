import dashscope
from typing import List, Dict, Any, Optional
from config import settings
from match_service.log import logger
import json


class LLMService:
    """LLM 服务：用于 JD 解析、生成 embeddings 等"""
    
    def __init__(self):
        dashscope.api_key = settings.dashscope_api_key
        self.model = settings.llm_model
        self.embedding_model = settings.embedding_model
    
    def parse_jd(self, jd_text: str) -> Dict[str, Any]:
        """
        解析 JD，提取必备技能、加分技能、过滤条件等
        
        Returns:
            {
                'must_skills': List[str],
                'nice_skills': List[str],
                'filters': Dict,
                'notes': str
            }
        """
        prompt = f"""请分析以下职位描述(JD)，提取关键信息：

职位描述：
{jd_text}

请以 JSON 格式返回以下信息：
1. must_skills: 必备技能列表（硬性要求）
2. nice_skills: 加分技能列表（优先但非必须）
3. filters: 过滤条件，包含：
   - location: 工作地点
   - min_years: 最少工作年限
   - max_years: 最多工作年限
   - education_level: 学历要求（如：本科、硕士、博士）
4. notes: 其他重要备注

请确保返回有效的 JSON 格式。"""

        try:
            response = dashscope.Generation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的招聘分析助手，擅长从职位描述中提取结构化信息。"},
                    {"role": "user", "content": prompt}
                ],
                result_format='message'
            )

            result = json.loads(response.output.choices[0].message.content)
            
            # 确保返回格式正确
            return {
                'must_skills': result.get('must_skills', []),
                'nice_skills': result.get('nice_skills', []),
                'filters': result.get('filters', {}),
                'notes': result.get('notes', '')
            }
        
        except Exception as e:
            # 降级：返回空结果
            logger.error(f"JD 解析失败: {str(e)}")
            return {
                'must_skills': [],
                'nice_skills': [],
                'filters': {},
                'notes': f'解析失败: {str(e)}'
            }
    
    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        使用 LLM 解析简历，提取结构化信息
        
        Returns:
            {
                'personal': {'name': str, 'email': str, 'phone': str, 'location': str},
                'current_title': str,
                'current_company': str,
                'years_experience': int,
                'skills': List[str],
                'experiences': List[Dict],
                'education': List[Dict]
            }
        """
        # 截断过长的文本
        text = self._truncate_text(resume_text, max_tokens=6000)
        
        prompt = f"""请分析以下简历内容，提取关键信息。

简历内容：
{text}

请以 JSON 格式返回以下信息：
1. name: 候选人姓名（必须提取，如果无法确定则返回文件中最像姓名的词）
2. email: 邮箱地址
3. phone: 手机号码
4. location: 所在城市
5. current_title: 当前/最近职位
6. current_company: 当前/最近公司
7. years_experience: 工作年限（整数，根据工作经历计算）
8. skills: 技能列表（提取所有技术技能、工具、语言等，最多20个）
9. education_level: 最高学历（如：本科、硕士、博士、专科）
10. experiences: 工作经历列表，每条包含 company, title, start_date, end_date, description
11. education: 教育经历列表，每条包含 school, degree, major, start_date, end_date

注意：
- 姓名是最重要的字段，请仔细识别
- 日期格式用 YYYY-MM 或 YYYY
- 如果信息不存在，返回 null
- skills 请提取具体的技术技能（如 Python、Vue、PostgreSQL），不要提取软技能

请确保返回有效的 JSON 格式。"""

        try:
            response = dashscope.Generation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的简历解析助手，擅长从简历文本中提取结构化信息。请仔细分析并提取所有可用信息。"},
                    {"role": "user", "content": prompt}
                ],
                result_format='message'
            )

            content = response.output.choices[0].message.content
            # 清理 JSON 格式
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            result = json.loads(content.strip())
            
            # 规范化返回格式
            return {
                'personal': {
                    'name': result.get('name'),
                    'email': result.get('email'),
                    'phone': result.get('phone'),
                    'location': result.get('location')
                },
                'current_title': result.get('current_title'),
                'current_company': result.get('current_company'),
                'years_experience': result.get('years_experience'),
                'skills': result.get('skills', []) or [],
                'education_level': result.get('education_level'),
                'experiences': result.get('experiences', []) or [],
                'education': result.get('education', []) or []
            }
        
        except Exception as e:
            logger.error(f"LLM 简历解析失败: {str(e)}")
            # 返回空结构
            return {
                'personal': {'name': None, 'email': None, 'phone': None, 'location': None},
                'current_title': None,
                'current_company': None,
                'years_experience': None,
                'skills': [],
                'education_level': None,
                'experiences': [],
                'education': []
            }
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本的向量表示
        
        Args:
            text: 要向量化的文本
        
        Returns:
            embedding 向量（1536 维）
        """
        try:
            # 截断过长的文本
            text = self._truncate_text(text, max_tokens=8000)

            response = dashscope.TextEmbedding.call(
                model=self.embedding_model,
                input=text
            )

            # 支持字典和对象两种返回格式
            output = response.output
            if isinstance(output, dict):
                embeddings = output.get('embeddings', [])
                if embeddings:
                    return embeddings[0].get('embedding')
            else:
                return output.embeddings[0].embedding
            
            return None
        
        except Exception as e:
            logger.error(f"生成 embedding 失败: {str(e)}")
            return None
    
    def generate_embeddings_batch(
        self, 
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        批量生成 embeddings
        
        Args:
            texts: 文本列表
        
        Returns:
            embeddings 列表
        """
        embeddings = []
        
        # 批量处理
        try:
            # 截断所有文本
            truncated_texts = [
                self._truncate_text(text, max_tokens=8000)
                for text in texts
            ]

            response = dashscope.TextEmbedding.call(
                model=self.embedding_model,
                input=truncated_texts
            )

            # 支持字典和对象两种返回格式
            output = response.output
            if isinstance(output, dict):
                for item in output.get('embeddings', []):
                    embeddings.append(item.get('embedding'))
            else:
                for item in output.embeddings:
                    embeddings.append(item.embedding)

            return embeddings
        
        except Exception as e:
            logger.warning(f"批量生成 embeddings 失败，降级为逐个生成: {str(e)}")
            # 降级：逐个生成
            for text in texts:
                emb = self.generate_embedding(text)
                embeddings.append(emb)
            
            return embeddings
    
    def generate_evidence(
        self,
        candidate_text: str,
        matched_skills: List[str],
        jd_text: str,
        max_evidences: int = 3
    ) -> List[Dict[str, Any]]:
        """
        生成匹配证据
        
        Args:
            candidate_text: 候选人简历文本
            matched_skills: 匹配的技能列表
            jd_text: 职位描述
            max_evidences: 最多返回几条证据
        
        Returns:
            证据列表，每条包含 skill, snippet, period 等
        """
        prompt = f"""请从以下候选人简历中，为匹配的技能找出具体的证据片段。

匹配的技能：{', '.join(matched_skills)}

候选人简历：
{candidate_text[:2000]}  # 截取前2000字符

请为每个技能找出：
1. 证据片段（snippet）：相关的句子或段落
2. 时间段（period）：该技能使用的时间范围

以 JSON 格式返回，格式如下：
{{
  "evidences": [
    {{
      "skill": "技能名称",
      "snippet": "证据片段",
      "period": "时间段"
    }}
  ]
}}

最多返回 {max_evidences} 条证据。"""

        try:
            response = dashscope.Generation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的简历分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                result_format='message'
            )

            result = json.loads(response.output.choices[0].message.content)
            return result.get('evidences', [])
        
        except Exception as e:
            logger.error(f"生成证据失败: {str(e)}")
            # 降级：返回简单的匹配列表
            return [
                {
                    'skill': skill,
                    'snippet': f'候选人简历中提及了 {skill}',
                    'period': '未知'
                }
                for skill in matched_skills[:max_evidences]
            ]
    
    def summarize_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """
        生成候选人摘要（用于向量化）
        
        Args:
            candidate_data: 候选人完整数据
        
        Returns:
            摘要文本
        """
        # 构建摘要文本
        parts = []
        
        # 基本信息
        if candidate_data.get('name'):
            parts.append(f"姓名：{candidate_data['name']}")
        
        if candidate_data.get('current_title'):
            parts.append(f"当前职位：{candidate_data['current_title']}")
        
        if candidate_data.get('current_company'):
            parts.append(f"当前公司：{candidate_data['current_company']}")
        
        if candidate_data.get('years_experience'):
            parts.append(f"工作年限：{candidate_data['years_experience']}年")
        
        # 技能
        if candidate_data.get('skills'):
            skills_text = ', '.join(candidate_data['skills'][:20])  # 最多20个技能
            parts.append(f"技能：{skills_text}")
        
        # 工作经历
        if candidate_data.get('experiences'):
            exp_texts = []
            for exp in candidate_data['experiences'][:3]:  # 最多3段经历
                exp_text = f"{exp.get('company', '')} - {exp.get('title', '')}"
                if exp.get('description'):
                    exp_text += f": {exp['description'][:100]}"  # 截取前100字符
                exp_texts.append(exp_text)
            if exp_texts:
                parts.append("工作经历：" + "; ".join(exp_texts))
        
        # 教育背景
        if candidate_data.get('education'):
            edu_texts = []
            for edu in candidate_data['education']:
                edu_text = f"{edu.get('school', '')} {edu.get('degree', '')} {edu.get('major', '')}"
                edu_texts.append(edu_text.strip())
            if edu_texts:
                parts.append("教育：" + "; ".join(edu_texts))
        
        return "\n".join(parts)
    
    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """截断文本以符合 token 限制（近似）"""
        # 简单近似：1 token ≈ 4 字符
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            text = text[:max_chars]
        return text

    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量（近似）"""
        # 简单近似：1 token ≈ 4 字符
        return len(text) // 4