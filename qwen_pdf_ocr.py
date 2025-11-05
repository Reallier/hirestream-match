# -*- coding: utf-8 -*-
"""
Qwen PDF OCR 封装类
依赖：pip install pymupdf pillow dashscope
"""

import os, io, base64, json, traceback, tempfile
import fitz
from PIL import Image


class QwenPDFOCR:
    DEFAULT_HINT = (
        "只做逐字转录，不要总结、不翻译、不改写；"
        "按自然阅读顺序输出文本，保留换行和项目符号；无法辨认处用 [UNREADABLE]。"
    )

    def __init__(
        self,
        pdf_path: str,
        api_key: str,
        model: str = "qwen-vl-ocr",
        region: str = "cn",   # "cn" 国内；"intl" 国际
        dpi: int = 400,
        ocr_hint: str | None = None,
        timeout: tuple[int, int] = (8, 120),
        verbose: bool = True,
    ):
        """
        :param pdf_path: 待 OCR 的 PDF 路径
        :param api_key: DashScope API Key
        :param model:   模型名称，默认 qwen-vl-ocr
        :param region:  "cn" 或 "intl"
        :param dpi:     渲染 PDF 位图 DPI
        :param ocr_hint:传给模型的指令
        :param timeout:(connect_timeout, read_timeout)
        :param verbose:打印详细日志
        """
        self.pdf_path = pdf_path
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

    # ------------------ 工具方法 ------------------

    @staticmethod
    def _set_base_url(region: str):
        import dashscope
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

    def _call_qwen(self, messages):
        from dashscope import MultiModalConversation
        return MultiModalConversation.call(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            stream=False,
            timeout=self.timeout,
        )

    def _log(self, *args):
        if self.verbose:
            print(*args)

    # ------------------ 响应解析 ------------------

    def _parse_resp(self, resp):
        """稳健解析 Qwen 多模态返回"""
        for k in ("status_code", "code", "message"):
            v = getattr(resp, k, None)
            if v is not None:
                self._log(f"    {k} =", v)

        out = getattr(resp, "output", {}) or {}
        self._log(">>> resp.output keys:", list(out.keys()) if isinstance(out, dict) else type(out))

        choices = out.get("choices") or out.get("outputs") or []
        if choices:
            msg = choices[0].get("message") or choices[0].get("messages", [{}])[0]
            content = msg.get("content", [])
            self._log(f">>> choices[0].content 类型: {type(content)}")
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
                text = "\n".join([t for t in texts if t]).strip()
                if text:
                    self._log(">>> 从 choices 解析成功，长度:", len(text))
                    return text
            elif isinstance(content, str) and content.strip():
                return content.strip()

        ot = None
        try:
            ot = getattr(resp, "output_text", None)
        except Exception:
            ot = None
        if ot:
            self._log(">>> 使用 resp.output_text 解析成功")
            return str(ot).strip()

        # 打印原始结构帮助诊断
        try:
            raw = resp.to_dict() if hasattr(resp, "to_dict") else getattr(resp, "__dict__", {})
            self._log(">>> 原始响应（截断 2000 字）：")
            self._log(json.dumps(raw, ensure_ascii=False, indent=2)[:2000])
        except Exception:
            self._log(">>> 无法序列化 resp，直接打印对象：", resp)

        return None

    # ------------------ 关键 OCR 逻辑 ------------------

    def _ocr_one_image(self, img_bytes: bytes) -> str:
        """
        上传策略：
          1) data:url 直接传 {"image": data_url}
          2) 若 SDK 不支持，则落盘到临时文件，改用 {"image": "file://..."}
        """
        # 方案1：data URL
        try:
            b64 = base64.b64encode(img_bytes).decode("ascii")
            data_url = f"data:image/jpeg;base64,{b64}"
            msgs = [{"role": "user", "content": [{"text": self.ocr_hint}, {"image": data_url}]}]
            self._log(">>> 尝试方案1: data:url")
            resp = self._call_qwen(msgs)
            text = self._parse_resp(resp)
            if text:
                return text
            else:
                self._log(">>> 方案1返回不可解析文本，切换到方案2")
        except Exception as e:
            self._log("❌ 方案1调用异常:", e)
            traceback.print_exc()
            self._log(">>> 切换到方案2")

        # 方案2：落盘 file://
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(img_bytes)
                tmp_path = f.name
            file_url = f"file://{tmp_path.replace(os.sep, '/')}"
            msgs = [{"role": "user", "content": [{"text": self.ocr_hint}, {"image": file_url}]}]
            self._log(">>> 尝试方案2: file:// 上传", file_url)
            resp = self._call_qwen(msgs)
            text = self._parse_resp(resp)
            return text or "[OCR 失败: 无法从响应中解析文本]"
        except Exception as e:
            self._log("❌ 方案2调用异常:", e)
            traceback.print_exc()
            return f"[API调用失败: {e}]"
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    # ------------------ 对外主流程 ------------------

    def run(self) -> str:
        """执行 PDF 全量 OCR，返回按页拼接的文本。"""
        lines = []
        with fitz.open(self.pdf_path) as doc:
            zoom = self.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for i, page in enumerate(doc):
                self._log(f"\n====== 处理第 {i+1} 页 ======")
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pil_img = self._pix_to_pil(pix)
                img_bytes = self._pil_to_jpeg_bytes(pil_img, quality=85)
                self._log(">>> 图像大小:", len(img_bytes), "bytes")
                text = self._ocr_one_image(img_bytes)
                if not text:
                    text = "[OCR 失败: 未返回文本]"
                lines.append(f"===[PAGE {i+1}]===\n{text}\n")
        return "\n".join(lines)


# ------------------ 直接运行示例 ------------------
if __name__ == "__main__":
    PDF_PATH = "曲若华.pdf"
    DASHSCOPE_API_KEY = "sk-5e5ae12f981a4b1fab7f40137b9f27cb"   # 填你的 Key
    MODEL = "qwen-vl-ocr"
    REGION = "cn"            # 或 "intl"

    ocr = QwenPDFOCR(
        pdf_path=PDF_PATH,
        api_key=DASHSCOPE_API_KEY,
        model=MODEL,
        region=REGION,
        dpi=400,
        verbose=True,
    )
    result = ocr.run()
    print("\n========== 最终输出 ==========\n")
    print(result)

