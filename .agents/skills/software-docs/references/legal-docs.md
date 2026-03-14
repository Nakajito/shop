# Legal & Closure Documentation Reference

Use sections of this file when generating formal project delivery or legal documents.

---

## Acceptance Certificate (Acta de Aceptación)

Adapt language (Spanish/English) to match the client's preference.

```markdown
# ACTA DE ACEPTACIÓN Y ENTREGA DE PROYECTO

**Proyecto:** [Nombre del Proyecto]  
**Versión entregada:** [X.X.X]  
**Fecha de entrega:** [DD/MM/AAAA]  
**Cliente:** [Nombre de la empresa / persona]  
**Proveedor:** [Nombre de la empresa desarrolladora]

---

## 1. Resumen del Proyecto

[Descripción breve de qué se desarrolló, el objetivo principal y las tecnologías utilizadas.]

Ejemplo: *"Se desarrolló una plataforma e-commerce B2C con módulo de gestión de inventario, pasarela de pago integrada con Stripe, y panel de administración para gestión de productos, pedidos y clientes."*

---

## 2. Entregables

| # | Entregable | Descripción | Estado |
|---|-----------|-------------|--------|
| 1 | Aplicación web en producción | URL: https://app.example.com | ✅ Entregado |
| 2 | Código fuente | Repositorio: github.com/org/project | ✅ Entregado |
| 3 | Documentación técnica | Arquitectura, API, instalación | ✅ Entregado |
| 4 | Manual de usuario | Guía para administradores | ✅ Entregado |
| 5 | Credenciales de producción | Accesos a servidor, DB, servicios | ✅ Entregado |
| 6 | Capacitación | Sesión de 2 horas con el equipo cliente | ✅ Realizado |

---

## 3. Funcionalidades Entregadas

| # | Funcionalidad | Resultado |
|---|--------------|-----------|
| 1 | Registro e inicio de sesión de usuarios | ✅ Completa |
| 2 | Catálogo de productos con búsqueda y filtros | ✅ Completa |
| 3 | Carrito de compras | ✅ Completa |
| 4 | Checkout con pago en línea (Stripe) | ✅ Completa |
| 5 | Panel de administración | ✅ Completa |
| 6 | Notificaciones por correo electrónico | ✅ Completa |
| 7 | [Funcionalidad pendiente, si aplica] | ⚠️ Diferida — ver Cláusula 5 |

---

## 4. Pruebas Realizadas

Se realizaron pruebas unitarias, de integración y de aceptación de usuario (UAT). El cliente participó en las pruebas UAT el [fecha]. Los resultados se encuentran en el Reporte de Pruebas adjunto.

**Cobertura de pruebas:** 94%  
**Defectos críticos encontrados:** 0  
**Defectos menores pendientes:** Ver Bitácora de Errores Conocidos

---

## 5. Elementos Fuera de Alcance / Diferidos

[Si hay funcionalidades acordadas que no se entregaron en esta versión, documentarlas aquí con la razón y el plan:]

| Elemento | Razón | Plan |
|---------|-------|------|
| Integración PayPal | API de PayPal en mantenimiento durante el sprint | Se entregará en v2.1, estimado [fecha] |

---

## 6. Período de Garantía

El proveedor otorga una garantía de **[30/60/90] días calendario** a partir de la fecha de firma de este documento. Durante este período, se corregirán sin costo adicional los defectos que sean responsabilidad directa del desarrollo.

**No está cubierto por garantía:**
- Errores causados por modificaciones del cliente al código
- Problemas derivados de servicios de terceros
- Solicitudes de nuevas funcionalidades

---

## 7. Firmas

Al firmar este documento, el cliente confirma haber recibido, revisado y aprobado los entregables descritos.

---

**Por el Cliente:**

Nombre: ___________________________  
Cargo: ___________________________  
Empresa: ___________________________  
Firma: ___________________________  
Fecha: ___________________________

---

**Por el Proveedor:**

Nombre: ___________________________  
Cargo: ___________________________  
Empresa: ___________________________  
Firma: ___________________________  
Fecha: ___________________________
```

---

## License Inventory

Document all third-party dependencies and their licenses. Critical for compliance.

```markdown
# License Inventory — [Project Name]

**Generated:** YYYY-MM-DD  
**Tool:** `license-checker` (npm) / `pip-licenses` (Python)

---

## Summary

| License Type | Count | Compatible with project? |
|---|---|---|
| MIT | 42 | ✅ Yes |
| Apache 2.0 | 8 | ✅ Yes |
| BSD-3-Clause | 5 | ✅ Yes |
| ISC | 3 | ✅ Yes |
| GPL-3.0 | 1 | ⚠️ Review required |

---

## Dependency List

| Package | Version | License | Notes |
|---------|---------|---------|-------|
| react | 18.2.0 | MIT | — |
| express | 4.18.2 | MIT | — |
| prisma | 5.0.0 | Apache-2.0 | — |
| bcryptjs | 2.4.3 | MIT | — |
| stripe | 12.0.0 | MIT | — |
| [package] | [version] | GPL-3.0 | ⚠️ Legal review needed if redistributing |

---

## Media Assets

| Asset | Source | License | Attribution required |
|-------|--------|---------|---------------------|
| Hero image | Unsplash | Unsplash License | ❌ No |
| Icon set | Lucide | ISC | ❌ No |
| Font: Inter | Google Fonts | OFL-1.1 | ❌ No |

---

## Notes

- All MIT, ISC, BSD, and Apache 2.0 licenses are permissive and compatible with commercial use.
- GPL licenses require the derivative work to also be open-source — confirm with legal before distributing.
- Run `npx license-checker --csv > licenses.csv` to regenerate this list from the actual dependency tree.
```

---

## Maintenance & Warranty Contract

```markdown
# Contrato de Mantenimiento y Soporte — [Project Name]

**Fecha de inicio:** [DD/MM/AAAA]  
**Período:** [12 meses] — renovable  
**Cliente:** [Nombre]  
**Proveedor:** [Nombre]

---

## 1. Servicios Incluidos

### Garantía Post-Entrega (primeros [30/60/90] días — sin costo)

- Corrección de defectos directamente relacionados con el desarrollo entregado
- Respuesta en < 24 horas hábiles para defectos críticos
- Respuesta en < 72 horas hábiles para defectos no críticos

### Mantenimiento Correctivo

Corrección de errores y bugs que surjan después del período de garantía.

### Mantenimiento Preventivo

- Actualización de dependencias de seguridad
- Monitoreo del estado del servidor
- Revisión mensual de logs de errores

---

## 2. Niveles de Servicio (SLA)

| Prioridad | Descripción | Tiempo de respuesta | Tiempo de resolución |
|-----------|-------------|---------------------|---------------------|
| Crítica (P1) | Sistema caído, pérdida de datos | < 2 horas | < 8 horas |
| Alta (P2) | Funcionalidad principal afectada | < 4 horas hábiles | < 24 horas |
| Media (P3) | Funcionalidad secundaria afectada | < 24 horas hábiles | < 72 horas |
| Baja (P4) | Mejoras menores, cosméticas | < 72 horas hábiles | Próxima versión |

---

## 3. Exclusiones

Este contrato **no incluye**:
- Desarrollo de nuevas funcionalidades
- Cambios en el diseño visual
- Migraciones a nuevas plataformas
- Soporte por daños causados por el cliente (modificaciones no autorizadas, credenciales comprometidas)

---

## 4. Canales de Soporte

| Canal | Disponibilidad | Para |
|-------|---------------|------|
| Email: soporte@proveedor.com | L-V 9:00–18:00 | P3, P4 |
| Teléfono: +52 55 0000 0000 | L-V 9:00–18:00 | P2 |
| WhatsApp de emergencias | 24/7 | P1 únicamente |
| Sistema de tickets | Siempre | Seguimiento |

---

## 5. Tarifas

[Definir si el mantenimiento es incluido, mensual fijo, o por horas. Adaptar según el acuerdo comercial.]

**Costo mensual:** $[X,XXX] MXN + IVA  
**Incluye:** [X] horas de soporte/mes  
**Horas adicionales:** $[XXX] MXN/hora

---

## 6. Vigencia y Terminación

Este contrato tiene vigencia de [12 meses]. Se renueva automáticamente salvo aviso con [30 días] de anticipación.

---

**Firmas**

Cliente: ___________________________ Fecha: ___________  
Proveedor: _________________________ Fecha: ___________
```
