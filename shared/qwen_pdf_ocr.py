# -*- coding: utf-8 -*-
"""
Qwen PDF OCR 封装类（支持 pdf_path 或 pdf_bytes）
依赖：pip install pymupdf pillow dashscope
"""

import os, io, base64, json, traceback, tempfile, sys
import fitz
from PIL import Image
from .log import logger
import dashscope


class QwenPDFOCR:
    DEFAULT_HINT = (
        "只做逐字转录，不要总结、不翻译、不改写；"
        "按自然阅读顺序输出文本，保留换行和项目符号；无法辨认处用 [UNREADABLE]。"
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

    # ------------------ 响应解析 ------------------

    def _parse_resp(self, resp):
        """稳健解析 Qwen 多模态返回"""
        for k in ("status_code", "code", "message"):
            v = getattr(resp, k, None)
            if v is not None:
                logger.info(f"    {k} = {v}")

        out = getattr(resp, "output", {}) or {}
        logger.info(f">>> resp.output keys: {list(out.keys()) if isinstance(out, dict) else type(out)}")

        choices = out.get("choices") or out.get("outputs") or []
        if choices:
            msg = choices[0].get("message") or choices[0].get("messages", [{}])[0]
            content = msg.get("content", [])
            logger.info(f">>> choices[0].content 类型: {type(content)}")
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
                text = "\n".join([t for t in texts if t]).strip()
                if text:
                    logger.info(f">>> 从 choices 解析成功，长度: {len(text)}")
                    return text
            elif isinstance(content, str) and content.strip():
                return content.strip()

        ot = None
        try:
            ot = getattr(resp, "output_text", None)
        except Exception:
            ot = None
        if ot:
            logger.info(">>> 使用 resp.output_text 解析成功")
            return str(ot).strip()

        # 打印原始结构帮助诊断
        try:
            raw = resp.to_dict() if hasattr(resp, "to_dict") else getattr(resp, "__dict__", {})
            logger.info(">>> 原始响应（截断 2000 字）：")
            logger.info(json.dumps(raw, ensure_ascii=False, indent=2)[:2000])
        except Exception:
            logger.info(f">>> 无法序列化 resp，直接打印对象：{resp}")

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
            logger.info(f"❌ 方案1调用异常: {e}")
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
            logger.info(f">>> 尝试方案2: file:// 上传 {file_url}")
            resp, usage = self._call_qwen(msgs)
            token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            text = self._parse_resp(resp)
            return (text or "[OCR 失败: 无法从响应中解析文本]"), token_usage
        except Exception as e:
            logger.info(f"❌ 方案2调用异常: {e}")
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
            logger.info(f">>> 图像大小: {len(img_bytes)} bytes (Page {page_num})")

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

        return "\n".join(lines), total_token_usage
