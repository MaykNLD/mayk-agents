"""
agente-scanner — Caza ofertas automatizada
Busca en APIs gratuitas/RSS (Remotive, etc.), filtra duplicados con dedup_hash,
y delega la evaluación al orchestrator.
"""
import os, json, hashlib, time
import urllib.request, urllib.parse, urllib.error
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from supabase_career import get_perfil_by_id, upsert_oferta

app = FastAPI(title="agente-scanner", version="1.0.0")
AGENT_ID = "agente-scanner"

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://career-orchestrator:8020")


# ── Modelos ──────────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    perfil_id: str
    limit: int = 10         # Cantidad máx de ofertas a procesar
    market: str = "remote"  # "es", "latam", "remote"


class ScanResponse(BaseModel):
    status: str
    mensaje: str
    ofertas_encontradas: int
    ofertas_nuevas: int


# ── APIs y Scrapers Ligeros ─────────────────────────────────────────

def buscar_en_remotive(terminos: str, limit: int = 10) -> list:
    """Busca ofertas remotas en Remotive.io (API gratuita, no requiere key)"""
    ofertas = []
    # Usar query params
    q = urllib.parse.quote(terminos)
    url = f"https://remotive.com/api/remote-jobs?search={q}&limit={limit * 2}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Career-Ops/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            jobs = data.get("jobs", [])
            
            for j in jobs[:limit]:
                ofertas.append({
                    "url": j.get("url"),
                    "titulo": j.get("title"),
                    "empresa": j.get("company_name"),
                    "portal": "remotive",
                    "texto_oferta": j.get("description", "")[:5000] # Limitar texto para no saturar al eval
                })
    except Exception as e:
        print(f"[scanner] Error en Remotive: {e}")
        
    return ofertas


# ── Tareas Globales ──────────────────────────────────────────────────

def _procesar_ofertas(ofertas: list, perfil_id: str):
    """
    Guarda las ofertas en el tracker y, si son nuevas, avisa al orquestador.
    """
    nuevas = 0
    for of in ofertas:
        url = of["url"]
        
        # 1. Crear dedup hash
        hash_str = f"{perfil_id}_{url}"
        dedup_hash = hashlib.sha256(hash_str.encode()).hexdigest()
        
        # 2. Insertar/Ignorar en db
        record = upsert_oferta({
            "perfil_id": perfil_id,
            "url": url,
            "titulo": of["titulo"],
            "empresa": of["empresa"],
            "portal": of["portal"],
            "dedup_hash": dedup_hash,
            "estado": "pendiente"
        })
        
        # Si record no está vacío, significa que se insertó (es nueva)
        if record and record.get("id"):
            nuevas += 1
            # 3. Disparar webhook de evaluacion en el orquestador
            try:
                eval_payload = {
                    "url_oferta": url,
                    "texto_oferta": of.get("texto_oferta", ""),
                    "perfil_id": perfil_id,
                    "idioma": "ES"
                }
                eval_req = urllib.request.Request(
                    f"{ORCHESTRATOR_URL}/career/evaluar",
                    data=json.dumps(eval_payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(eval_req, timeout=2) # Timeout corto, no bloqueamos
            except Exception as e:
                # El TimeoutError es normal porque el evaluador puede tardar. Todo OK.
                pass
                
    print(f"[scanner] Proceso finalizado. Total: {len(ofertas)} | Nuevas inyectadas: {nuevas}")


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "agent": AGENT_ID, "version": "1.0.0"}


@app.post("/scan", response_model=ScanResponse)
def iniciar_scan(req: ScanRequest, bg_tasks: BackgroundTasks):
    perfil = get_perfil_by_id(req.perfil_id)
    if not perfil:
        raise HTTPException(404, "Perfil no encontrado")
        
    # Construir query basándonos en el objetivo del perfil o su rol actual
    objetivo = perfil.get("objetivo", "")
    if not objetivo:
        # Fallback a nombre+apellido (poco util para search)
        # Mejor forzar una palabra clave generica de ingeniería o dejar en blanco
        terminos = "developer"
    else:
        # Extraer primeras palabras clave del objetivo
        terminos = " ".join(objetivo.split()[:3])
        
    print(f"[scanner] Buscando ofertas para '{terminos}'...")
    
    # Ejecutar scrapers (síncrono para contar, pero la inyección es asíncrona)
    # Por ahora solo Remotive por simplicidad
    ofertas = buscar_en_remotive(terminos, limit=req.limit)
    
    # Mandar a procesar al background para no bloquear al CLI/Orquestador
    bg_tasks.add_task(_procesar_ofertas, ofertas, req.perfil_id)
    
    return ScanResponse(
        status="escaneando",
        mensaje=f"Búsqueda iniciada para '{terminos}'. Procesando en background.",
        ofertas_encontradas=len(ofertas),
        ofertas_nuevas=0 # Se computan en BG
    )
