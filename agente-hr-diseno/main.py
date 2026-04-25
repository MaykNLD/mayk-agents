"""
agente-hr-diseno — Capa 1b del sistema Career-Ops Unificado
Genera el CV en HTML premium (ATS-bypass, print-to-PDF).
Convierte a PDF con WeasyPrint y sube a Supabase Storage.
"""
import os, json, hashlib, base64, time
import urllib.request, urllib.error
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from llm_client import call_llm
from supabase_career import (get_perfil_by_id, get_latest_approved_cv,
                              update_cv_version_pdf, create_cv_version)

app = FastAPI(title="agente-hr-diseno", version="1.0.0")
AGENT_ID = "agente-hr-diseno"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")


# ── Modelos ──────────────────────────────────────────────────────────
class GenerarCVRequest(BaseModel):
    perfil_id: str
    cv_version_id: Optional[str] = None   # Si None, usa el último aprobado
    foto_modo: Optional[str] = "sin_foto"  # sin_foto | placeholder | con_foto
    foto_url: Optional[str] = None
    idioma: Optional[str] = "ES"

class GenerarCVResponse(BaseModel):
    perfil_id: str
    version_id: Optional[str]
    html_cv: str
    pdf_url: Optional[str]
    secciones_detectadas: list
    advertencias: list


# ── Endpoints ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "version": "1.0.0"}


@app.post("/generar-cv-html", response_model=GenerarCVResponse)
def generar_cv_html(req: GenerarCVRequest):
    """
    Genera el CV en HTML premium usando el CV mejorado de Supabase.
    Intenta convertir a PDF con WeasyPrint y subir a Supabase Storage.
    """
    perfil = get_perfil_by_id(req.perfil_id)
    if not perfil:
        raise HTTPException(status_code=404, detail=f"Perfil {req.perfil_id} no encontrado")

    # Obtener texto del CV (de la versión específica o la última aprobada)
    cv_texto = perfil.get("cv_markdown", "")
    version_id = req.cv_version_id

    if not cv_texto:
        raise HTTPException(
            status_code=400,
            detail="El perfil no tiene cv_markdown. Ejecuta primero /analizar-cv en agente-hr-rrhh."
        )

    nombre   = f"{perfil.get('nombre', '')} {perfil.get('apellido', '')}".strip()
    mercado  = perfil.get("mercado", "")
    linkedin = perfil.get("linkedin", "")
    github   = perfil.get("github_url", "")
    email    = perfil.get("email", "")

    foto_instruccion = {
        "sin_foto":    "sin_foto — diseño cabecera completa a todo ancho sin espacio para foto",
        "placeholder": "placeholder — inserta <div id='foto-candidato' class='foto-placeholder'>[Foto profesional]</div>",
        "con_foto":    f"con_foto — usa <img id='foto-candidato' src='{req.foto_url}' alt='Foto profesional'>",
    }.get(req.foto_modo, "sin_foto")

    user_message = f"""
CANDIDATO: {nombre}
Email: {email}
LinkedIn: {linkedin}
GitHub: {github}
Mercado objetivo: {mercado}
Idioma del CV: {req.idioma}
Modo foto: {foto_instruccion}

CV EN TEXTO PLANO (ya mejorado por RRHH-01):
---
{cv_texto}
---

Genera el HTML del CV siguiendo tus estándares visuales premium.
Responde EXCLUSIVAMENTE con el JSON definido en tu prompt. Sin texto fuera del JSON.
"""

    raw = call_llm(AGENT_ID, user_message, max_tokens=4000)
    resultado = _parse_llm_json(raw)

    if resultado is None:
        raise HTTPException(
            status_code=500,
            detail=f"El agente LLM no devolvió JSON válido. Respuesta: {raw[:300]}"
        )

    html_cv = resultado.get("html_cv", "")
    if not html_cv or not html_cv.strip():
        raise HTTPException(
            status_code=500,
            detail="El LLM devolvio un html_cv vacio. Respuesta truncada o invalida."
        )

    # Generar PDF con WeasyPrint (obligatorio para la descarga premium)
    pdf_url = None
    try:
        from weasyprint import HTML as WP_HTML
        pdf_bytes = WP_HTML(string=html_cv).write_pdf()
        if not pdf_bytes:
            raise RuntimeError("WeasyPrint genero 0 bytes de PDF")
        print(f"[agente-hr-diseno] PDF generado OK: {len(pdf_bytes)} bytes")
        pdf_url = _upload_pdf_to_supabase(pdf_bytes, req.perfil_id)
        if not pdf_url:
            raise RuntimeError("La subida a Supabase Storage devolvio URL vacia")
        print(f"[agente-hr-diseno] PDF subido OK: {pdf_url[:80]}")
        # Actualizar version en Supabase con la URL del PDF y el HTML
        if version_id:
            from supabase_career import _patch
            _patch("cv_versiones", "id", version_id, {
                "html_cv":  html_cv,
                "pdf_url":  pdf_url,
                "aprobado": True,
            })
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="WeasyPrint no esta instalado en el contenedor. Revisa el Dockerfile."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando/subiendo PDF: {str(e)}"
        )

    return GenerarCVResponse(
        perfil_id           = req.perfil_id,
        version_id          = version_id,
        html_cv             = html_cv,
        pdf_url             = pdf_url,
        secciones_detectadas= resultado.get("secciones_detectadas") or [],
        advertencias        = resultado.get("advertencias") or [],
    )


# ── Helpers ──────────────────────────────────────────────────────────
def _parse_llm_json(raw: str) -> Optional[dict]:
    if raw.startswith("ERROR"):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _upload_pdf_to_supabase(pdf_bytes: bytes, perfil_id: str) -> Optional[str]:
    """Sube el PDF a Supabase Storage y devuelve URL firmada (24h).
    Lanza excepcion si falla — no devuelve None silenciosamente.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL o SUPABASE_KEY no configuradas en el entorno")

    ts       = int(time.time())
    filename = f"{perfil_id}/{ts}_cv.pdf"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/cvs-pdf/{filename}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/pdf",
        "x-upsert":      "true",
    }
    req = urllib.request.Request(upload_url, data=pdf_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
            if status not in (200, 201):
                raise RuntimeError(f"Storage upload devolvio HTTP {status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:300]
        raise RuntimeError(f"Storage upload HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"Storage upload error: {e}")

    # Generar URL firmada (86400 segundos = 24h)
    sign_url = f"{SUPABASE_URL}/storage/v1/object/sign/cvs-pdf/{filename}"
    body_bytes = json.dumps({"expiresIn": 86400}).encode()
    headers2 = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
    }
    req2 = urllib.request.Request(sign_url, data=body_bytes, headers=headers2, method="POST")
    try:
        with urllib.request.urlopen(req2, timeout=10) as r:
            data = json.loads(r.read().decode())
            signed_path = data.get("signedURL", "")
            if not signed_path:
                raise RuntimeError(f"signedURL vacio en la respuesta: {data}")
            return f"{SUPABASE_URL}/storage/v1{signed_path}"
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")[:300]
        raise RuntimeError(f"Storage sign HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"Storage sign error: {e}")
