"""
Agente Arquitecto Visual — Microservicio FastAPI
Puerto: 8003
"""
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import call_llm

app = FastAPI(
    title="Agente Arquitecto Visual",
    description="Diseña UI/UX, guía de estilos, componentes y mockups Mobile First.",
    version="4.0.0",
)

class VisualRequest(BaseModel):
    tipo_proyecto:     str              # landing | ecommerce | saas | app-movil | dashboard
    requisitos:        str              # Resumen de requisitos (salida del Estratega)
    referencias_diseno: list[str] = [] # URLs de referencia visual
    paleta_cliente:    str | None = None
    tipografia_cliente: str | None = None

class AgentResponse(BaseModel):
    agent_id: str
    result:   str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-visual", "version": "4.0.0"}

@app.post("/execute", response_model=AgentResponse)
def execute(req: VisualRequest):
    if not req.requisitos:
        raise HTTPException(status_code=400, detail="El campo 'requisitos' es obligatorio.")

    partes = [
        f"Tipo de proyecto: {req.tipo_proyecto}",
        f"Requisitos aprobados:\n{req.requisitos[:2000]}",
    ]
    if req.referencias_diseno:
        partes.append(f"Referencias de diseño: {', '.join(req.referencias_diseno)}")
    if req.paleta_cliente:
        partes.append(f"Paleta de colores del cliente: {req.paleta_cliente}")
    if req.tipografia_cliente:
        partes.append(f"Tipografía del cliente: {req.tipografia_cliente}")

    user_msg = "\n".join(partes)
    result   = call_llm("agente-visual", user_msg)

    return AgentResponse(agent_id="agente-visual", result=result)
