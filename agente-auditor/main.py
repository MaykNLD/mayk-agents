"""
Agente Auditor Forense — Microservicio FastAPI
Puerto: 8001
"""
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import call_llm

app = FastAPI(
    title="Agente Auditor Forense",
    description="Analiza webs, repos y apps existentes. Entrega informe rescate/reconstrucción.",
    version="4.0.0",
)

class AuditorRequest(BaseModel):
    url_actual:       str | None = None
    codigo_fuente:    str | None = None
    urls_competidores: list[str] = []
    tipo_proyecto:    str = "web"  # web | app-movil | saas | desktop

class AgentResponse(BaseModel):
    agent_id: str
    result:   str
    model_used: str = "auto"

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-auditor", "version": "4.0.0"}

@app.post("/execute", response_model=AgentResponse)
def execute(req: AuditorRequest):
    # Construir el mensaje de usuario compacto (solo lo necesario)
    partes = []
    if req.url_actual:
        partes.append(f"URL a auditar: {req.url_actual}")
    if req.codigo_fuente:
        # Limitar a 3000 chars para economizar tokens
        partes.append(f"Código fuente (extracto):\n{req.codigo_fuente[:3000]}")
    if req.urls_competidores:
        partes.append(f"Competidores: {', '.join(req.urls_competidores)}")
    partes.append(f"Tipo de proyecto: {req.tipo_proyecto}")

    if not partes:
        raise HTTPException(status_code=400, detail="Debes proporcionar al menos url_actual o codigo_fuente.")

    user_msg = "\n".join(partes)
    result   = call_llm("agente-auditor", user_msg)

    return AgentResponse(agent_id="agente-auditor", result=result)
