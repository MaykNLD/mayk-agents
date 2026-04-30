"""
agente-hr-diseno — Capa 1b del sistema Career-Ops Unificado
Genera el CV en HTML premium (ATS-bypass).
El PDF lo genera el orquestador usando Playwright (Chromium).
"""
import os, json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from llm_client import call_llm
from supabase_career import get_perfil_by_id

app = FastAPI(title="agente-hr-diseno", version="2.0.0")
AGENT_ID = "agente-hr-diseno"


# ── Modelos ────────────────────────────────────
class GenerarCVRequest(BaseModel):
    perfil_id:     str
    cv_version_id: Optional[str] = None   # No usado, por compatibilidad
    foto_modo:     Optional[str] = "sin_foto"  # sin_foto | placeholder | con_foto
    foto_url:      Optional[str] = None
    idioma:        Optional[str] = "ES"

class GenerarCVResponse(BaseModel):
    perfil_id:            str
    version_id:           Optional[str] = None
    html_cv:              str
    pdf_url:              Optional[str] = None   # Siempre None — PDF lo hace el orquestador
    secciones_detectadas: list = []
    advertencias:         list = []


# ── Endpoints ────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "version": "2.0.0"}


@app.post("/generar-cv-html", response_model=GenerarCVResponse)
def generar_cv_html(req: GenerarCVRequest):
    """
    Genera el HTML premium del CV usando el LLM.
    El PDF lo genera el orquestador con Playwright (Chromium) — no WeasyPrint.
    """
    # ── 1. Obtener perfil ─────────────────────────────────
    perfil = get_perfil_by_id(req.perfil_id)
    if not perfil:
        raise HTTPException(status_code=404,
                            detail=f"Perfil {req.perfil_id} no encontrado")

    # ── 2. Obtener el texto del CV ──────────────────────────
    cv_texto = (perfil.get("cv_markdown") or "").strip()
    if not cv_texto:
        raise HTTPException(
            status_code=400,
            detail="El perfil no tiene cv_markdown. El orquestador debe construirlo antes de llamar a este endpoint."
        )

    nombre   = f"{(perfil.get('nombre') or '').strip()} {(perfil.get('apellido') or '').strip()}".strip()
    mercado  = perfil.get("mercado") or ""
    email    = perfil.get("email") or ""

    # Datos de contacto: primero perfil raiz, luego datos_json.contacto como fallback
    datos_raw = perfil.get("datos_json") or {}
    if isinstance(datos_raw, str):
        try:    datos_raw = json.loads(datos_raw)
        except: datos_raw = {}
    contacto_raw = datos_raw.get("contacto") or {}
    if not isinstance(contacto_raw, dict):
        contacto_raw = {}

    linkedin = perfil.get("linkedin") or contacto_raw.get("linkedin") or ""
    github   = perfil.get("github_url") or contacto_raw.get("github") or ""
    telefono = perfil.get("telefono") or contacto_raw.get("telefono") or ""
    ciudad   = perfil.get("ciudad") or contacto_raw.get("ciudad") or ""
    web      = contacto_raw.get("web") or ""

    # Datos estructurados ricos para que el LLM los renderice con fidelidad
    def _lst(v): return v if isinstance(v, list) else []
    def _dct(v): return v if isinstance(v, dict) else {}

    stack_raw    = _dct(datos_raw.get("stack_tecnico"))
    proyectos    = _lst(datos_raw.get("proyectos"))
    certificaciones = _lst(datos_raw.get("certificaciones"))
    idiomas      = _lst(datos_raw.get("idiomas"))
    experiencia  = _lst(datos_raw.get("experiencia"))
    educacion    = _lst(datos_raw.get("educacion"))
    habilidades  = _lst(datos_raw.get("habilidades"))

    # Serializar como JSON legible para el LLM
    def _json(v): return json.dumps(v, ensure_ascii=False, indent=2)

    foto_instruccion = {
        "sin_foto":    "sin_foto — diseño cabecera completa a todo ancho sin espacio para foto",
        "placeholder": "placeholder — inserta <div id='foto-candidato' class='foto-placeholder'>[Foto profesional]</div>",
        "con_foto":    f"con_foto — usa <img id='foto-candidato' src='{req.foto_url}' alt='Foto profesional'>",
    }.get(req.foto_modo or "sin_foto", "sin_foto — diseño cabecera completa a todo ancho sin espacio para foto")

    user_message = f"""
INSTRUCCION CRITICA: USA SOLO los datos que aparecen a continuacion. NUNCA inventes ni completes datos ausentes.
Si un campo esta vacio o es una lista vacia, simplemente omite esa seccion del CV.

CANDIDATO: {nombre}
Email: {email}
Telefono: {telefono}
Ciudad/Pais: {ciudad}
LinkedIn: {linkedin}
GitHub: {github}
Web/Portfolio: {web}
Mercado objetivo: {mercado}
Idioma del CV: {req.idioma or 'ES'}
Modo foto: {foto_instruccion}

== TEXTO DEL CV (mejorado) ==
{cv_texto}

== STACK TECNICO (usar estas categorias si tienen datos, omitir las vacias) ==
{_json(stack_raw)}

== PROYECTOS ==
{_json(proyectos)}

== EXPERIENCIA DETALLADA ==
{_json(experiencia)}

== EDUCACION ==
{_json(educacion)}

== CERTIFICACIONES ==
{_json(certificaciones)}

== IDIOMAS ==
{_json(idiomas)}

== HABILIDADES ==
{_json(habilidades)}

Genera el HTML del CV siguiendo tus estandares visuales premium.
Incluye SOLO las secciones que tienen datos reales arriba. No inventes nada.
Responde EXCLUSIVAMENTE con el JSON definido en tu prompt. Sin texto fuera del JSON.
"""

    # ── 3. Llamar al LLM ─────────────────────────────────
    raw = call_llm(AGENT_ID, user_message, max_tokens=4000)
    resultado = _parse_llm_json(raw)

    if resultado is None:
        raise HTTPException(
            status_code=500,
            detail=f"El LLM no devolvio JSON valido. Primeros 300 chars: {raw[:300]}"
        )

    html_cv = (resultado.get("html_cv") or "").strip()
    if not html_cv:
        raise HTTPException(
            status_code=500,
            detail="El LLM devolvio html_cv vacio. Reintenta o revisa el prompt del agente."
        )

    return GenerarCVResponse(
        perfil_id            = req.perfil_id,
        version_id           = req.cv_version_id,
        html_cv              = html_cv,
        pdf_url              = None,  # El orquestador genera el PDF con Playwright
        secciones_detectadas = resultado.get("secciones_detectadas") or [],
        advertencias         = resultado.get("advertencias") or [],
    )


# ── Helpers ────────────────────────────────────
def _parse_llm_json(raw: str) -> Optional[dict]:
    if not raw or raw.startswith("ERROR"):
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
