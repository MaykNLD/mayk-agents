"""
Agente QA-Ops — Microservicio FastAPI
Puerto: 8005
"""
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import call_llm

app = FastAPI(
    title="Agente QA-Ops",
    description="Control de calidad, seguridad y entrega final del proyecto.",
    version="4.0.0",
)

class QARequest(BaseModel):
    url_proyecto:    str | None = None  # URL para análisis Lighthouse
    codigo_fuente:   str | None = None  # Extracto de código a revisar
    tipo_proyecto:   str = "web"        # web | app-movil | saas
    checklist_items: list[str] = []     # Items específicos a verificar

class AgentResponse(BaseModel):
    agent_id: str
    result:   str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-qa-ops", "version": "4.0.0"}

@app.post("/execute", response_model=AgentResponse)
def execute(req: QARequest):
    if not req.url_proyecto and not req.codigo_fuente:
        raise HTTPException(status_code=400, detail="Proporciona url_proyecto o codigo_fuente.")

    partes = [f"Tipo de proyecto: {req.tipo_proyecto}"]
    if req.url_proyecto:
        partes.append(f"URL del proyecto: {req.url_proyecto}")
    if req.codigo_fuente:
        partes.append(f"Código a revisar (extracto):\n{req.codigo_fuente[:3000]}")
    if req.checklist_items:
        partes.append(f"Items de checklist a verificar: {', '.join(req.checklist_items)}")

    user_msg = "\n".join(partes)
    result   = call_llm("agente-qa-ops", user_msg)

    return AgentResponse(agent_id="agente-qa-ops", result=result)
