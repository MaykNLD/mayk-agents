"""
Agente HR Sastre de CV - Microservicio FastAPI
Puerto: 8012
"""
import sys, json
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from llm_client import call_llm

app = FastAPI(
    title="Agente HR Sastre de CV",
    description="Adapta el CV base a una oferta especifica con optimizacion ATS. Solo activo si fit_score >= 3.0.",
    version="1.0.0",
)

class SastreRequest(BaseModel):
    perfil_base_json:        dict = {}
    analisis_evaluador_json: dict = {}
    idioma:                  str = "ES"
    mercado_geografico:      str = "ES"

class SastreResponse(BaseModel):
    agent_id:           str
    result:             str   # JSON string con cv_adaptado_json completo
    keywords_insertadas: List[str] = []
    model_used:         str = "auto"

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-hr-sastre", "version": "1.0.0"}

@app.post("/execute", response_model=SastreResponse)
def execute(req: SastreRequest):
    if not req.perfil_base_json:
        raise HTTPException(status_code=400, detail="perfil_base_json es obligatorio.")
    if not req.analisis_evaluador_json:
        raise HTTPException(status_code=400, detail="analisis_evaluador_json es obligatorio.")

    fit_score = float(req.analisis_evaluador_json.get("fit_score", 0.0))
    if fit_score < 3.0:
        raise HTTPException(
            status_code=422,
            detail=f"fit_score {fit_score} < 3.0 (grado D/F). El Sastre no procesa ofertas de baja compatibilidad."
        )

    partes = [
        f"Perfil base del candidato (JSON):\n{json.dumps(req.perfil_base_json, ensure_ascii=False)[:6000]}",
        f"Analisis del evaluador (JSON):\n{json.dumps(req.analisis_evaluador_json, ensure_ascii=False)[:4000]}",
        f"Idioma del CV: {req.idioma}",
        f"Mercado geografico: {req.mercado_geografico}",
        "Responde UNICAMENTE en JSON valido con la estructura definida en tu prompt.",
    ]

    user_msg = "\n\n".join(partes)
    raw = call_llm("agente-hr-sastre", user_msg, max_tokens=4096)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])
        data = json.loads(clean)
        return SastreResponse(
            agent_id="agente-hr-sastre",
            result=json.dumps(data, ensure_ascii=False),
            keywords_insertadas=data.get("keywords_insertadas", []),
        )
    except Exception:
        return SastreResponse(
            agent_id="agente-hr-sastre",
            result=raw,
        )