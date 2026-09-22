# Interface Contracts, Data Schemas, and Domain Constants for PropTech E2E Testing.
# Authoritative sources: ORIGINAL_REQUEST.md and PROJECT.md - Interface Contracts.
from typing import Dict, Any, List, Optional, Tuple

PERU_LAT_MIN = -18.5
PERU_LAT_MAX = 0.0
PERU_LON_MIN = -81.5
PERU_LON_MAX = -68.5

PERU_GEOGRAPHIC_BOUNDS = {
    "lat_min": PERU_LAT_MIN,
    "lat_max": PERU_LAT_MAX,
    "lon_min": PERU_LON_MIN,
    "lon_max": PERU_LON_MAX,
}

AUTHENTIC_PERU_MALLS = [
    {"nombre": "Plaza Center Villa El Salvador", "slug": "plaza-center-ves", "departamento": "Lima", "lat": -12.215, "lon": -76.938},
    {"nombre": "Real Plaza Salaverry", "slug": "real-plaza-salaverry", "departamento": "Lima", "lat": -12.0899, "lon": -77.0510},
    {"nombre": "Jockey Plaza", "slug": "jockey-plaza", "departamento": "Lima", "lat": -12.0863, "lon": -76.9763},
    {"nombre": "Mall Aventura Porongoche", "slug": "mall-aventura-porongoche", "departamento": "Arequipa", "lat": -16.4225, "lon": -71.5173},
    {"nombre": "Real Plaza Cusco", "slug": "real-plaza-cusco", "departamento": "Cusco", "lat": -13.5226, "lon": -71.9427},
    {"nombre": "Real Plaza Trujillo", "slug": "real-plaza-trujillo", "departamento": "La Libertad", "lat": -8.1281, "lon": -79.0345},
    {"nombre": "Mallplaza Cayma", "slug": "mallplaza-cayma", "departamento": "Arequipa", "lat": -16.3861, "lon": -71.5422},
    {"nombre": "Real Plaza Chiclayo", "slug": "real-plaza-chiclayo", "departamento": "Lambayeque", "lat": -6.7725, "lon": -79.8392},
    {"nombre": "Real Plaza Piura", "slug": "real-plaza-piura", "departamento": "Piura", "lat": -5.1872, "lon": -80.6384},
    {"nombre": "Plaza Center San Martín de Porres", "slug": "plaza-center-smp", "departamento": "Lima", "lat": -11.9961, "lon": -77.0652},
    {"nombre": "Plaza Center Lurín", "slug": "plaza-center-lurin", "departamento": "Lima", "lat": -12.2742, "lon": -76.8711},
]

PERU_MALLS = {
    "plaza_center_ves": {
        "nombre": "Plaza Center Villa El Salvador",
        "slug": "plaza-center-ves",
        "departamento": "Lima",
        "department": "Lima",
        "city": "Lima",
        "address": "Av. Pachacútec, Villa El Salvador, Lima",
        "lat": -12.215,
        "lng": -76.938,
        "lon": -76.938,
    },
    "real_plaza_salaverry": {
        "nombre": "Real Plaza Salaverry",
        "slug": "real-plaza-salaverry",
        "departamento": "Lima",
        "department": "Lima",
        "city": "Lima",
        "address": "Av. General Salaverry 2370, Jesús María, Lima",
        "lat": -12.0899,
        "lng": -77.0510,
        "lon": -77.0510,
    },
    "jockey_plaza": {
        "nombre": "Jockey Plaza",
        "slug": "jockey-plaza",
        "departamento": "Lima",
        "department": "Lima",
        "city": "Lima",
        "address": "Av. Javier Prado Este 4200, Santiago de Surco, Lima",
        "lat": -12.0863,
        "lng": -76.9763,
        "lon": -76.9763,
    },
    "mall_aventura_porongoche": {
        "nombre": "Mall Aventura Porongoche",
        "slug": "mall-aventura-porongoche",
        "departamento": "Arequipa",
        "department": "Arequipa",
        "city": "Arequipa",
        "address": "Av. Porongoche 500, Paucarpata, Arequipa",
        "lat": -16.4225,
        "lng": -71.5173,
        "lon": -71.5173,
    },
    "real_plaza_cusco": {
        "nombre": "Real Plaza Cusco",
        "slug": "real-plaza-cusco",
        "departamento": "Cusco",
        "department": "Cusco",
        "city": "Cusco",
        "address": "Av. Collasuyo 2164, Cusco",
        "lat": -13.5226,
        "lng": -71.9427,
        "lon": -71.9427,
    },
    "real_plaza_trujillo": {
        "nombre": "Real Plaza Trujillo",
        "slug": "real-plaza-trujillo",
        "departamento": "La Libertad",
        "department": "La Libertad",
        "city": "Trujillo",
        "address": "Av. César Vallejo Poniente 1345, Trujillo",
        "lat": -8.1281,
        "lng": -79.0345,
        "lon": -79.0345,
    },
    "mallplaza_cayma": {
        "nombre": "Mallplaza Cayma",
        "slug": "mallplaza-cayma",
        "departamento": "Arequipa",
        "department": "Arequipa",
        "city": "Arequipa",
        "address": "Av. Ejército 795, Cayma, Arequipa",
        "lat": -16.3861,
        "lng": -71.5422,
        "lon": -71.5422,
    },
    "real_plaza_chiclayo": {
        "nombre": "Real Plaza Chiclayo",
        "slug": "real-plaza-chiclayo",
        "departamento": "Lambayeque",
        "department": "Lambayeque",
        "city": "Chiclayo",
        "address": "Av. Miguel Grau 650, Chiclayo",
        "lat": -6.7725,
        "lng": -79.8392,
        "lon": -79.8392,
    },
    "real_plaza_piura": {
        "nombre": "Real Plaza Piura",
        "slug": "real-plaza-piura",
        "departamento": "Piura",
        "department": "Piura",
        "city": "Piura",
        "address": "Av. Sánchez Cerro 234, Piura",
        "lat": -5.1872,
        "lng": -80.6384,
        "lon": -80.6384,
    },
    "real_plaza_huancayo": {
        "nombre": "Real Plaza Huancayo",
        "slug": "real-plaza-huancayo",
        "departamento": "Junin",
        "department": "Junin",
        "city": "Huancayo",
        "address": "Av. Ferrocarril 1035, Huancayo",
        "lat": -12.0689,
        "lng": -75.2104,
        "lon": -75.2104,
    },
    "plaza_center_smp": {
        "nombre": "Plaza Center San Martín de Porres",
        "slug": "plaza-center-smp",
        "departamento": "Lima",
        "department": "Lima",
        "city": "Lima",
        "address": "Av. Tomás Valle con Panamericana Norte, Lima",
        "lat": -11.9961,
        "lng": -77.0652,
        "lon": -77.0652,
    },
}

ROLE_COMERCIAL = "comercial"
ROLE_PROYECTOS = "proyectos"
VALID_ROLES = {ROLE_COMERCIAL, ROLE_PROYECTOS}

RBAC_PERMISSIONS = {
    ROLE_COMERCIAL: {
        "view_malls": True,
        "view_blueprints": True,
        "view_polygons": True,
        "view_locales": True,
        "update_local_terms": True,
        "create_polygon": False,
        "update_polygon": False,
        "delete_polygon": False,
        "link_polygon_local": False,
        "create_ticket": True,
        "view_tickets": True,
        "resolve_ticket": False,
        "dispatch_webhooks": False,
        "units:view": True,
        "units:create": True,
        "units:update": True,
        "blueprint:draw": False,
        "tickets:create": True,
        "tickets:update_status": False,
    },
    ROLE_PROYECTOS: {
        "view_malls": True,
        "view_blueprints": True,
        "view_polygons": True,
        "view_locales": True,
        "update_local_terms": True,
        "create_polygon": True,
        "update_polygon": True,
        "delete_polygon": True,
        "link_polygon_local": True,
        "create_ticket": True,
        "view_tickets": True,
        "resolve_ticket": True,
        "dispatch_webhooks": True,
        "units:view": True,
        "units:create": False,
        "units:update": False,
        "blueprint:draw": True,
        "tickets:create": True,
        "tickets:update_status": True,
    }
}

LOCAL_ESTADOS = {"disponible", "arrendado", "reservado", "mantenimiento"}
TICKET_ESTADOS = {"abierto", "en_revision", "resuelto", "rechazado"}
TICKET_PRIORIDADES = {"baja", "media", "alta", "urgente"}
TICKET_TIPOS = {"modificacion_plano", "division_local", "mantenimiento", "revision_comercial", "nuevo_requerimiento"}

def is_within_peru(lat: float, lon: float) -> bool:
    return (PERU_LAT_MIN <= lat <= PERU_LAT_MAX) and (PERU_LON_MIN <= lon <= PERU_LON_MAX)

def validate_peru_coordinates(lat: float, lon: float) -> bool:
    return is_within_peru(lat, lon)

def is_valid_normalized_coord(u: float, v: float) -> bool:
    return 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0

def validate_polygon_geometry(points: List[Dict[str, float]]) -> Tuple[bool, Optional[str]]:
    if not isinstance(points, list):
        return False, "Points must be a list"
    if len(points) < 3:
        return False, "A polygon must have at least 3 vertices"
    for i, pt in enumerate(points):
        if not isinstance(pt, dict) or "x" not in pt or "y" not in pt:
            return False, f"Vertex {i} must be an object with 'x' and 'y'"
        x, y = pt["x"], pt["y"]
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            return False, f"Vertex {i} coordinates must be numbers"
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return False, f"Vertex {i} ({x}, {y}) out of normalized [0.0, 1.0] bounds"
    return True, None

def validate_relative_polygon(points: List[Dict[str, float]]) -> bool:
    valid, err = validate_polygon_geometry(points)
    if not valid:
        raise ValueError(err)
    return True

def check_rbac_permission(role: str, action: str) -> bool:
    role_norm = role.lower().strip() if role else ""
    permissions = RBAC_PERMISSIONS.get(role_norm, {})
    return permissions.get(action, False)

