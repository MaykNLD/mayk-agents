"""
agente-hr-rrhh — Capa 1 del sistema Career-Ops Unificado
Analiza CV bruto, repara brechas, extrae métricas de impacto.
Guarda resultado en Supabase: perfil_base.cv_markdown + cv_versiones
"""
import os, json, time, hashlib
import urllib.request, urllib.error
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Importar módulos compartidos
import sys
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from llm_client import call_llm
from supabase_career import get_perfil_by_id, update_perfil, create_cv_version

app = FastAPI(title="agente-hr-rrhh", version="1.0.0")

AGENT_ID = "agente-hr-rrhh"


# ── Modelos ──────────────────────────────────────────────────────────
class AnalizarCVRequest(BaseModel):
    perfil_id: str
    cv_texto: str                # Texto completo del CV en bruto
    idioma: Optional[str] = "ES"

class AnalizarCVResponse(BaseModel):
    perfil_id: str
    nivel_detectado: str
    objetivo_profesional: str
    resumen_ejecutivo: str
    skills_clave: list
    brechas_detectadas: str
    cv_mejorado: str
    advertencias: list
    version_id: Optional[str] = None
    model_used: str


# ── Endpoints ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "version": "1.0.0"}


@app.post("/analizar-cv", response_model=AnalizarCVResponse)
def analizar_cv(req: AnalizarCVRequest):
    """
    Analiza el CV bruto del candidato y devuelve el CV mejorado.
    Guarda en Supabase si perfil_id es válido.
    """
    # Obtener perfil base de Supabase
    perfil = get_perfil_by_id(req.perfil_id)
    if not perfil:
        raise HTTPException(status_code=404, detail=f"Perfil {req.perfil_id} no encontrado en Supabase")

    nombre = f"{perfil.get('nombre', '')} {perfil.get('apellido', '')}".strip()
    linkedin = perfil.get("linkedin", "")
    github   = perfil.get("github_url", "")
    mercado  = perfil.get("mercado", "")

    # Construir el mensaje para el LLM
    user_message = f"""
CANDIDATO: {nombre}
LinkedIn: {linkedin}
GitHub: {github}
Mercado objetivo: {mercado}
Idioma de salida: {req.idioma}

CV BRUTO A ANALIZAR:
---
{req.cv_texto}
---

Analiza este CV y responde EXCLUSIVAMENTE con el JSON definido en tu prompt.
"""

    raw = call_llm(AGENT_ID, user_message, max_tokens=3000)

    # Parsear JSON defensivamente
    resultado = _parse_llm_json(raw)
    if resultado is None:
        raise HTTPException(
            status_code=500,
            detail=f"El agente LLM no devolvió JSON válido. Respuesta cruda: {raw[:300]}"
        )

    # Guardar en Supabase
    version_id = None
    try:
        # Actualizar perfil_base con el CV mejorado
        update_perfil(req.perfil_id, {
            "cv_markdown": resultado.get("cv_mejorado", ""),
            "nivel":       resultado.get("nivel_detectado", ""),
            "objetivo":    resultado.get("objetivo_profesional", ""),
        })

        # Crear versión en cv_versiones
        version_record = create_cv_version({
            "perfil_id":     req.perfil_id,
            "version":       1,
            "texto_cv":      resultado.get("cv_mejorado", ""),
            "handoff_json":  {
                "nivel":            resultado.get("nivel_detectado"),
                "skills":           resultado.get("skills_clave", []),
                "brechas":          resultado.get("brechas_detectadas"),
                "advertencias":     resultado.get("advertencias", []),
                "objetivo":         resultado.get("objetivo_profesional"),
                "resumen":          resultado.get("resumen_ejecutivo"),
                "fase":             "RRHH-01_Completa",
                "idioma_objetivo":  req.idioma,
                "mercado":          mercado,
            },
            "aprobado": False,
        })
        version_id = version_record.get("id")
    except Exception as e:
        # No fallar si Supabase falla — devolver el resultado de todas formas
        print(f"[agente-hr-rrhh] Advertencia al guardar en Supabase: {e}")

    return AnalizarCVResponse(
        perfil_id           = req.perfil_id,
        nivel_detectado     = resultado.get("nivel_detectado", ""),
        objetivo_profesional= resultado.get("objetivo_profesional", ""),
        resumen_ejecutivo   = resultado.get("resumen_ejecutivo", ""),
        skills_clave        = resultado.get("skills_clave", []),
        brechas_detectadas  = resultado.get("brechas_detectadas", ""),
        cv_mejorado         = resultado.get("cv_mejorado", ""),
        advertencias        = resultado.get("advertencias", []),
        version_id          = version_id,
        model_used          = AGENT_ID,
    )


# ── Helpers ──────────────────────────────────────────────────────────
def _parse_llm_json(raw: str) -> Optional[dict]:
    """Intenta extraer JSON de la respuesta del LLM, ignorando texto extra."""
    if raw.startswith("ERROR"):
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Buscar el primer '{' y último '}'
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return None
