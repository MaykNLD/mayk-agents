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
    empresa:      str = "Desconocida"
    rol:          str = "No especificado"
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
    import re as _re
    try:
        clean = raw.strip()
        # Eliminar bloques <think>...</think> que emiten modelos como Nemotron/R1
        clean = _re.sub(r"<think>.*?</think>", "", clean, flags=_re.DOTALL).strip()
        # Eliminar bloques de codigo markdown
        if clean.startswith("```"):
            lines = clean.split("\n")
            # Saltar la primera línea (```json) y la última (```)
            clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        # Extraer primer bloque JSON si hay texto extra alrededor
        match = _re.search(r"\{.*\}", clean, _re.DOTALL)
        if match:
            clean = match.group(0)
        data = json.loads(clean)

        # Normalizar fit_score: algunos modelos devuelven match_score, score o puntuacion (0-100)
        fit_score = float(data.get("fit_score") or data.get("match_score") or data.get("score") or data.get("puntuacion") or 0.0)
        if fit_score > 5.0:  # Viene en escala 0-100, convertir a 0-5
            fit_score = round(fit_score / 20.0, 2)
        
        # Override heurístico si el LLM olvida el score pero da señales positivas
        if fit_score == 0.0 and (data.get("apto") == True or data.get("cumple_requisitos_excluyentes") == True or "Contratar" in data.get("recomendacion", "")):
            fit_score = 4.5
            
        data["fit_score"] = fit_score  # Normalizar en el dict para Supabase


        # Recalcular grado si no lo viene bien o no corresponde al score normalizado
        grado = data.get("grado", "")
        if not grado or grado not in ["A", "B", "C", "D", "F"]:
            if fit_score >= 4.5:   grado = "A"
            elif fit_score >= 3.5: grado = "B"
            elif fit_score >= 3.0: grado = "C"
            elif fit_score >= 2.0: grado = "D"
            else:                  grado = "F"
            data["grado"] = grado

        # Extraer empresa y rol — primero raiz JSON, luego fallback en bloque_a
        def _extract_empresa_rol(d: dict):
            empresa = (d.get("empresa") or "").strip()
            rol     = (d.get("rol")     or "").strip()
            if empresa and rol:
                return empresa, rol
            # Fallback: buscar en bloque_a (puede ser dict o markdown string)
            bloque_a = d.get("bloque_a", "")
            import re as _re2
            if isinstance(bloque_a, dict):
                empresa = empresa or (bloque_a.get("empresa") or bloque_a.get("company") or "").strip()
                rol     = rol     or (bloque_a.get("rol")     or bloque_a.get("role")    or "").strip()
            elif isinstance(bloque_a, str) and len(bloque_a) > 5:
                # Formato tabla markdown: | Empresa | Acme Corp |
                tab_empresa = _re2.search(r"\|\s*(?:empresa|company)\s*\|\s*([^|\n]+)", bloque_a, _re2.IGNORECASE)
                tab_rol     = _re2.search(r"\|\s*(?:rol|role|posici[oó]n|puesto)\s*\|\s*([^|\n]+)", bloque_a, _re2.IGNORECASE)
                # Formato key-value: Empresa: Acme Corp
                kv_empresa  = _re2.search(r"(?:empresa|company)[:\s]+([^\n|]+)", bloque_a, _re2.IGNORECASE)
                kv_rol      = _re2.search(r"(?:rol|role|posici[oó]n|puesto)[:\s]+([^\n|]+)", bloque_a, _re2.IGNORECASE)
                empresa = empresa or (tab_empresa.group(1).strip() if tab_empresa else (kv_empresa.group(1).strip() if kv_empresa else ""))
                rol     = rol     or (tab_rol.group(1).strip()     if tab_rol     else (kv_rol.group(1).strip()     if kv_rol     else ""))
            return empresa or "Desconocida", rol or "No especificado"

        empresa_val, rol_val = _extract_empresa_rol(data)

        return EvaluadorResponse(
            agent_id="agente-hr-evaluador",
            fit_score=fit_score,
            grado=grado,
            recomendacion=data.get("recomendacion", "Descartar"),
            empresa=empresa_val,
            rol=rol_val,
            result=json.dumps(data, ensure_ascii=False),
        )
    except Exception as parse_err:
        print(f"[evaluador] JSON parse error: {parse_err}. Raw (500 chars): {raw[:500]}")
        return EvaluadorResponse(
            agent_id="agente-hr-evaluador",
            fit_score=0.0,
            grado="F",
            recomendacion="Descartar",
            result=raw,
        )