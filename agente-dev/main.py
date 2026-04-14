"""
Agente Ingeniería Dev — Microservicio FastAPI
Puerto: 8004
"""
import sys
sys.path.insert(0, "/app/shared")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_client import call_llm

app = FastAPI(
    title="Agente Ingenieria Dev",
    description="Construye el proyecto técnico según stack y diseño aprobados.",
    version="4.0.0",
)

class DevRequest(BaseModel):
    stack:        str   # react-node | nextjs | html-astro | react-websockets | react-native | flutter
    requisitos:   str   # Requisitos funcionales aprobados
    diseno:       str   # Resumen del diseño/guía de estilos
    modulo:       str | None = None  # Módulo/componente específico a generar
    codigo_base:  str | None = None  # Código existente a modificar (max 3000 chars)

class AgentResponse(BaseModel):
    agent_id: str
    result:   str

@app.get("/health")
def health():
    return {"status": "ok", "agent": "agente-dev", "version": "4.0.0"}

@app.post("/execute", response_model=AgentResponse)
def execute(req: DevRequest):
    if not req.stack or not req.requisitos:
        raise HTTPException(status_code=400, detail="Los campos 'stack' y 'requisitos' son obligatorios.")

    partes = [
        f"Stack tecnológico: {req.stack}",
        f"Requisitos funcionales:\n{req.requisitos[:1500]}",
        f"Guía de diseño:\n{req.diseno[:1000]}",
    ]
    if req.modulo:
        partes.append(f"Módulo a generar: {req.modulo}")
    if req.codigo_base:
        partes.append(f"Código base existente (extracto):\n{req.codigo_base[:3000]}")

    user_msg = "\n".join(partes)
    # Dev usa Claude Sonnet (más potente) — max_tokens extra para código largo
    result   = call_llm("agente-dev", user_msg, max_tokens=4096)

    return AgentResponse(agent_id="agente-dev", result=result)
