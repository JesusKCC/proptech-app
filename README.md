# PropTech - Plataforma Comercial y Visor de Planos Interactivos

Aplicación web corporativa escalable y orientada a eventos para la gestión, visualización e interacción de activos comerciales usando mapas satelitales y visor de planos interactivos.

## 🏗️ Arquitectura del Proyecto

- **Frontend (`/frontend`)**: Desarrollado en **Next.js 14**, React, TailwindCSS, Konva / SVG y visores de planos interactivos con coordenadas normalizadas.
- **Backend (`/backend`)**: API REST desarrollada en **Python FastAPI**, PostgreSQL / PostGIS / SQLite, sistema de tickets, gestión de locales y arquitectura de eventos con Outbox pattern.

## 🚀 Despliegue en Vercel (Frontend)

Para desplegar el Frontend en Vercel:
1. **Root Directory**: Configurar en los ajustes del proyecto (`Settings` -> `General`) el valor `frontend`.
2. **Framework Preset**: Next.js (se detecta automáticamente al definir el Root Directory).
3. **Build Command**: `npm run build`
4. **Output Directory**: `.next`
