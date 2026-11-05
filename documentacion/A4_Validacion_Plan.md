# [V2] A4: validación del plan contra la especificación

Fecha: 2026-11-05 (CDMX). Responsable: codex-par.

Se revisó `A3_Propuesta_Incrementos.md` contra la especificación v2.0, el
inventario A2 y el prompt A4 de `Consigna_Plan_Incremental.md`. Esta es una
validación documental; no acredita implementación, pruebas de la app ni
publicación de tags. No reescribe la propuesta.

Limitación de independencia: Codex no redactó A3, pero sí revisó sus entregas
en esta misma conversación. No se realizó la conversación nueva que pide la
consigna para A4; no se afirma independencia total del contexto previo.

## Checklist de los cinco puntos de A4

| Punto | Resultado | Evidencia y límite |
| --- | --- | --- |
| 1. Cada requerimiento pendiente aparece exactamente una vez | Cumple en el escenario de cuatro incrementos | 44 RF y 33 RNF asignados sin faltantes ni duplicados; 23 HU y sus 93 CA cubiertos por las fichas. Fuente: secciones 5–8 del PDF; tablas 3 y 4 de A3. Los RNF se vuelven a comprobar en los incrementos afectados aunque su cierre se asigne una sola vez. |
| 2. Nada queda fuera del documento | Cumple en los IDs; condicionado en la publicación | Todos los RF/RNF/HU asignados existen en secciones 5–8. Actualizar al guardar corresponde a D-11/CA-21.4, no a un RF adicional. P-01 sigue abierto: no se puede convertir la suposición de carga por RutaMx en un mecanismo aprobado de publicación (sección 4.3, D-10). |
| 3. Dependencias en orden | Cumple contra A2 | Cero dependencias RF/RNF asignadas después de su dependiente. RNF-32 está en v0.2.0, antes de RNF-06/07 en v0.4.0 (sección 6). La comprobación acepta dependencias dentro del mismo incremento; B1 debe ordenar sus tareas. El catálogo tiene además el bloqueo externo P-01/P-03, que el chequeo de IDs no resuelve. |
| 4. Cada incremento termina en una función ejecutable | Condicionado | Los objetivos son flujos utilizables: generar; editar/agregar, guardar y recuperar; explorar catálogo; completar edición/copia/mapa (sección 3.2). Faltan precisar alcance parcial de RF-18/24/37 antes de las modificaciones posteriores, módulos compartidos de Descubrir y resolución de P-01/P-03. No hay demostración en navegador por tratarse de un plan. |
| 5. Carga razonable para cuatro clases y dos integrantes | No comprobado | A3 reconoce que no conoce horas por clase, trabajo fuera de clase ni ritmo. Los 12/9/10/13 RF no son una estimación de esfuerzo. Hay margen de integración y calibración, pero todavía no evidencia para comprometer cuatro cierres. Sección 12.2: tiempo e integraciones son riesgos. |

## Observaciones para resolver o justificar antes del plan final

1. **Alta: precisar cuándo se considera terminado cada RF.** A3 asigna RF-18,
   RF-24 y RF-37 a v0.2.0 y promete todos los CA de HU-12/HU-20, pero agregar,
   eliminar, reordenar y cambiar preferencias se reparten entre v0.3.0 y v0.5.0.
   RF-18 enumera las cinco intenciones (sección 5, D-05) y CA-20.4 exige
   atomicidad ante fallos durante una modificación (sección 8, p. 24).
   Distinguir la entrega inicial del mecanismo de su cobertura final con todas
   las operaciones: no marcar el RF completo antes de probar sus escenarios
   aplicables. No se requiere duplicar asignaciones: se puede registrar
   cobertura parcial y regresión final en trazabilidad.
2. **Alta: sostener o reducir el compromiso de calendario.** Antes de aceptar
   las fichas, registrar disponibilidad real y bloques de implementación,
   pruebas e integración. Cuatro clases de trabajo más dos de exposición no
   prueban que quepa todo el MVP. Si se conserva como escenario condicionado,
   el plan final debe decirlo y marcar la aceptación del equipo como pendiente,
   sin declarar las fichas aprobadas. Cualquier recorte conserva los RF
   pendientes y su destino posterior en el registro de cambios (consigna,
   entrega y reflexión; riesgo de tiempo, sección 12.2).
3. **Alta para Descubrir: cerrar las condiciones del catálogo.** Mantener
   P-01/P-03 como bloqueos explícitos para implementación y aceptación del
   catálogo, sin asumir resuelto cómo se publican rutas ni inventar categorías
   o regiones. P-02 determina el mapa (secciones 4.3/12.1, D-06 y D-10).
   La autorización de esquema aprobada en bitácora 02 (2026-11-03) debe
   reconocerse al precisar su alcance; no pedir otra vez una aprobación que
   ya cubra la misma acción. Las comprobaciones de migración en copia y
   regresión siguen siendo requisitos del proyecto.
4. **Media: completar módulos del incremento de catálogo.** La ficha v0.4.0
   lista solo M-01/M-02/M-11, pero depende de lectura de rutas públicas y
   visibilidad, y el esquema aún no las ofrece. Secciones 10.1/10.5 disponen
   gestor/repositorio compartidos (M-05/M-09). Precisar en la ficha o B1 sus
   tareas de consulta, metadatos/visibilidad y migración compatible antes de
   suponer el catálogo disponible; que una ruta esté guardada no la hace
   pública (RNF-15/D-10).

También conviene justificar explícitamente la excepción de prioridad:
HU-01/HU-05/HU-17 (Alta) quedan después de HU-19 (Media). A3 argumenta
riesgo y agrupación de flujos; el equipo debe aceptar esa justificación
respecto del orden de criterios de A3 (prioridad antes de riesgo). No se
modifica aquí la prioridad de las HU de la sección 7.

## Verificación reproducible

Desde la raíz del repositorio; no requiere base, red ni temporales. La fuente
PDF se contrastó con PDFKit: secciones 4.2/4.3, 5–8, 10.1–10.5 y 12.1–12.2;
para los IDs completos se conserva el comando de `A1_Conteo_Independiente_Codex.md`.
Este bloque comprueba las asignaciones y el orden contra A2, no la viabilidad
ni la corrección semántica de cada dependencia:

```sh
PYTHONDONTWRITEBYTECODE=1 venv/bin/python - <<'PY'
from pathlib import Path
import re
plan=Path('documentacion/A3_Propuesta_Incrementos.md').read_text()
inventory=Path('documentacion/A2_Inventario_Requerimientos.md').read_text()
where={}
for kind,start,end,total in [('RF','## 3.','## 4.',44),('RNF','## 4.','## 5.',33)]:
    ids=[]
    for line in plan.split(start,1)[1].split(end,1)[0].splitlines():
        if re.match(r'^\| [2-5] ',line):
            inc=int(line.split('|')[1].strip().split()[0])
            found=re.findall(r'\b'+kind+r'-\d+',line)
            ids+=found
            where.update({x:inc for x in found})
    missing=sorted({f'{kind}-{i:02}' for i in range(1,total+1)}-set(ids))
    duplicates=sorted({x for x in ids if ids.count(x)>1})
    print(kind, 'asignaciones=',len(ids),'únicos=',len(set(ids)),'faltantes=',missing,'duplicados=',duplicates)
    assert len(ids)==total and not missing and not duplicates
violations=[]
for line in inventory.splitlines():
    if re.match(r'^\| (RF|RNF)-',line):
        cells=[c.strip() for c in line.split('|')[1:-1]]
        item=cells[0]
        deps=cells[5 if item.startswith('RF-') else 4]
        for dep in re.findall(r'\b(?:RF|RNF)-\d+',deps):
            if where[dep]>where[item]: violations.append((item,dep))
print('Dependencias posteriores contra A2:',violations)
assert not violations
histories=[]
for i, ficha in enumerate(plan.split('### Incremento ')[1:],2):
    row=next(l for l in ficha.splitlines() if l.startswith('| HU incluidas'))
    ids=re.findall(r'HU-\d+',row)
    histories+=ids
    total=sum(5 if x=='HU-12' else 4 for x in ids)
    print('Incremento',i,'HU=',len(ids),'CA por HU=',total)
assert len(histories)==23 and len(set(histories))==23
print('HU únicas=23; CA asignados por sus HU=93')
PY
```

Salida real (código 0):

```text
RF asignaciones= 44 únicos= 44 faltantes= [] duplicados= []
RNF asignaciones= 33 únicos= 33 faltantes= [] duplicados= []
Dependencias posteriores contra A2: []
Incremento 2 HU= 6 CA por HU= 25
Incremento 3 HU= 5 CA por HU= 20
Incremento 4 HU= 5 CA por HU= 20
Incremento 5 HU= 7 CA por HU= 28
HU únicas=23; CA asignados por sus HU=93
```

Quedan observaciones abiertas; el paso A5 debe resolverlas o justificar por qué
se conservan antes de presentar el resultado como listo para publicar.
