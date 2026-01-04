-- 测试数据生成 SQL - 大规模版本
-- 用户 ID: 5
-- 生成 50 个候选人

-- 清理旧数据
DELETE FROM candidate_index WHERE candidate_id IN (SELECT id FROM candidates WHERE user_id = 5);
DELETE FROM candidates WHERE user_id = 5;

-- ============== Python 开发方向 (10人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '张伟', 'zhangwei@test.com', '13800000001', '北京', 5, '高级Python开发工程师', '阿里巴巴', ARRAY['Python','FastAPI','Django','PostgreSQL','Redis','Docker','Kubernetes'], 'active', NOW(), NOW()),
(5, '李强', 'liqiang@test.com', '13800000002', '上海', 3, 'Python后端工程师', '腾讯', ARRAY['Python','Flask','MySQL','MongoDB','RabbitMQ'], 'active', NOW(), NOW()),
(5, '王芳', 'wangfang@test.com', '13800000003', '深圳', 7, 'Python架构师', '字节跳动', ARRAY['Python','Django','Celery','Elasticsearch','AWS','微服务'], 'active', NOW(), NOW()),
(5, '刘明', 'liuming@test.com', '13800000004', '杭州', 2, '初级Python开发', '网易', ARRAY['Python','Flask','SQLite','Git'], 'active', NOW(), NOW()),
(5, '陈静', 'chenjing@test.com', '13800000005', '广州', 6, 'Python技术专家', '华为', ARRAY['Python','FastAPI','PostgreSQL','Redis','Kafka','容器化'], 'active', NOW(), NOW()),
(5, '赵磊', 'zhaolei@test.com', '13800000006', '成都', 4, 'Python全栈工程师', '美团', ARRAY['Python','Django','Vue.js','MySQL','Docker'], 'active', NOW(), NOW()),
(5, '周洋', 'zhouyang@test.com', '13800000007', '南京', 8, 'Python技术总监', '小米', ARRAY['Python','微服务','分布式系统','团队管理','架构设计'], 'active', NOW(), NOW()),
(5, '吴琳', 'wulin@test.com', '13800000008', '武汉', 1, 'Python实习生', '创业公司', ARRAY['Python','Django','HTML','CSS'], 'active', NOW(), NOW()),
(5, '郑鹏', 'zhengpeng@test.com', '13800000009', '西安', 5, 'Python爬虫工程师', '数据公司', ARRAY['Python','Scrapy','Selenium','MongoDB','数据分析'], 'active', NOW(), NOW()),
(5, '孙悦', 'sunyue@test.com', '13800000010', '苏州', 4, 'Python自动化工程师', '测试公司', ARRAY['Python','pytest','Selenium','Jenkins','CI/CD'], 'active', NOW(), NOW());

-- ============== Java 开发方向 (10人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '钱军', 'qianjun@test.com', '13800000011', '北京', 6, '高级Java开发工程师', '京东', ARRAY['Java','Spring Boot','Spring Cloud','MySQL','Redis','Dubbo'], 'active', NOW(), NOW()),
(5, '孔维', 'kongwei@test.com', '13800000012', '上海', 4, 'Java后端工程师', '拼多多', ARRAY['Java','Spring','MyBatis','RabbitMQ','分布式'], 'active', NOW(), NOW()),
(5, '曹雪', 'caoxue@test.com', '13800000013', '深圳', 8, 'Java架构师', '蚂蚁金服', ARRAY['Java','微服务','DDD','领域驱动设计','中间件'], 'active', NOW(), NOW()),
(5, '谢峰', 'xiefeng@test.com', '13800000014', '杭州', 3, '中级Java开发', '有赞', ARRAY['Java','Spring Boot','MySQL','Git','Linux'], 'active', NOW(), NOW()),
(5, '邹颖', 'zouying@test.com', '13800000015', '广州', 5, 'Java技术专家', '唯品会', ARRAY['Java','Netty','高并发','性能优化','JVM调优'], 'active', NOW(), NOW()),
(5, '金辉', 'jinhui@test.com', '13800000016', '成都', 7, 'Java技术经理', '新希望', ARRAY['Java','Spring Cloud','Kubernetes','团队管理','敏捷开发'], 'active', NOW(), NOW()),
(5, '郝杰', 'haojie@test.com', '13800000017', '南京', 2, '初级Java开发', '苏宁', ARRAY['Java','Spring','JDBC','基础框架'], 'active', NOW(), NOW()),
(5, '顾婷', 'guting@test.com', '13800000018', '武汉', 9, 'Java总架构师', '斗鱼', ARRAY['Java','系统架构','技术规划','分布式事务','微服务治理'], 'active', NOW(), NOW()),
(5, '韩超', 'hanchao@test.com', '13800000019', '西安', 4, 'Java安全工程师', '安全公司', ARRAY['Java','安全编码','渗透测试','代码审计'], 'active', NOW(), NOW()),
(5, '杨帆', 'yangfan@test.com', '13800000020', '苏州', 6, 'Java大数据工程师', '大数据公司', ARRAY['Java','Hadoop','Spark','Flink','数据湖'], 'active', NOW(), NOW());

-- ============== 前端开发方向 (10人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '林涛', 'lintao@test.com', '13800000021', '北京', 4, '高级前端工程师', '百度', ARRAY['JavaScript','TypeScript','React','Redux','Webpack','Node.js'], 'active', NOW(), NOW()),
(5, '何敏', 'hemin@test.com', '13800000022', '上海', 3, 'Vue.js开发工程师', 'B站', ARRAY['JavaScript','Vue.js','Vuex','Element UI','CSS3'], 'active', NOW(), NOW()),
(5, '罗刚', 'luogang@test.com', '13800000023', '深圳', 6, '前端架构师', '微信', ARRAY['JavaScript','React','微前端','性能优化','工程化'], 'active', NOW(), NOW()),
(5, '马丽', 'mali@test.com', '13800000024', '杭州', 2, '前端开发工程师', '蘑菇街', ARRAY['JavaScript','Vue.js','SCSS','移动端适配'], 'active', NOW(), NOW()),
(5, '范波', 'fanbo@test.com', '13800000025', '广州', 5, '全栈工程师', '虎牙', ARRAY['JavaScript','React','Node.js','Express','MongoDB'], 'active', NOW(), NOW()),
(5, '梁欢', 'lianghuan@test.com', '13800000026', '成都', 7, '前端技术总监', '字节跳动', ARRAY['JavaScript','技术管理','前端架构','团队建设','技术规划'], 'active', NOW(), NOW()),
(5, '施琪', 'shiqi@test.com', '13800000027', '南京', 1, '前端实习生', '创业公司', ARRAY['HTML','CSS','JavaScript','jQuery'], 'active', NOW(), NOW()),
(5, '姜浩', 'jianghao@test.com', '13800000028', '武汉', 4, 'React Native工程师', '跨平台公司', ARRAY['React Native','JavaScript','iOS','Android','跨平台开发'], 'active', NOW(), NOW()),
(5, '崔阳', 'cuiyang@test.com', '13800000029', '西安', 3, 'Angular开发工程师', '外企', ARRAY['TypeScript','Angular','RxJS','NgRx','企业应用'], 'active', NOW(), NOW()),
(5, '熊飞', 'xiongfei@test.com', '13800000030', '苏州', 5, '小程序开发工程师', '电商公司', ARRAY['微信小程序','uni-app','Taro','支付宝小程序'], 'active', NOW(), NOW());

-- ============== DevOps/运维方向 (5人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '唐鑫', 'tangxin@test.com', '13800000031', '北京', 5, '高级DevOps工程师', '阿里云', ARRAY['Linux','Docker','Kubernetes','Ansible','Terraform','CI/CD'], 'active', NOW(), NOW()),
(5, '邓勇', 'dengyong@test.com', '13800000032', '上海', 3, 'SRE工程师', '谷歌', ARRAY['Linux','Kubernetes','Prometheus','Grafana','故障排查'], 'active', NOW(), NOW()),
(5, '江丽', 'jiangli@test.com', '13800000033', '深圳', 7, '运维架构师', '腾讯云', ARRAY['云计算','AWS','阿里云','容器编排','自动化运维'], 'active', NOW(), NOW()),
(5, '蔡明', 'caiming@test.com', '13800000034', '杭州', 4, '云平台工程师', '华为云', ARRAY['OpenStack','VMware','网络架构','存储','虚拟化'], 'active', NOW(), NOW()),
(5, '丁伟', 'dingwei@test.com', '13800000035', '广州', 6, '安全运维工程师', '安全厂商', ARRAY['安全运维','防火墙','WAF','漏洞修复','安全加固'], 'active', NOW(), NOW());

-- ============== AI/机器学习方向 (5人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '贾涛', 'jiatao@test.com', '13800000036', '北京', 6, 'AI算法专家', '商汤科技', ARRAY['Python','PyTorch','TensorFlow','计算机视觉','深度学习'], 'active', NOW(), NOW()),
(5, '潘晓', 'panxiao@test.com', '13800000037', '上海', 4, '机器学习工程师', '旷视科技', ARRAY['Python','机器学习','Scikit-learn','特征工程','模型部署'], 'active', NOW(), NOW()),
(5, '田甜', 'tiantian@test.com', '13800000038', '深圳', 8, 'AI研究员', '腾讯AI Lab', ARRAY['深度学习','自然语言处理','BERT','GPT','LLM'], 'active', NOW(), NOW()),
(5, '龚明', 'gongming@test.com', '13800000039', '杭州', 3, '推荐算法工程师', '阿里妈妈', ARRAY['Python','推荐系统','协同过滤','深度推荐','实时计算'], 'active', NOW(), NOW()),
(5, '魏宁', 'weining@test.com', '13800000040', '广州', 5, '语音算法工程师', '讯飞', ARRAY['Python','语音识别','语音合成','信号处理','Kaldi'], 'active', NOW(), NOW());

-- ============== 数据方向 (5人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '薛辉', 'xuehui@test.com', '13800000041', '北京', 5, '大数据工程师', '滴滴', ARRAY['Hadoop','Spark','Hive','Kafka','Flink','数据仓库'], 'active', NOW(), NOW()),
(5, '沈洁', 'shenjie@test.com', '13800000042', '上海', 4, '数据分析师', '携程', ARRAY['SQL','Python','数据分析','Tableau','PowerBI','统计学'], 'active', NOW(), NOW()),
(5, '雷鸣', 'leiming@test.com', '13800000043', '深圳', 6, 'ETL工程师', '数据公司', ARRAY['ETL','Informatica','数据集成','数据清洗','数据治理'], 'active', NOW(), NOW()),
(5, '白雪', 'baixue@test.com', '13800000044', '杭州', 3, '数据产品经理', '阿里', ARRAY['数据产品','指标体系','数据可视化','需求分析','商业分析'], 'active', NOW(), NOW()),
(5, '闫伟', 'yanwei@test.com', '13800000045', '广州', 7, '数据架构师', '美团', ARRAY['数据架构','元数据管理','数据治理','数据安全','数据建模'], 'active', NOW(), NOW());

-- ============== 测试方向 (5人) ==============
INSERT INTO candidates (user_id, name, email, phone, location, years_experience, current_title, current_company, skills, status, created_at, updated_at) VALUES
(5, '任磊', 'renlei@test.com', '13800000046', '北京', 4, '高级测试工程师', '小米', ARRAY['自动化测试','Selenium','Appium','Python','测试框架'], 'active', NOW(), NOW()),
(5, '柳薇', 'liuwei@test.com', '13800000047', '上海', 3, '性能测试工程师', '网易', ARRAY['JMeter','LoadRunner','性能测试','压力测试','性能调优'], 'active', NOW(), NOW()),
(5, '段鹏', 'duanpeng@test.com', '13800000048', '深圳', 5, '测试开发工程师', '华为', ARRAY['测试开发','持续集成','测试框架开发','Jenkins','Docker'], 'active', NOW(), NOW()),
(5, '石娟', 'shijuan@test.com', '13800000049', '杭州', 2, '功能测试工程师', '蘑菇街', ARRAY['功能测试','测试用例设计','Bug管理','Jira'], 'active', NOW(), NOW()),
(5, '龙飞', 'longfei@test.com', '13800000050', '广州', 6, '测试经理', '快手', ARRAY['测试管理','测试体系建设','团队管理','质量保障'], 'active', NOW(), NOW());

-- 为所有候选人创建索引
INSERT INTO candidate_index (candidate_id, lexical_tsv, embedding, filters_json, features_json, embedding_version, index_updated_at)
SELECT 
    c.id,
    to_tsvector('simple', c.name || ' ' || c.current_title || ' ' || c.current_company || ' ' || array_to_string(c.skills, ' ')),
    (SELECT array_agg(random()*0.2-0.1)::vector(1536) FROM generate_series(1,1536)),
    jsonb_build_object('location', c.location, 'years_experience', c.years_experience),
    jsonb_build_object('title', c.current_title, 'top_skills', c.skills[1:3]),
    1,
    NOW()
FROM candidates c
WHERE c.user_id = 5 AND NOT EXISTS (SELECT 1 FROM candidate_index ci WHERE ci.candidate_id = c.id);

-- 验证
SELECT COUNT(*) as total_candidates FROM candidates WHERE user_id = 5;
SELECT COUNT(*) as total_indexes FROM candidate_index;
SELECT location, COUNT(*) as count FROM candidates WHERE user_id = 5 GROUP BY location ORDER BY count DESC;
