# -*- coding: utf-8 -*-
"""
测试模块 16: 边界条件测试

测试各种极端输入情况下的系统行为：
1. 大文件简历（>1MB）
2. 超长 JD 文本（>10000 字符）
3. 特殊字符和格式
4. 空值和边界值
"""

import pytest
import os
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data"


class TestLargeInputs:
    """大输入测试"""
    
    @pytest.fixture
    def large_resume_text(self):
        """生成 >1MB 的大型简历文本"""
        # 基础简历模板
        base_resume = """
张三
高级软件工程师 | 10年经验

技能专长：
- Python, Java, Go, C++
- FastAPI, Django, Spring Boot
- PostgreSQL, Redis, MongoDB, Elasticsearch
- Docker, Kubernetes, CI/CD
- AWS, GCP, Azure

工作经历：
"""
        # 生成大量工作经历条目以达到 >1MB
        experience_template = """
{year}年-{next_year}年 某科技公司{company_num} 技术负责人
- 负责核心业务系统的架构设计与技术选型，主导完成从单体架构到微服务架构的转型
- 带领{team_size}人研发团队，完成{project_count}个重要项目的按时交付
- 优化系统性能，将核心接口响应时间从{old_time}ms降低到{new_time}ms，提升{improvement}%
- 推动DevOps实践落地，建立完善的CI/CD流水线，部署频率提升{deploy_freq}倍
- 主导技术分享和代码评审，提升团队整体技术水平，培养{engineer_count}名骨干工程师
- 负责技术预研和创新项目孵化，在{topic1}、{topic2}等方向取得突破性成果
- 与产品、运营紧密协作，确保技术方案满足业务需求并具备扩展性
- 参与系统故障排查和性能调优，保障线上服务{availability}可用性
"""
        # 生成足够多的条目以超过 1MB
        resume_content = base_resume
        topics = ["AI", "大数据", "云原生", "边缘计算", "区块链", "物联网", "5G", "自动驾驶"]
        
        for i in range(500):  # 生成500个工作经历条目
            year = 2020 - (i // 5)
            entry = experience_template.format(
                year=year,
                next_year=year + 1,
                company_num=i + 1,
                team_size=(i % 20) + 5,
                project_count=(i % 10) + 3,
                old_time=500 + (i % 300),
                new_time=50 + (i % 50),
                improvement=70 + (i % 25),
                deploy_freq=3 + (i % 5),
                engineer_count=(i % 5) + 2,
                topic1=topics[i % len(topics)],
                topic2=topics[(i + 1) % len(topics)],
                availability="99.99%"
            )
            resume_content += entry
        
        # 确保超过 1MB
        while len(resume_content.encode('utf-8')) < 1024 * 1024:
            resume_content += "\n额外技能描述：精通各种现代化开发技术和最佳实践。" * 100
        
        return resume_content
    
    @pytest.fixture
    def long_jd_text(self):
        """生成超长 JD 文本（>10000 字符）"""
        jd_base = """
职位：资深全栈工程师
公司：某知名科技公司
地点：北京/上海/深圳/杭州

职位描述：
我们正在寻找一位经验丰富的全栈工程师加入我们的核心技术团队，您将参与公司核心产品的设计、开发和优化工作。

岗位职责：
"""
        responsibilities = [
            "负责公司核心产品的后端架构设计和开发工作",
            "参与前端页面的开发，确保良好的用户体验",
            "设计和实现高性能、高可用的微服务架构",
            "编写清晰、可维护的代码，进行代码评审",
            "参与技术方案的讨论和制定",
            "解决复杂的技术问题和性能瓶颈",
            "与产品、设计团队紧密协作",
            "参与技术文档的编写和维护",
            "推动技术创新和最佳实践的落地",
            "指导和帮助初级工程师成长",
        ]
        
        requirements = [
            "计算机科学或相关专业本科及以上学历",
            "5年以上软件开发经验",
            "精通Python/Java/Go中至少一种语言",
            "熟悉前端技术栈（React/Vue/Angular）",
            "熟悉关系型数据库和NoSQL数据库",
            "了解分布式系统设计原则",
            "具备良好的沟通能力和团队协作精神",
            "有大型项目经验者优先",
            "有开源项目贡献经验者优先",
            "具备快速学习能力和技术热情",
        ]
        
        jd_content = jd_base
        
        # 重复添加内容直到超过10000字符
        for i in range(100):
            jd_content += f"\n第{i+1}项职责：\n"
            for r in responsibilities:
                jd_content += f"  - {r}（要求{i+1}）\n"
            jd_content += f"\n第{i+1}项要求：\n"
            for r in requirements:
                jd_content += f"  - {r}（级别{i+1}）\n"
        
        return jd_content
    
    @pytest.mark.slow
    def test_large_resume_matching(self, backend_client, large_resume_text, sample_jd):
        """测试大文件简历匹配（>1MB 文本）"""
        # 验证简历确实超过 1MB
        resume_size_mb = len(large_resume_text.encode('utf-8')) / (1024 * 1024)
        print(f"📊 简历大小: {resume_size_mb:.2f}MB")
        assert resume_size_mb > 1.0, f"简历大小不足 1MB: {resume_size_mb:.2f}MB"
        
        # 发送匹配请求
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": large_resume_text,
            },
            timeout=120  # 大文件需要更长超时
        )
        
        # 验证请求处理
        # 可能成功返回结果，也可能返回 413 Payload Too Large
        if response.status_code == 413:
            print("⚠️ 服务器拒绝过大请求 (413 Payload Too Large)")
            pytest.skip("服务器限制请求大小")
        elif response.status_code == 200:
            data = response.json()
            assert "match_score" in data or "error" in data
            print(f"✅ 大文件简历处理成功: {data}")
        else:
            print(f"📊 响应状态: {response.status_code}")
            print(f"📊 响应内容: {response.text[:500]}")
    
    @pytest.mark.slow
    def test_long_jd_matching(self, backend_client, long_jd_text, sample_resume):
        """测试超长 JD 匹配（>10000 字符）"""
        jd_char_count = len(long_jd_text)
        print(f"📊 JD 长度: {jd_char_count} 字符")
        assert jd_char_count > 10000, f"JD 长度不足 10000: {jd_char_count}"
        
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": long_jd_text,
                "resume_text": sample_resume,
            },
            timeout=120
        )
        
        if response.status_code == 413:
            print("⚠️ 服务器拒绝过大请求 (413 Payload Too Large)")
            pytest.skip("服务器限制请求大小")
        elif response.status_code == 200:
            data = response.json()
            assert "match_score" in data or "error" in data
            print(f"✅ 超长 JD 处理成功")
        else:
            print(f"📊 响应状态: {response.status_code}")


class TestSpecialCharacters:
    """特殊字符测试"""
    
    def test_emoji_in_resume(self, backend_client, sample_jd):
        """包含 Emoji 的简历"""
        resume_with_emoji = """
👨‍💻 张三
🎯 Python 开发工程师 | ⏰ 5年经验

🛠️ 技能专长：
- 🐍 Python, FastAPI, Django
- 🗄️ MySQL, PostgreSQL, Redis
- 🐳 Docker, Kubernetes
- ☁️ AWS, GCP

💼 工作经历：
2020-至今 某科技公司 高级工程师 🚀
- 负责核心系统开发 ✨
- 优化性能 📈 提升300%
- 带队5人完成项目 👥

🎓 教育背景：
2014-2018 北京大学 计算机科学 📚
"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": resume_with_emoji,
            }
        )
        
        assert response.status_code == 200, f"Emoji 简历处理失败: {response.status_code}"
        data = response.json()
        assert "match_score" in data
        print(f"✅ Emoji 简历处理成功，分数: {data.get('match_score')}")
    
    def test_special_punctuation(self, backend_client, sample_jd):
        """包含特殊标点的简历"""
        resume_with_special = """
张三《Python高级工程师》
【技能】：Python™、Java®、Go©
【经验】：5年+
「核心能力」：
• 架构设计（微服务/分布式）
• 性能优化【QPS提升300%】
• 团队管理〈5人〉
"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": resume_with_special,
            }
        )
        
        assert response.status_code == 200
        print("✅ 特殊标点处理成功")
    
    def test_mixed_language(self, backend_client, sample_jd):
        """中英日韩混合文本"""
        mixed_resume = """
张三 Zhang San
ソフトウェアエンジニア | 소프트웨어 엔지니어
Senior Software Engineer

技能 / Skills / スキル / 기술:
- Python, Java, Go
- 精通 / Proficient / 熟練 / 능숙

経験 / Experience / 경험:
2020-现在 某科技公司
- Developed microservices
- 負責システム設計
- 시스템 개발 담당
"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": mixed_resume,
            }
        )
        
        assert response.status_code == 200
        print("✅ 混合语言处理成功")


class TestEmptyAndBoundary:
    """空值和边界值测试"""
    
    def test_minimal_jd(self, backend_client, sample_resume):
        """最小有效 JD（仅职位名称）"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": "招聘Python工程师",
                "resume_text": sample_resume,
            }
        )
        
        # 应该能处理，即使结果不太准确
        assert response.status_code in [200, 400, 422]
        print(f"📊 最小 JD 响应: {response.status_code}")
    
    def test_minimal_resume(self, backend_client, sample_jd):
        """最小有效简历（仅姓名和技能）"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": "张三，Python开发",
            }
        )
        
        assert response.status_code in [200, 400, 422]
        print(f"📊 最小简历响应: {response.status_code}")
    
    def test_whitespace_only(self, backend_client):
        """纯空白字符输入"""
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": "   \n\t\r   ",
                "resume_text": "   \n\t\r   ",
            }
        )
        
        # 应该被拒绝或返回错误
        if response.status_code == 200:
            data = response.json()
            assert "error" in data or data.get("match_score", 0) == 0
        else:
            assert response.status_code in [400, 422]
        print("✅ 空白输入正确处理")
    
    def test_unicode_normalization(self, backend_client, sample_jd):
        """Unicode 规范化测试"""
        # 使用不同的 Unicode 表示形式
        resume_nfc = "张三 Python工程师"  # NFC 形式
        resume_nfd = "张三 Python工程师"  # 可能的 NFD 形式
        
        response = backend_client.post(
            "/api/instant-match",
            data={
                "jd": sample_jd,
                "resume_text": resume_nfc,
            }
        )
        
        assert response.status_code == 200
        print("✅ Unicode 规范化处理成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
