# report_analyzer_helpers.py — Medical Report Analyzer (standalone module).
# Not used by disease ML pipeline. Heuristic parsing + demo reference bands only — not a diagnostic device.

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Report Analyzer: max upload size (bytes) for safe in-memory handling.
MAX_UPLOAD_BYTES = 15 * 1024 * 1024

# Report Analyzer: cap extracted text length to avoid runaway memory on odd PDFs.
MAX_EXTRACT_CHARS = 400_000


@dataclass
class LabFinding:
    """Report Analyzer: one parsed parameter with a display string and status label."""

    key: str
    label: str
    value_display: str
    status: str  # "Normal" | "High" | "Low" | "Unknown"
    note: str


def validate_upload_bytes(data: bytes) -> Optional[str]:
    """Report Analyzer: return error message if upload is unsafe/too large, else None."""
    if not data:
        return "Empty file."
    if len(data) > MAX_UPLOAD_BYTES:
        return f"File exceeds maximum size ({MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."
    return None


# Report Analyzer: max PDF pages to OCR (scanned reports) to keep runs responsive.
_MAX_PDF_OCR_PAGES = 25


def _configure_tesseract_cmd() -> None:
    """
    Report Analyzer: point pytesseract at tesseract.exe when it is installed but not on PATH.
    Checks TESSERACT_CMD, PATH (where), then common Windows install locations.
    """
    import os
    import shutil

    try:
        import pytesseract
    except ImportError:
        return

    candidates: List[str] = []
    env = (os.environ.get("TESSERACT_CMD") or "").strip().strip('"')
    if env:
        candidates.append(env)
    which = shutil.which("tesseract")
    if which:
        candidates.append(which)
    local = os.environ.get("LOCALAPPDATA", "")
    candidates.extend(
        [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(local, r"Programs\Tesseract-OCR\tesseract.exe") if local else "",
        ]
    )
    for p in candidates:
        if p and os.path.isfile(p):
            pytesseract.pytesseract.tesseract_cmd = p
            return


def _tesseract_available() -> bool:
    """Report Analyzer: True if Tesseract binary is callable by pytesseract."""
    try:
        import pytesseract

        _configure_tesseract_cmd()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ocr_unavailable_help() -> str:
    """Report Analyzer: user-facing hint when no OCR engine is available."""
    return (
        "Scanned PDFs need OCR. Easiest on Windows without Tesseract: run "
        "`pip install easyocr opencv-python-headless` (adds ~100MB+ PyTorch/models on first use), "
        "restart Streamlit, and try again. "
        "Alternatively install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki "
        "and tick 'Add to PATH' or set TESSERACT_CMD to tesseract.exe. "
        "You can also paste lab text instead of uploading a scan."
    )


def _easyocr_importable() -> bool:
    """Report Analyzer: True if easyocr package is installed (reader may still fail to init)."""
    try:
        import easyocr  # noqa: F401

        return True
    except ImportError:
        return False


class _EasyOCRSingleton:
    """Report Analyzer: lazy EasyOCR reader (heavy first-time model download)."""

    reader: Any = None
    init_failed: bool = False


def _get_easyocr_reader():
    """Report Analyzer: return easyocr.Reader or None if import/init failed."""
    if _EasyOCRSingleton.init_failed:
        return None
    if _EasyOCRSingleton.reader is not None:
        return _EasyOCRSingleton.reader
    try:
        import easyocr

        _EasyOCRSingleton.reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return _EasyOCRSingleton.reader
    except Exception:
        _EasyOCRSingleton.init_failed = True
        return None


def _any_ocr_available() -> bool:
    """Report Analyzer: Tesseract works OR easyocr is installed."""
    return _tesseract_available() or _easyocr_importable()


def _plumber_page_to_pil_rgb(page) -> Any:
    """Report Analyzer: render pdfplumber page to RGB PIL image."""
    try:
        rendered = page.to_image(resolution=300)
        img = getattr(rendered, "original", None)
        if img is None:
            return None
        if img.mode == "RGBA":
            return img.convert("RGB")
        if img.mode not in ("RGB", "L"):
            return img.convert("RGB")
        if img.mode == "L":
            return img.convert("RGB")
        return img
    except Exception:
        return None


def _ocr_pil_tesseract(img) -> str:
    """Report Analyzer: run Tesseract on a PIL image."""
    try:
        import pytesseract

        _configure_tesseract_cmd()
        if not _tesseract_available():
            return ""
        best = ""
        for cfg in ("--psm 6", "--psm 4", "--psm 3"):
            chunk = (pytesseract.image_to_string(img, config=cfg) or "").strip()
            if len(chunk) > len(best):
                best = chunk
        return best
    except Exception:
        return ""


def _ocr_pil_easyocr(img) -> str:
    """Report Analyzer: run EasyOCR on a PIL image (no Tesseract binary required)."""
    reader = _get_easyocr_reader()
    if reader is None:
        return ""
    try:
        import numpy as np

        arr = np.array(img.convert("RGB"))
        lines = reader.readtext(arr, detail=0, paragraph=False)
        if isinstance(lines, str):
            return lines.strip()
        return "\n".join(lines).strip() if lines else ""
    except Exception:
        return ""


def _ocr_pdf_page_plumber(page) -> Tuple[str, str]:
    """
    Report Analyzer: OCR one PDF page. Returns (text, engine) where engine is
    'tesseract', 'easyocr', or ''.
    """
    img = _plumber_page_to_pil_rgb(page)
    if img is None:
        return "", ""

    tess_text = _ocr_pil_tesseract(img)
    if len(tess_text.strip()) >= 35:
        return tess_text, "tesseract"

    easy_text = _ocr_pil_easyocr(img)
    if len(easy_text.strip()) > len(tess_text.strip()):
        return easy_text, "easyocr" if easy_text.strip() else ""

    if tess_text.strip():
        return tess_text, "tesseract"
    if easy_text.strip():
        return easy_text, "easyocr"
    return "", ""


def extract_text_from_pdf(data: bytes) -> Tuple[str, Optional[str]]:
    """
    Report Analyzer: extract text from PDF — embedded text first, then per-page OCR for scans.
    """
    err_parts: List[str] = []
    note: Optional[str] = None

    try:
        import pdfplumber

        direct_chunks: List[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = list(pdf.pages)
            for page in pages:
                t = page.extract_text() or ""
                if t.strip():
                    direct_chunks.append(t)
            merged_direct = "\n".join(direct_chunks).strip()

            merged_ocr = ""
            if len(merged_direct) < 150:
                if not _any_ocr_available():
                    err_parts.append(_ocr_unavailable_help())
                else:
                    ocr_chunks: List[str] = []
                    engines: set = set()
                    for i, page in enumerate(pages):
                        if i >= _MAX_PDF_OCR_PAGES:
                            break
                        ot, eng = _ocr_pdf_page_plumber(page)
                        if ot:
                            ocr_chunks.append(ot)
                        if eng:
                            engines.add(eng)
                    merged_ocr = "\n".join(ocr_chunks).strip()
                    if merged_ocr:
                        if engines == {"easyocr"}:
                            note = (
                                "Used EasyOCR on PDF pages (Tesseract not used or weak). "
                                "First EasyOCR run may download models (~100MB+)."
                            )
                        elif "easyocr" in engines:
                            note = "Used Tesseract and/or EasyOCR on PDF pages (scanned report)."
                        else:
                            note = "Used OCR on PDF pages (image-based or scanned report)."

            if len(merged_ocr) > len(merged_direct):
                text = merged_ocr
            else:
                text = merged_direct

            if text:
                return text[:MAX_EXTRACT_CHARS], note
    except Exception as e:
        err_parts.append(f"pdfplumber: {e}")

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(data))
        chunks = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                chunks.append(t)
        text = "\n".join(chunks).strip()
        if text:
            return text[:MAX_EXTRACT_CHARS], None
    except Exception as e:
        err_parts.append(f"PyPDF2: {e}")

    hint = "No text found in PDF."
    if err_parts:
        hint += " " + " ".join(err_parts)
    elif not _any_ocr_available():
        hint += " " + _ocr_unavailable_help()
    else:
        hint += " OCR ran but could not read text — try a higher-resolution scan or paste lab lines as text."
    return "", hint


def extract_text_from_image(data: bytes) -> Tuple[str, Optional[str]]:
    """Report Analyzer: OCR image — Tesseract if available, else EasyOCR."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        if _tesseract_available():
            import pytesseract

            _configure_tesseract_cmd()
            text = (pytesseract.image_to_string(img) or "").strip()
            if text:
                return text[:MAX_EXTRACT_CHARS], None

        ez = _ocr_pil_easyocr(img)
        if ez.strip():
            note = None
            if not _tesseract_available():
                note = "Used EasyOCR (Tesseract not available; first run may download models)."
            return ez[:MAX_EXTRACT_CHARS], note

        if not _any_ocr_available():
            return "", _ocr_unavailable_help()
        return "", "OCR could not read this image — try a clearer scan or paste text."
    except Exception as e:
        return "", str(e)


def extract_text_from_plain(data: bytes) -> Tuple[str, Optional[str]]:
    """Report Analyzer: decode plain text / pasted-style reports."""
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)[:MAX_EXTRACT_CHARS], None
        except UnicodeDecodeError:
            continue
    return "", "Could not decode text file."


def _float_token(s: str) -> Optional[float]:
    s = s.replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _first_match(patterns: List[str], text: str) -> Optional[re.Match]:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m
    return None


def _status_glucose(val_mg_dl: float) -> Tuple[str, str]:
    if val_mg_dl < 70:
        return "Low", "Below typical fasting lower bound (demo band)."
    if val_mg_dl <= 99:
        return "Normal", "Within common fasting glucose reference (demo)."
    if val_mg_dl <= 125:
        return "High", "Above typical fasting upper bound — confirm with lab/clinician (demo)."
    return "High", "Well above typical fasting upper bound (demo)."


def _status_hemoglobin(val: float) -> Tuple[str, str]:
    if val < 12.0:
        return "Low", "Below broad adult lower reference (demo)."
    if val <= 17.5:
        return "Normal", "Within broad adult hemoglobin band (demo)."
    return "High", "Above broad adult upper reference (demo)."


def _status_cholesterol_total(val: float) -> Tuple[str, str]:
    if val < 200:
        return "Normal", "Below 200 mg/dL total cholesterol (common lab cut-off, demo)."
    if val < 240:
        return "High", "Borderline/high range — follow up clinically (demo)."
    return "High", "High range — follow up clinically (demo)."


def _status_wbc(val: float) -> Tuple[str, str]:
    if val < 4.5:
        return "Low", "Below common WBC lower bound x10^3/uL (demo)."
    if val <= 11.0:
        return "Normal", "Within common WBC band (demo)."
    return "High", "Above common WBC upper bound (demo)."


def _status_rbc(val: float) -> Tuple[str, str]:
    if val < 4.0:
        return "Low", "Below broad RBC lower bound (demo)."
    if val <= 5.9:
        return "Normal", "Within broad RBC band (demo)."
    return "High", "Above broad RBC upper bound (demo)."


def _normalize_platelet_count(raw: float) -> float:
    """Report Analyzer: express platelets in x10^3/uL (approx) for rules."""
    if raw >= 1000:
        return raw / 1000.0
    return raw


def _status_platelets(val_k: float) -> Tuple[str, str]:
    if val_k < 150:
        return "Low", "Below common lower bound (x10^3/uL equivalent, demo)."
    if val_k <= 450:
        return "Normal", "Within common platelet band (demo)."
    return "High", "Above common upper bound (demo)."


def _status_bp(sys: float, dia: float) -> Tuple[str, str]:
    if sys < 90 or dia < 60:
        return "Low", "Hypotension-style reading vs common demo thresholds."
    if sys < 120 and dia < 80:
        return "Normal", "Within common normal BP band (demo)."
    if sys < 130 and dia < 80:
        return "High", "Elevated systolic vs common demo threshold."
    if sys >= 130 or dia >= 80:
        return "High", "Above common normal BP thresholds (demo)."
    return "Normal", "Within mixed thresholds (demo)."


def parse_lab_findings(text: str) -> List[LabFinding]:
    """Report Analyzer: regex/heuristic extraction of common labs from free text."""
    if not text or not text.strip():
        return []

    findings: List[LabFinding] = []
    seen: set = set()

    def add(
        key: str,
        label: str,
        display: str,
        status: str,
        note: str,
    ) -> None:
        if key in seen:
            return
        seen.add(key)
        findings.append(LabFinding(key=key, label=label, value_display=display, status=status, note=note))

    # Glucose (mg/dL or mmol/L) — expanded labels for real lab PDFs / OCR output
    gm = _first_match(
        [
            r"(?:fasting\s*)?(?:blood\s*glucose|blood\s*sugar|plasma\s*glucose|serum\s*glucose|s\.?\s*glucose|glucose|fbs|rbs|bsl)\s*[:=\-]?\s*([\d.,]+)\s*(mg/dl|mg/ldl|mmol/l|mmol)?",
            r"(?:random\s*blood\s*sugar)\s*[:=\-]?\s*([\d.,]+)\s*(mg/dl|mmol/l)?",
            r"\b(?:rbs|fbs)\b\s*[:=\-]?\s*([\d.,]+)\s*(mg/dl|mmol/l)?",
            r"(?:^|[\s,|])(?:glucose|sugar)\s*[:=\-]\s*([\d.,]+)\s*(mg/dl|mmol/l)?",
        ],
        text,
    )
    if gm:
        v = _float_token(gm.group(1))
        if v is not None:
            unit = (gm.group(2) or "mg/dl").lower()
            if "mmol" in unit:
                v_mg = v * 18.0182
                disp = f"{v:.2f} mmol/L (~{v_mg:.0f} mg/dL)"
            else:
                v_mg = v
                disp = f"{v:.0f} mg/dL" if v == int(v) else f"{v:.1f} mg/dL"
            st, nt = _status_glucose(v_mg)
            add("glucose", "Glucose", disp, st, nt)

    # Hemoglobin — allow line breaks after label (OCR / table layouts)
    hm = _first_match(
        [
            r"(?:hemoglobin|haemoglobin|h\.?\s*g\.?|hgb)\s*[:=\-\s]*([\d.,]+)\s*(g/dl|gms/dl|gm/dl|g/ldl)?",
            r"\bhb\b\s*[:=\-\s]*([\d.,]+)\s*(g/dl)?",
        ],
        text,
    )
    if hm:
        v = _float_token(hm.group(1))
        if v is not None:
            disp = f"{v:.1f} g/dL"
            st, nt = _status_hemoglobin(v)
            add("hemoglobin", "Hemoglobin", disp, st, nt)

    # Total cholesterol (avoid matching HDL/LDL as total if possible — prefer explicit total)
    cm = _first_match(
        [
            r"total\s*cholesterol\s*[:=\-]?\s*([\d.,]+)\s*(mg/dl)?",
            r"(?:serum|blood|s\.?)\s*cholesterol\s*[:=\-]?\s*([\d.,]+)\s*(mg/dl)?",
            r"(?:^|[\s,|])cholesterol\s*[:=\-]\s*([\d.,]+)\s*(mg/dl)?",
        ],
        text,
    )
    if cm:
        v = _float_token(cm.group(1))
        if v is not None and v > 40:
            disp = f"{v:.0f} mg/dL" if v == int(v) else f"{v:.1f} mg/dL"
            st, nt = _status_cholesterol_total(v)
            add("cholesterol", "Total cholesterol", disp, st, nt)

    # Blood pressure
    bpm = _first_match(
        [
            r"(?:blood\s*pressure|\bbp\b)\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})",
            r"(?:^|\s)(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mm\s*hg|mmhg)\b",
        ],
        text,
    )
    if bpm:
        sys_v = float(bpm.group(1))
        dia_v = float(bpm.group(2))
        if 50 <= sys_v <= 250 and 30 <= dia_v <= 150:
            disp = f"{int(sys_v)}/{int(dia_v)} mmHg"
            st, nt = _status_bp(sys_v, dia_v)
            add("blood_pressure", "Blood pressure", disp, st, nt)

    # WBC
    wm = _first_match(
        [
            r"(?:wbc|white\s*blood\s*cells?|total\s*leucocyte\s*count|tlc)\s*[:=\-\s]*([\d.,]+)\s*(?:x?\s*10\^?9/l|10\^9/l|k/ul|/cmm|cells?/mm3)?",
        ],
        text,
    )
    if wm:
        v = _float_token(wm.group(1))
        if v is not None:
            v_calc = (v / 1000.0) if v > 50 else v
            if v > 50:
                disp = f"{v:,.0f} /uL (~{v_calc:.2f} x10^3/uL)"
            else:
                disp = f"{v_calc:.2f} x10^3/uL"
            st, nt = _status_wbc(v_calc)
            add("wbc", "WBC", disp, st, nt)

    # RBC
    rm = _first_match(
        [
            r"(?:rbc|red\s*blood\s*cells?)\s*[:=\-\s]*([\d.,]+)\s*(?:x?\s*10\^?12/l|million/ul|m/ul|mill/cumm)?",
        ],
        text,
    )
    if rm:
        v = _float_token(rm.group(1))
        if v is not None:
            disp = f"{v:.2f} x 10^6/uL"
            st, nt = _status_rbc(v)
            add("rbc", "RBC", disp, st, nt)

    # Platelets
    pm = _first_match(
        [
            r"(?:platelet|plt|platelets)\s*(?:count)?\s*[:=\-\s]*([\d.,]+)\s*(?:x?\s*10\^?9/l|k/ul|/ul|cells?/mm3)?",
        ],
        text,
    )
    if pm:
        v = _float_token(pm.group(1))
        if v is not None:
            vk = _normalize_platelet_count(v)
            if v >= 1000:
                disp = f"{v:,.0f} /uL (~{vk:.1f} x10^3/uL)"
            else:
                disp = f"{vk:.0f} x10^3/uL"
            st, nt = _status_platelets(vk)
            add("platelets", "Platelets", disp, st, nt)

    return findings


def build_health_summary(findings: List[LabFinding]) -> str:
    """Report Analyzer: short plain-language summary (non-clinical wording)."""
    if not findings:
        return (
            "No common lab patterns were recognized in this report. "
            "Try a clearer scan, paste key lines, or check that units and labels match typical lab reports."
        )

    abnormal = [f for f in findings if f.status in ("High", "Low")]
    lines = [
        f"We parsed {len(findings)} parameter(s) from the document.",
    ]
    if abnormal:
        lines.append(
            "Values that differ from the built-in demo reference bands: "
            + ", ".join(f"{f.label} ({f.status})" for f in abnormal)
            + "."
        )
        lines.append("Discuss any concerns with a qualified clinician; this tool does not diagnose.")
    else:
        lines.append("Parsed values fall within the app's demo reference bands — still verify with your clinician and official lab report.")

    return " ".join(lines)


def findings_to_dicts(findings: List[LabFinding]) -> List[Dict[str, Any]]:
    """Report Analyzer: serialize for optional JSON/debug."""
    return [
        {
            "key": f.key,
            "label": f.label,
            "value_display": f.value_display,
            "status": f.status,
            "note": f.note,
        }
        for f in findings
    ]


def run_extraction(
    file_bytes: bytes,
    mime_hint: str,
    filename: str,
) -> Tuple[str, Optional[str]]:
    """
    Report Analyzer: route bytes to PDF / image / text extractor by extension and mime.
    Returns (text, error_message).
    """
    name = (filename or "").lower()
    err = validate_upload_bytes(file_bytes)
    if err:
        return "", err

    if name.endswith(".pdf") or "pdf" in mime_hint.lower():
        return extract_text_from_pdf(file_bytes)
    if name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")) or "image" in mime_hint.lower():
        return extract_text_from_image(file_bytes)
    if name.endswith((".txt", ".text", ".csv", ".md")) or "text" in mime_hint.lower():
        return extract_text_from_plain(file_bytes)

    if file_bytes[:4] == b"%PDF":
        return extract_text_from_pdf(file_bytes)
    if file_bytes[:2] in (b"\xff\xd8", b"\x89P") or file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return extract_text_from_image(file_bytes)

    return "", "Unsupported file type. Upload PDF, PNG/JPG, or TXT."
