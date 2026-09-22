import { RelativePoint } from '../lib/coordinateMath';

export type UserRole = 'comercial' | 'proyectos';

export type LocalEstado = 'disponible' | 'arrendado' | 'reservado' | 'mantenimiento';

export type TicketType =
  | 'modificacion_plano'
  | 'division_local'
  | 'mantenimiento'
  | 'revision_comercial'
  | 'nuevo_requerimiento';

export type TicketPriority = 'baja' | 'media' | 'alta' | 'urgente';

export type TicketStatus = 'abierto' | 'en_progreso' | 'resuelto' | 'cancelado';

export interface CentroComercial {
  id: string;
  nombre: string;
  slug: string;
  direccion: string;
  departamento: string;
  provincia?: string;
  distrito?: string;
  lat: number;
  lon: number;
  total_locales: number;
  superficie_total_m2: number;
  imagen_url?: string;
  plano_url?: string;
}

export interface LocalComercial {
  id: string;
  codigo_local: string;
  nombre_comercial?: string;
  categoria: string;
  estado: LocalEstado;
  area_m2: number;
  precio_alquiler_mensual: number;
  moneda: 'USD' | 'PEN';
  piso_nivel: string;
  descripcion?: string;
  centro_comercial_id?: string;
  centro_comercial_nombre?: string;
  plano_id?: string;
}

export interface PoligonoBlueprint {
  id: string;
  local_id: string;
  plano_id: string;
  coordenadas_relativas: RelativePoint[];
  color_relleno?: string;
  color_borde?: string;
  opacidad?: number;
  etiqueta?: string;
  local?: LocalComercial;
}

export interface BlueprintInfo {
  id: string;
  centro_comercial_id: string;
  nombre_piso: string;
  numero_orden?: number;
  archivo_pdf_url: string;
  ancho_unscaled_pt: number;
  alto_unscaled_pt: number;
}

export interface Ticket {
  id: string;
  codigo_ticket: string;
  centro_comercial_id: string;
  local_id?: string;
  titulo: string;
  descripcion: string;
  tipo: TicketType;
  prioridad: TicketPriority;
  estado: TicketStatus;
  creado_por: string;
  asignado_a?: string;
  notas_resolucion?: string;
  resuelto_en?: string;
  creado_en: string;
  actualizado_en?: string;
  // Hydrated joins
  centro_comercial_nombre?: string;
  codigo_local?: string;
}

export interface TicketCreate {
  centro_comercial_id: string;
  local_id?: string;
  titulo: string;
  descripcion: string;
  tipo: TicketType;
  prioridad: TicketPriority;
  creado_por?: string;
}

export interface TicketResolve {
  notas_resolucion: string;
}
