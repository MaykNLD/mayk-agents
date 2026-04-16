"""
supabase_career.py — Funciones Supabase específicas para Career-Ops Unificado
Complementa al supabase_client.py existente con las tablas nuevas.
"""
import os, json, urllib.request, urllib.error
from typing import Optional

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")


def _headers():
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }


def _get(table: str, query: str = "") -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}{'?' + query if query else ''}"
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return []


def _post(table: str, data: dict) -> dict:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            return result[0] if isinstance(result, list) and result else {}
    except Exception as e:
        print(f"[supabase_career] POST {table} error: {e}")
        return {}


def _patch(table: str, eq_field: str, eq_value: str, data: dict) -> dict:
    url = f"{SUPABASE_URL}/rest/v1/{table}?{eq_field}=eq.{eq_value}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=_headers(), method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            return result[0] if isinstance(result, list) and result else {}
    except Exception as e:
        print(f"[supabase_career] PATCH {table} error: {e}")
        return {}


# ── perfil_base ──────────────────────────────────────────────────────
def get_perfil_by_id(perfil_id: str) -> Optional[dict]:
    result = _get("perfil_base", f"id=eq.{perfil_id}&limit=1")
    return result[0] if result else None


def get_first_perfil() -> Optional[dict]:
    result = _get("perfil_base", "order=created_at.asc&limit=1")
    return result[0] if result else None


def list_perfiles() -> list:
    return _get("perfil_base", "select=id,nombre,apellido,email,mercado,idioma,nivel&order=created_at.asc")


def update_perfil(perfil_id: str, data: dict) -> dict:
    return _patch("perfil_base", "id", perfil_id, data)


# ── cv_versiones ─────────────────────────────────────────────────────
def create_cv_version(data: dict) -> dict:
    return _post("cv_versiones", data)


def get_cv_versions_by_perfil(perfil_id: str) -> list:
    return _get("cv_versiones", f"perfil_id=eq.{perfil_id}&order=version.desc")


def get_latest_approved_cv(perfil_id: str) -> Optional[dict]:
    result = _get("cv_versiones",
                  f"perfil_id=eq.{perfil_id}&aprobado=eq.true&order=version.desc&limit=1")
    return result[0] if result else None


def approve_cv_version(version_id: str) -> dict:
    return _patch("cv_versiones", "id", version_id, {"aprobado": True})


def update_cv_version_pdf(version_id: str, pdf_url: str) -> dict:
    return _patch("cv_versiones", "id", version_id, {"pdf_url": pdf_url})


# ── ofertas_tracker ──────────────────────────────────────────────────
def upsert_oferta(data: dict) -> dict:
    """Inserta una oferta o la ignora si el dedup_hash ya existe."""
    url = f"{SUPABASE_URL}/rest/v1/ofertas_tracker"
    h = _headers()
    h["Prefer"] = "resolution=ignore-duplicates,return=representation"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read().decode())
            return result[0] if isinstance(result, list) and result else {}
    except Exception as e:
        print(f"[supabase_career] upsert_oferta error: {e}")
        return {}


def get_ofertas_pendientes(perfil_id: Optional[str] = None, limit: int = 20) -> list:
    q = f"estado=eq.pendiente&order=created_at.desc&limit={limit}"
    if perfil_id:
        q = f"perfil_id=eq.{perfil_id}&{q}"
    return _get("ofertas_tracker", q)


def update_oferta_estado(oferta_id: str, estado: str, fit_score: Optional[float] = None) -> dict:
    data = {"estado": estado}
    if fit_score is not None:
        data["fit_score"] = fit_score
    return _patch("ofertas_tracker", "id", oferta_id, data)


# ── aplicaciones_career ──────────────────────────────────────────────
def create_aplicacion(data: dict) -> dict:
    return _post("aplicaciones_career", data)


def update_aplicacion(app_id: str, data: dict) -> dict:
    return _patch("aplicaciones_career", "id", app_id, data)


def get_aplicaciones_by_perfil(perfil_id: str, limit: int = 50) -> list:
    return _get("aplicaciones_career",
                f"perfil_id=eq.{perfil_id}&order=created_at.desc&limit={limit}")
