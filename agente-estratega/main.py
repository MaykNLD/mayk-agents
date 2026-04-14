"""
Agente Estratega de Negocio — Microservicio FastAPI
Puerto: 8002
"""
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import call_llm

app = FastAPI(
    title="Agente Estratega de Negocio",
    description="Define arquitectura, stack tecnológico y propuesta económica del proyecto.",
    version="4.0.0",
)

class EstrategaRequest(BaseModel):
    tipo_proyecto:   str              # landing | ecommerce | saas | app-movil | pwa | crm
    objetivo:        str              # Descripción del objetivo de negocio
    usuarios:        str | None = None
    integraciones:   list[str] = []
    presupuesto:     str | None = None
    stack_existente: str | None = None

class AgentResponse(BaseModel):
    agent_id: str
    result:   str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-estratega", "version": "4.0.0"}

@app.post("/execute", response_model=AgentResponse)
def execute(req: EstrategaRequest):
    partes = [
        f"Tipo de proyecto: {req.tipo_proyecto}",
        f"Objetivo de negocio: {req.objetivo}",
    ]
    if req.usuarios:
        partes.append(f"Usuarios objetivo: {req.usuarios}")
    if req.integraciones:
        partes.append(f"Integraciones necesarias: {', '.join(req.integraciones)}")
    if req.presupuesto:
        partes.append(f"Presupuesto disponible: {req.presupuesto}")
    if req.stack_existente:
        partes.append(f"Stack existente a mantener/migrar: {req.stack_existente}")

    user_msg = "\n".join(partes)
    result   = call_llm("agente-estratega", user_msg)

    return AgentResponse(agent_id="agente-estratega", result=result)
