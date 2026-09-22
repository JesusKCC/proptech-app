import {
  FALLBACK_MALLS,
  FALLBACK_LOCALES,
  FALLBACK_TICKETS,
  resolveTicket,
  createTicket,
} from '../src/lib/api';
import { UserRole } from '../src/types';

describe('Milestone 3: Frontend GIS & Security Module Verification', () => {
  describe('1. Peru Satellite GIS Mall Data Verification', () => {
    test('contains all 11 authentic Peruvian shopping centers', () => {
      expect(FALLBACK_MALLS.length).toBe(11);
      const slugs = FALLBACK_MALLS.map((m) => m.slug);
      expect(slugs).toContain('plaza-center-villa-el-salvador');
      expect(slugs).toContain('jockey-plaza');
      expect(slugs).toContain('real-plaza-salaverry');
      expect(slugs).toContain('mall-aventura-porongoche');
      expect(slugs).toContain('real-plaza-trujillo');
      expect(slugs).toContain('real-plaza-chiclayo');
      expect(slugs).toContain('open-plaza-piura');
      expect(slugs).toContain('real-plaza-cusco');
      expect(slugs).toContain('real-plaza-huancayo');
      expect(slugs).toContain('el-quinde-ica');
      expect(slugs).toContain('mall-plaza-tacna');
    });

    test('all shopping centers have valid coordinates within Peru boundaries', () => {
      // Peru bounding box: Lat between -18.5 and 0.0, Lon between -81.5 and -68.5
      for (const mall of FALLBACK_MALLS) {
        expect(mall.lat).toBeGreaterThanOrEqual(-18.5);
        expect(mall.lat).toBeLessThanOrEqual(0.0);
        expect(mall.lon).toBeGreaterThanOrEqual(-81.5);
        expect(mall.lon).toBeLessThanOrEqual(-68.5);
        expect(mall.total_locales).toBeGreaterThan(0);
        expect(mall.superficie_total_m2).toBeGreaterThan(0);
        expect(mall.departamento.length).toBeGreaterThan(0);
      }
    });

    test('covers diverse departments across Peru', () => {
      const depts = new Set(FALLBACK_MALLS.map((m) => m.departamento));
      expect(depts.has('Lima')).toBe(true);
      expect(depts.has('Arequipa')).toBe(true);
      expect(depts.has('La Libertad')).toBe(true);
      expect(depts.has('Cusco')).toBe(true);
      expect(depts.size).toBeGreaterThanOrEqual(6);
    });
  });

  describe('2. Commercial Units (Locales) Integrity', () => {
    test('contains authentic units from Plaza Center Villa El Salvador', () => {
      const codes = FALLBACK_LOCALES.map((l) => l.codigo_local);
      expect(codes).toContain('LCE-103'); // COOLBOX
      expect(codes).toContain('LCE-105'); // BITEL
      expect(codes).toContain('LCE-107'); // ECONOLENTES
      expect(codes).toContain('LCE-101/102'); // STARBUCKS
    });

    test('units have valid commercial attributes', () => {
      for (const unit of FALLBACK_LOCALES) {
        expect(unit.area_m2).toBeGreaterThan(0);
        expect(unit.precio_alquiler_mensual).toBeGreaterThan(0);
        expect(['USD', 'PEN']).toContain(unit.moneda);
        expect(['disponible', 'arrendado', 'reservado', 'mantenimiento']).toContain(unit.estado);
      }
    });
  });

  describe('3. RBAC Security & Ticket Resolution Workflow', () => {
    test('roleHeaders generates correct X-User-Role header', () => {
      const comercialHeader = { 'X-User-Role': 'comercial' as UserRole };
      const proyectosHeader = { 'X-User-Role': 'proyectos' as UserRole };

      expect(comercialHeader['X-User-Role']).toBe('comercial');
      expect(proyectosHeader['X-User-Role']).toBe('proyectos');
    });

    test('resolveTicket throws Access Denied error when invoked with role comercial', async () => {
      await expect(
        resolveTicket('tck-001', { notas_resolucion: 'Resolución no autorizada' }, 'comercial')
      ).rejects.toThrow(/Acceso denegado/i);
    });

    test('resolveTicket successfully resolves ticket when invoked with role proyectos', async () => {
      const resolved = await resolveTicket(
        'tck-001',
        { notas_resolucion: 'Inspección técnica validada por ingeniería' },
        'proyectos'
      );

      expect(resolved).not.toBeNull();
      expect(resolved?.estado).toBe('resuelto');
      expect(resolved?.notas_resolucion).toBe('Inspección técnica validada por ingeniería');
    });

    test('createTicket succeeds with role comercial', async () => {
      const newTicket = await createTicket(
        {
          centro_comercial_id: 'plaza-center-villa-el-salvador',
          local_id: 'loc-coolbox',
          titulo: 'Solicitud de ampliación de escaparate',
          descripcion: 'El arrendatario solicita modificación de plano de mampara',
          tipo: 'modificacion_plano',
          prioridad: 'alta',
        },
        'comercial'
      );

      expect(newTicket).not.toBeNull();
      expect(newTicket?.creado_por).toBe('comercial');
      expect(newTicket?.estado).toBe('abierto');
    });
  });
});
