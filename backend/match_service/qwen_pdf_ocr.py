# -*- coding: utf-8 -*-
"""
Qwen PDF OCR 封装类（支持 pdf_path 或 pdf_bytes）
依赖：pip install pymupdf pillow dashscope
"""

import os, io, base64, json, traceback, tempfile, sys
import fitz
from PIL import Image
from log import logger
import dashscope


class QwenPDFOCR:
    # 优化提示词：明确要求返回纯文本，不要坐标/边界框格式
    DEFAULT_HINT = (
        "请识别图片中的所有文字内容，直接输出纯文本。"
        "要求：1. 只输出文字内容，不要输出坐标、边界框或位置信息；"
        "2. 按从上到下、从左到右的阅读顺序输出；"
        "3. 保留段落换行和项目符号；"
        "4. 不要总结或改写原文；"
        "5. 无法识别的文字用 [?] 标记。"
    )

    def __init__(
        self,
        pdf_path: str | None = None,
        pdf_bytes: bytes | None = None,
        api_key: str = "",
        model: str = "qwen-vl-ocr-2025-11-20",
        region: str = "cn",   # "cn" 国内；"intl" 国际
        dpi: int = 400,
        ocr_hint: str | None = None,
        timeout: tuple[int, int] = (8, 120),
        verbose: bool = True,
    ):
        """
        :param pdf_path: PDF 文件路径（二选一）
        :param pdf_bytes: PDF 的原始字节内容（二选一）
        :param api_key: DashScope API Key
        :param model:   模型名称，默认 qwen-vl-ocr
        :param region:  "cn" 或 "intl"
        :param dpi:     渲染 PDF 位图 DPI
        :param ocr_hint:传给模型的指令
        :param timeout:(connect_timeout, read_timeout)
        :param verbose:打印详细日志
        """
        self.pdf_path = pdf_path
        self.pdf_bytes = pdf_bytes

        self.api_key = api_key
        self.model = model
        self.region = region
        self.dpi = dpi
        self.ocr_hint = ocr_hint or self.DEFAULT_HINT
        self.timeout = timeout
        self.verbose = verbose

        # 清理代理，设置地区 base_url
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "REQUESTS_CA_BUNDLE"):
            os.environ.pop(k, None)
        self._set_base_url(self.region)

    # ------------------ 便捷构造 ------------------
    @staticmethod
    def from_bytes(
        data: bytes,
        api_key: str,
        model: str = "qwen-vl-ocr-2025-11-20",
        region: str = "cn",
        dpi: int = 400,
        ocr_hint: str | None = None,
        timeout: tuple[int, int] = (8, 120),
        verbose: bool = True,
    ) -> "QwenPDFOCR":
        return QwenPDFOCR(
            pdf_path=None,
            pdf_bytes=data,
            api_key=api_key,
            model=model,
            region=region,
            dpi=dpi,
            ocr_hint=ocr_hint,
            timeout=timeout,
            verbose=verbose,
        )

    @staticmethod
    def from_image_bytes(
        data: bytes,
        api_key: str,
        model: str = "qwen-vl-ocr-2025-11-20",
        region: str = "cn",
        ocr_hint: str | None = None,
        timeout: tuple[int, int] = (8, 120),
        verbose: bool = True,
    ) -> tuple[str, dict]:
        """
        直接处理单张图片的OCR（不创建实例，直接返回文本和token使用量）
        :param data: 图片的字节内容
        :param api_key: DashScope API Key
        :param model: 模型名称
        :param region: "cn" 或 "intl"
        :param ocr_hint: OCR提示词
        :param timeout: 超时设置
        :param verbose: 是否打印日志
        :return: (OCR识别的文本, token使用量字典)
        """
        instance = QwenPDFOCR(
            pdf_path=None,
            pdf_bytes=None,
            api_key=api_key,
            model=model,
            region=region,
            dpi=400,
            ocr_hint=ocr_hint,
            timeout=timeout,
            verbose=verbose,
        )
        return instance._ocr_one_image(data)

    # ------------------ 工具方法 ------------------

    @staticmethod
    def _set_base_url(region: str):
        dashscope.base_http_api_url = (
            "https://dashscope.aliyuncs.com/api/v1"
            if region == "cn"
            else "https://dashscope-intl.aliyuncs.com/api/v1"
        )

    @staticmethod
    def _pil_to_jpeg_bytes(img: Image.Image, quality=85) -> bytes:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    @staticmethod
    def _pix_to_pil(pix: fitz.Pixmap) -> Image.Image:
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def _call_qwen(self, messages) -> tuple:
        """调用 Qwen API 并返回响应和 token 使用量"""
        from dashscope import MultiModalConversation
        resp = MultiModalConversation.call(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            stream=False,
            timeout=self.timeout,
        )
        
        # 提取 token 使用量
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        try:
            usage = getattr(resp, "usage", None)
            if usage:
                token_usage["prompt_tokens"] = getattr(usage, "input_tokens", 0) or 0
                token_usage["completion_tokens"] = getattr(usage, "output_tokens", 0) or 0
        except Exception:
            pass
        
        return resp, token_usage

    # ------------------ 坐标格式后处理 ------------------

    @staticmethod
    def _extract_text_from_coordinate_format(text: str) -> str | None:
        """
        尝试从坐标格式中提取纯文本。
        格式示例: "100,32,23,33,90,自" -> "自"
        或: "164,30,25,129,90,项目经历" -> "项目经历"
        """
        if not text:
            return None
        
        lines = text.strip().split("\n")
        extracted = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测是否是坐标格式 (至少有4个逗号分隔的数字开头)
            parts = line.split(",")
            if len(parts) >= 5:
                # 检查前几个部分是否都是数字
                try:
                    # 检查前4个是否是数字（坐标）
                    is_coord_format = all(p.strip().isdigit() for p in parts[:4])
                    if is_coord_format:
                        # 最后一个部分是文本
                        text_part = ",".join(parts[5:]) if len(parts) > 5 else (parts[-1] if not parts[-1].strip().isdigit() else "")
                        if text_part and not text_part.strip().isdigit():
                            extracted.append(text_part.strip())
                        continue
                except:
                    pass
            
            # 不是坐标格式，保留原文
            extracted.append(line)
        
        if extracted:
            result = "\n".join(extracted)
            if len(result) > 10:  # 至少有一些有意义的文本
                return result
        return None

    # ------------------ 响应解析 ------------------

    def _parse_resp(self, resp):
        """稳健解析 Qwen 多模态返回 - 增强版"""
        # 记录状态码等元信息
        for k in ("status_code", "code", "message"):
            v = getattr(resp, k, None)
            if v is not None:
                logger.info(f"    {k} = {v}")

        out = getattr(resp, "output", {}) or {}
        logger.info(f">>> resp.output keys: {list(out.keys()) if isinstance(out, dict) else type(out)}")

        # 方案1: 标准 choices 格式
        choices = out.get("choices") or out.get("outputs") or []
        if choices:
            msg = choices[0].get("message") or choices[0].get("messages", [{}])[0]
            content = msg.get("content", [])
            logger.info(f">>> choices[0].content 类型: {type(content)}")
            
            if isinstance(content, list):
                texts = []
                for c in content:
                    if isinstance(c, dict):
                        # 标准 text 字段
                        if "text" in c:
                            texts.append(c["text"])
                        # 某些版本返回 box 格式: {"box": [x,y,w,h], "text": "内容"}
                        elif "box" in c and isinstance(c.get("box"), list):
                            # 有些响应把文本放在其他字段
                            box_text = c.get("text") or c.get("content") or c.get("label") or ""
                            if box_text:
                                texts.append(str(box_text))
                    elif isinstance(c, str) and c.strip():
                        texts.append(c)
                
                text = "\n".join([t for t in texts if t]).strip()
                if text:
                    logger.info(f">>> 从 choices 解析成功，长度: {len(text)}")
                    return text
            elif isinstance(content, str) and content.strip():
                return content.strip()

        # 方案2: output_text 属性
        ot = None
        try:
            ot = getattr(resp, "output_text", None)
        except Exception:
            ot = None
        if ot:
            logger.info(">>> 使用 resp.output_text 解析成功")
            return str(ot).strip()

        # 方案3: 尝试从原始 dict 提取
        try:
            raw = resp.to_dict() if hasattr(resp, "to_dict") else getattr(resp, "__dict__", {})
            
            # 深度搜索 text 字段
            def find_text_deep(obj, depth=0):
                if depth > 5:
                    return []
                texts = []
                if isinstance(obj, dict):
                    # 直接的 text 字段
                    if "text" in obj and isinstance(obj["text"], str):
                        texts.append(obj["text"])
                    # 遍历所有值
                    for v in obj.values():
                        texts.extend(find_text_deep(v, depth + 1))
                elif isinstance(obj, list):
                    for item in obj:
                        texts.extend(find_text_deep(item, depth + 1))
                return texts
            
            found_texts = find_text_deep(raw)
            if found_texts:
                combined = "\n".join([t for t in found_texts if t and len(t) > 2])
                if combined and len(combined) > 10:
                    logger.info(f">>> 深度搜索解析成功，找到 {len(found_texts)} 段文本")
                    return combined
            
            # 仅记录元信息，不记录原始响应内容（防止简历隐私泄露到日志）
            raw_keys = list(raw.keys()) if isinstance(raw, dict) else str(type(raw))
            logger.warning(f">>> OCR 解析失败 | 响应结构: {raw_keys} | 请检查 API 返回格式")
        except Exception as e:
            logger.warning(f">>> 无法序列化 resp: {e}")

        return None

    # ------------------ 关键 OCR 逻辑 ------------------

    def _ocr_one_image(self, img_bytes: bytes) -> tuple[str, dict]:
        """
        上传策略：
          1) data:url 直接传 {"image": data_url}
          2) 若 SDK 不支持，则落盘到临时文件，改用 {"image": "file://..."}
        
        Returns:
            (text, token_usage) - OCR文本和token使用量
        """
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "model": self.model}
        
        # 方案1：data URL
        try:
            b64 = base64.b64encode(img_bytes).decode("ascii")
            data_url = f"data:image/jpeg;base64,{b64}"
            msgs = [{"role": "user", "content": [{"text": self.ocr_hint}, {"image": data_url}]}]
            logger.info(">>> 尝试方案1: data:url")
            resp, usage = self._call_qwen(msgs)
            token_usage["prompt_tokens"] = usage.get("prompt_tokens", 0)
            token_usage["completion_tokens"] = usage.get("completion_tokens", 0)
            text = self._parse_resp(resp)
            if text:
                return text, token_usage
            else:
                logger.info(">>> 方案1返回不可解析文本，切换到方案2")
        except Exception as e:
            logger.info("❌ 方案1调用异常:", e)
            traceback.print_exc()
            logger.info(">>> 切换到方案2")

        # 方案2：落盘 file://
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(img_bytes)
                tmp_path = f.name
            file_url = f"file://{tmp_path.replace(os.sep, '/')}"
            msgs = [{"role": "user", "content": [{"text": self.ocr_hint}, {"image": file_url}]}]
            logger.info(">>> 尝试方案2: file:// 上传", file_url)
            resp, usage = self._call_qwen(msgs)
            token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            text = self._parse_resp(resp)
            return (text or "[OCR 失败: 无法从响应中解析文本]"), token_usage
        except Exception as e:
            logger.info("❌ 方案2调用异常:", e)
            traceback.print_exc()
            return f"[API调用失败: {e}]", token_usage
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass



    # ------------------ 对外主流程 ------------------

    def run(self, max_workers: int = 10) -> tuple[str, dict]:
        """
        【优化版】执行 PDF 全量 OCR，并发处理页面以提高速度。
        :param max_workers: 并发线程数，根据 API 的 QPS/QPM 限制调整
        :return: (OCR文本, token使用量汇总)
        """
        lines = []
        page_image_bytes_list = []  # 存储所有待处理的页面图像
        
        # 汇总 token 使用量
        total_token_usage = {
            "prompt_tokens": 0, 
            "completion_tokens": 0, 
            "model": self.model,
            "pages": 0
        }

        # --- 阶段1：串行准备所有图像（CPU密集型，保持在主线程）---
        logger.info(f"开始准备 PDF 图像（串行），共 {self.pdf_path or 'bytes data'}...")
        try:
            if self.pdf_bytes:
                doc = fitz.open(stream=self.pdf_bytes, filetype="pdf")
            else:
                doc = fitz.open(self.pdf_path)
        except Exception as e:
            logger.info(f"❌ 打开 PDF 失败: {e}")
            return f"[错误: 无法打开 PDF 文件 {e}]", total_token_usage

        with doc:
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for i, page in enumerate(doc):
                logger.info(f"    正在渲染第 {i + 1} 页...")
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pil_img = self._pix_to_pil(pix)
                img_bytes = self._pil_to_jpeg_bytes(pil_img, quality=85)
                # 存储待处理的数据
                page_image_bytes_list.append((i + 1, img_bytes))

        logger.info(f"✅ 所有页面图像准备完毕，共 {len(page_image_bytes_list)} 页。")
        total_token_usage["pages"] = len(page_image_bytes_list)

        # --- 阶段2：并发执行 OCR（I/O密集型）---
        # 我们需要一个辅助函数来解包元组并调用 _ocr_one_image
        # 这样日志才能正确打印页码
        def ocr_task(page_data: tuple[int, bytes]) -> tuple[int, str, dict]:
            page_num, img_bytes = page_data
            logger.info(f"\n====== [并发] 开始处理第 {page_num} 页 ======")
            logger.info(f">>> 图像大小:", len(img_bytes), "bytes", f"(Page {page_num})")

            # _ocr_one_image 现在返回 (text, token_usage)
            text, usage = self._ocr_one_image(img_bytes)

            if not text:
                text = "[OCR 失败: 未返回文本]"
            logger.info(f"====== [并发] 第 {page_num} 页处理完毕 ======")
            return (page_num, text, usage)

        # 按顺序存储最终结果
        page_results = [None] * len(page_image_bytes_list)
        page_usages = []  # 存储每页的 token 使用量

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 使用 ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            logger.info(f"🚀 启动线程池 (max_workers={max_workers})，开始并发 OCR...")

            # 提交所有任务
            # 我们使用 submit 而不是 map，以便在日志中更好地跟踪
            future_to_page = {
                executor.submit(ocr_task, page_data): page_data[0]
                for page_data in page_image_bytes_list
            }

            processed_count = 0
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_num_result, text_result, usage = future.result()
                    page_results[page_num_result - 1] = text_result  # 放到正确的位置
                    page_usages.append(usage)
                    processed_count += 1
                    logger.info(
                        f"    (进度: {processed_count}/{len(page_image_bytes_list)}) 第 {page_num} 页结果已获取。")
                except Exception as exc:
                    logger.info(f"❌ 第 {page_num} 页在并发处理时发生严重错误: {exc}")
                    traceback.print_exc()
                    page_results[page_num - 1] = f"[OCR 失败: 发生异常 {exc}]"

        logger.info("✅ 所有并发任务完成。")

        # --- 阶段3：汇总结果 ---
        for i, text in enumerate(page_results):
            lines.append(f"===[PAGE {i + 1}]===\n{text}\n")
        
        # 汇总 token 使用量
        for usage in page_usages:
            total_token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            total_token_usage["completion_tokens"] += usage.get("completion_tokens", 0)

        raw_result = "\n".join(lines)
        
        # --- 阶段4：后处理 - 检测并修复坐标格式问题 ---
        # 如果结果包含 OCR 失败标记或看起来像坐标格式，尝试提取纯文本
        if "[OCR 失败" in raw_result or self._looks_like_coordinate_format(raw_result):
            logger.info(">>> 检测到 OCR 失败或坐标格式，尝试后处理提取文本...")
            extracted = self._extract_text_from_coordinate_format(raw_result)
            if extracted and len(extracted) > 50:  # 至少提取出 50 字符的有效内容
                logger.info(f">>> 坐标格式后处理成功，提取文本长度: {len(extracted)}")
                return extracted, total_token_usage
            else:
                logger.warning(f">>> 坐标格式后处理失败或内容过少，返回原始结果")
        
        return raw_result, total_token_usage
    
    @staticmethod
    def _looks_like_coordinate_format(text: str) -> bool:
        """检测文本是否看起来像坐标格式"""
        import re
        # 坐标格式模式: 多行 "数字,数字,数字,..." 开头
        coord_pattern = re.compile(r'^\d+,\d+,\d+,\d+', re.MULTILINE)
        matches = coord_pattern.findall(text)
        # 如果超过 3 行匹配坐标格式，认为是坐标格式
        return len(matches) >= 3

