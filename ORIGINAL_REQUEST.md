# Original User Request

## 2026-09-08T01:41:35Z

# Teamwork Project Prompt

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full team

Desarrollo de una aplicación web corporativa PropTech escalable y orientada a eventos para la gestión, visualización e interacción de activos comerciales usando mapas satelitales y visor de planos PDF interactivos.

Working directory: ~/teamwork_projects/proptech_app
Integrity mode: development

## Requirements

### R1. Base de Datos y Backend Core
Implementar el backend usando **Python con FastAPI** y PostgreSQL con la extensión **PostGIS**. Diseñar el esquema para Centros Comerciales, Locales, Polígonos (coordenadas relativas al PDF) y Tickets. Los endpoints deben ser aislados y modulares, preparados para una futura integración mediante Eventos/Webhooks con un CRM externo.

### R2. Visor de Planos Interactivos (El Reto Principal)
Implementar en React (Next.js) un visor usando `react-pdf` combinado con `react-konva` o SVG puro. 
Debe permitir al Área de Proyectos dibujar polígonos sobre el plano arquitectónico y enlazar este polígono al código de un local.
**Crucial:** Las coordenadas guardadas deben ser relativas para que, sin importar el nivel de zoom aplicado al PDF, los polígonos mantengan su posición y proporción exacta.

### R3. Módulos Frontend y Geolocalización
- **Mapa Satelital:** Mostrar un mapa de Perú (Mapbox GL JS o Leaflet) con marcadores por cada Centro Comercial y una tabla resumen.
- **Gestión Comercial:** Al hacer clic en un polígono en el PDF, abrir la Ficha del Local. 
- **Módulo de Tickets:** Sistema para crear requerimientos (Comercial) y resolverlos en un dashboard tipo bandeja de entrada (Proyectos).

### R4. Roles y Seguridad
Aplicar un sistema de roles en el UI y API: 
- Área Comercial: Solo lectura de planos, y creación de tickets.
- Área de Proyectos: Creación/Edición de polígonos y resolución de tickets.

## Acceptance Criteria

### Verificación Backend y BD
- [ ] Existe un archivo de semillas (`seed.py`) que puebla la base de datos con al menos 1 Centro Comercial en Perú, 3 locales y 1 polígono de prueba.
- [ ] Una suite de tests automatizados (`pytest`) ejecuta y pasa pruebas sobre la creación de tickets y lectura de coordenadas geográficas en FastAPI.

### Verificación del Visor y Polígonos
- [ ] La aplicación frontend compila y levanta correctamente sin errores.
- [ ] Existe un test automatizado (o script de verificación claro) que asegura matemáticamente que si se dibuja un polígono en (X,Y) y se aplica un factor de zoom de 2x, el polígono renderizado se escala y se reposiciona sobre el mismo elemento del PDF.
- [ ] El Frontend y Backend se conectan exitosamente, permitiendo leer y guardar la ficha de un local al hacer clic en un polígono.
