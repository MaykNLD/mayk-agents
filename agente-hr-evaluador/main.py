"""
Agente HR Evaluador de Ofertas - Microservicio FastAPI
Puerto: 8011
"""
import sys, json
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from llm_client import call_llm

app = FastAPI(
    title="Agente HR Evaluador de Ofertas",
    description="Evalua ofertas de trabajo con scoring A-F en 7 bloques (A-G). Optimizado para ATS.",
    version="1.0.0",
)

class EvaluadorRequest(BaseModel):
    url_oferta:        Optional[str] = None
    texto_oferta:      Optional[str] = None
    perfil_base_json:  dict = {}
    idioma:            str = "ES"

class EvaluadorResponse(BaseModel):
    agent_id:     str
    fit_score:    float
    grado:        str
    recomendacion: str
    result:       str   # JSON string con los 7 bloques completos
    model_used:   str = "auto"

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-hr-evaluador", "version": "1.0.0"}

@app.post("/execute", response_model=EvaluadorResponse)
def execute(req: EvaluadorRequest):
    if not req.url_oferta and not req.texto_oferta:
        raise HTTPException(status_code=400, detail="Proporciona url_oferta o texto_oferta.")

    partes = []
    if req.url_oferta:
        partes.append(f"URL de la oferta: {req.url_oferta}")
    if req.texto_oferta:
        partes.append(f"Texto de la JD:\n{req.texto_oferta[:8000]}")
    if req.perfil_base_json:
        perfil_str = json.dumps(req.perfil_base_json, ensure_ascii=False)
        partes.append(f"Perfil del candidato (JSON):\n{perfil_str[:6000]}")
    partes.append(f"Idioma de respuesta: {req.idioma}")
    partes.append("Responde UNICAMENTE en JSON valido con la estructura definida en tu prompt.")

    user_msg = "\n\n".join(partes)
    raw = call_llm("agente-hr-evaluador", user_msg, max_tokens=2500)

    # Parsear JSON de la respuesta
    try:
        # Limpiar bloques de codigo markdown si el modelo los incluye
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])
        data = json.loads(clean)
        return EvaluadorResponse(
            agent_id="agente-hr-evaluador",
            fit_score=float(data.get("fit_score", 0.0)),
            grado=data.get("grado", "F"),
            recomendacion=data.get("recomendacion", "Descartar"),
            result=json.dumps(data, ensure_ascii=False),
        )
    except Exception:
        # Si el LLM no produjo JSON valido, devolvemos el raw con score 0
        return EvaluadorResponse(
            agent_id="agente-hr-evaluador",
            fit_score=0.0,
            grado="F",
            recomendacion="Descartar",
            result=raw,
        )