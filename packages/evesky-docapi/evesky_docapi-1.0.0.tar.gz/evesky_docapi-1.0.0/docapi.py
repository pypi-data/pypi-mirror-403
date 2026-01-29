"""
DocAPI Python SDK v1.0.0
========================
pip install docapi

Usage:
    from docapi import DocAPI
    api = DocAPI("your_key")
    api.merge(["a.pdf", "b.pdf"]).save("out.pdf")
"""

__version__ = "1.0.0"
__all__ = ["DocAPI", "DocAPIError"]

import os
import requests
from pathlib import Path
from typing import Union, List, Optional, Any

# ============================================================
# Exceptions
# ============================================================

class DocAPIError(Exception):
    """DocAPI 에러"""
    def __init__(self, msg: str, code: int = None):
        self.code = code
        super().__init__(f"[{code}] {msg}" if code else msg)

# ============================================================
# Response
# ============================================================

class Result:
    """API 응답 래퍼"""
    
    def __init__(self, content: bytes, filename: str = "output"):
        self._content = content
        self.filename = filename
    
    @property
    def content(self) -> bytes:
        return self._content
    
    @property
    def size(self) -> int:
        return len(self._content)
    
    def save(self, path: str) -> str:
        """파일 저장"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self._content)
        return str(p.absolute())
    
    def __repr__(self):
        return f"<Result {self.filename} ({self.size:,} bytes)>"

class TextResult:
    """텍스트 응답"""
    
    def __init__(self, text: str):
        self.text = text
    
    def save(self, path: str) -> str:
        Path(path).write_text(self.text, encoding="utf-8")
        return path
    
    def __str__(self):
        return self.text

class JsonResult:
    """JSON 응답"""
    
    def __init__(self, data: Any):
        self.data = data
    
    def save(self, path: str) -> str:
        import json
        Path(path).write_text(json.dumps(self.data, ensure_ascii=False, indent=2))
        return path

# ============================================================
# Client
# ============================================================

class DocAPI:
    """
    DocAPI 클라이언트
    
    Usage:
        api = DocAPI("your_key")
        
        # PDF 병합
        api.merge(["a.pdf", "b.pdf"]).save("merged.pdf")
        
        # PDF 압축
        api.compress("large.pdf").save("small.pdf")
        
        # PDF → Word
        api.to_word("doc.pdf").save("doc.docx")
        
        # 이미지 → PDF
        api.images_to_pdf(["1.jpg", "2.png"]).save("images.pdf")
        
        # HTML → PDF
        api.html_to_pdf("<h1>Hello</h1>").save("hello.pdf")
        
        # URL → PDF
        api.url_to_pdf("https://example.com").save("page.pdf")
        
        # OCR
        text = api.ocr("scan.pdf")
        print(text.text)
    """
    
    BASE = "https://pdf.evesky.net"
    
    def __init__(self, key: str = None, base_url: str = None, timeout: int = 120):
        self.key = key or os.getenv("DOCAPI_KEY")
        if not self.key:
            raise DocAPIError("API 키 필요: DocAPI('key') 또는 DOCAPI_KEY 환경변수")
        self.base = (base_url or os.getenv("DOCAPI_URL") or self.BASE).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {self.key}"
    
    def _req(self, method: str, ep: str, **kw) -> requests.Response:
        """HTTP 요청"""
        try:
            r = self._session.request(method, f"{self.base}{ep}", timeout=self.timeout, **kw)
            if r.status_code == 401:
                raise DocAPIError("인증 실패: API 키 확인", 401)
            if r.status_code == 429:
                raise DocAPIError("요청 한도 초과", 429)
            if r.status_code >= 400:
                raise DocAPIError(r.text or "요청 실패", r.status_code)
            return r
        except requests.exceptions.Timeout:
            raise DocAPIError("타임아웃")
        except requests.exceptions.ConnectionError:
            raise DocAPIError("연결 실패")
    
    def _files(self, paths: Union[str, List[str]], name: str = "files") -> list:
        """파일 준비"""
        if isinstance(paths, str):
            paths = [paths]
        result = []
        for p in paths:
            path = Path(p)
            if not path.exists():
                raise DocAPIError(f"파일 없음: {p}")
            result.append((name, (path.name, open(path, "rb"))))
        return result
    
    def _upload(self, ep: str, files: Union[str, List[str]], data: dict = None) -> Result:
        """파일 업로드 + 처리"""
        prepared = self._files(files)
        try:
            r = self._req("POST", ep, files=prepared, data=data)
            fn = None
            cd = r.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                fn = cd.split("filename=")[-1].strip('"')
            return Result(r.content, fn or "output")
        finally:
            for _, (_, f) in prepared:
                f.close()
    
    # ============================================================
    # PDF 작업
    # ============================================================
    
    def merge(self, files: List[str]) -> Result:
        """PDF 병합"""
        if len(files) < 2:
            raise DocAPIError("2개 이상 파일 필요")
        return self._upload("/v1/pdf/merge", files)
    
    def split(self, file: str, pages: str = None) -> Result:
        """PDF 분할 (pages: '1-3,5,7-10')"""
        return self._upload("/v1/pdf/split", file, {"pages": pages} if pages else None)
    
    def compress(self, file: str, level: str = "medium") -> Result:
        """PDF 압축 (level: low/medium/high)"""
        return self._upload("/v1/pdf/compress", file, {"level": level})
    
    def rotate(self, file: str, angle: int = 90) -> Result:
        """PDF 회전 (90/180/270)"""
        return self._upload("/v1/pdf/rotate", file, {"angle": angle})
    
    def protect(self, file: str, password: str) -> Result:
        """PDF 암호 설정"""
        return self._upload("/v1/pdf/protect", file, {"password": password})
    
    def unlock(self, file: str, password: str) -> Result:
        """PDF 암호 해제"""
        return self._upload("/v1/pdf/unlock", file, {"password": password})
    
    def watermark(self, file: str, text: str, opacity: float = 0.5) -> Result:
        """PDF 워터마크"""
        return self._upload("/v1/pdf/watermark", file, {"text": text, "opacity": opacity})
    
    def to_word(self, file: str) -> Result:
        """PDF → Word"""
        return self._upload("/v1/pdf/to-word", file)
    
    def to_excel(self, file: str) -> Result:
        """PDF → Excel"""
        return self._upload("/v1/pdf/to-excel", file)
    
    def to_images(self, file: str, fmt: str = "png", dpi: int = 150) -> Result:
        """PDF → 이미지 (ZIP)"""
        return self._upload("/v1/pdf/to-images", file, {"format": fmt, "dpi": dpi})
    
    def extract_text(self, file: str) -> TextResult:
        """PDF 텍스트 추출"""
        prepared = self._files(file, "file")
        try:
            r = self._req("POST", "/v1/pdf/extract-text", files=prepared)
            return TextResult(r.json().get("text", ""))
        finally:
            for _, (_, f) in prepared:
                f.close()
    
    def ocr(self, file: str, lang: str = "kor+eng") -> TextResult:
        """PDF OCR"""
        prepared = self._files(file, "file")
        try:
            r = self._req("POST", "/v1/pdf/ocr", files=prepared, data={"language": lang})
            return TextResult(r.json().get("text", ""))
        finally:
            for _, (_, f) in prepared:
                f.close()
    
    # ============================================================
    # 생성
    # ============================================================
    
    def html_to_pdf(self, html: str) -> Result:
        """HTML → PDF"""
        r = self._req("POST", "/v1/html/to-pdf", json={"html": html})
        return Result(r.content, "document.pdf")
    
    def url_to_pdf(self, url: str) -> Result:
        """URL → PDF"""
        r = self._req("POST", "/v1/url/to-pdf", json={"url": url})
        return Result(r.content, "webpage.pdf")
    
    def md_to_pdf(self, md: str) -> Result:
        """Markdown → PDF"""
        r = self._req("POST", "/v1/markdown/to-pdf", json={"markdown": md})
        return Result(r.content, "document.pdf")
    
    def text_to_pdf(self, text: str, title: str = "Document") -> Result:
        """텍스트 → PDF"""
        r = self._req("POST", "/v1/pdf/from-text", json={"text": text, "title": title})
        return Result(r.content, f"{title}.pdf")
    
    # ============================================================
    # 이미지
    # ============================================================
    
    def images_to_pdf(self, files: List[str]) -> Result:
        """이미지 → PDF"""
        return self._upload("/v1/image/to-pdf", files)
    
    def compress_image(self, file: str, quality: int = 80) -> Result:
        """이미지 압축"""
        return self._upload("/v1/image/compress", file, {"quality": quality})
    
    def resize_image(self, file: str, width: int = None, height: int = None) -> Result:
        """이미지 리사이즈"""
        data = {}
        if width: data["width"] = width
        if height: data["height"] = height
        return self._upload("/v1/image/resize", file, data)
    
    def convert_image(self, file: str, fmt: str) -> Result:
        """이미지 변환 (png/jpg/webp)"""
        return self._upload("/v1/image/convert", file, {"format": fmt})
    
    def ocr_image(self, file: str, lang: str = "kor+eng") -> TextResult:
        """이미지 OCR"""
        prepared = self._files(file, "file")
        try:
            r = self._req("POST", "/v1/image/ocr", files=prepared, data={"language": lang})
            return TextResult(r.json().get("text", ""))
        finally:
            for _, (_, f) in prepared:
                f.close()
    
    # ============================================================
    # Excel/Word
    # ============================================================
    
    def excel_to_csv(self, file: str) -> Result:
        """Excel → CSV"""
        return self._upload("/v1/excel/to-csv", file)
    
    def excel_to_json(self, file: str) -> JsonResult:
        """Excel → JSON"""
        prepared = self._files(file, "file")
        try:
            r = self._req("POST", "/v1/excel/to-json", files=prepared)
            return JsonResult(r.json())
        finally:
            for _, (_, f) in prepared:
                f.close()
    
    def excel_to_pdf(self, file: str) -> Result:
        """Excel → PDF"""
        return self._upload("/v1/excel/to-pdf", file)
    
    def word_to_pdf(self, file: str) -> Result:
        """Word → PDF"""
        return self._upload("/v1/word/to-pdf", file)
    
    # ============================================================
    # 유틸
    # ============================================================
    
    def health(self) -> dict:
        """서버 상태"""
        return self._req("GET", "/v1/health").json()
    
    def close(self):
        self._session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        self.close()
