# [V2] A1: Verificación de la especificación v2.0

- Fecha: 2026-11-05 (CDMX). Autora: claude-par. Revisora: codex-par.
- Documento fuente (única fuente): `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (versión 2.0, 8 de octubre de 2026, 46 páginas).
- Consigna: `documentacion/Consigna_Plan_Incremental.md` (prompt A1).
- Los totales de este archivo son provisionales hasta contrastarlos con el conteo ciego de Codex (`A1_Conteo_Independiente_Codex.md`) en el paso 4 (A2).

## 1. Cómo se contó (reproducible)

Todo se ejecuta desde la raíz del repo, con PDFKit de macOS (viene con el sistema; no usa red, base de datos ni archivos dentro del repo). El texto se extrae a un archivo temporal fuera del repo (`$TMPDIR`):

```sh
PDF="documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf"
swift -e 'import PDFKit
let d = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
print(d.string ?? "")' "$PDF" > "${TMPDIR:-/tmp}/v2.0.txt"
T="${TMPDIR:-/tmp}/v2.0.txt"
grep -o -E '\bRF-[0-9]+'  "$T" | sort -u | wc -l          # 44
grep -o -E '\bRNF-[0-9]+' "$T" | sort -u | wc -l          # 33
grep -o -E '\bHU-[0-9]+'  "$T" | sort -u | wc -l          # 23
grep -o -E 'CA-[0-9]+\.[0-9]+' "$T" | sort -u | wc -l     # 93
# Continuidad (sin huecos): imprime "OK" si los números van de 1 a N sin saltos
for x in RF:44 RNF:33 HU:23; do p=${x%%:*}; n=${x##*:}
  grep -o -E "\b$p-[0-9]+" "$T" | sed "s/$p-//" | sort -un | awk -v n=$n -v p=$p '{if($1!=NR)bad=1} END{print p, (NR==n && !bad)?"OK":"HUECO"}'
done
# Grupos de CA: cada HU debe tener .1 a .4 (HU-12 hasta .5)
grep -o -E 'CA-[0-9]+\.[0-9]+' "$T" | sort -u | awk -F'[-.]' '{c[$2]++} END{for(k in c) print k, c[k]}' | sort -n | awk '$2!=4' # solo imprime 12 5
```

Este bloque es el mismo criterio de conteo que usa el conteo independiente de Codex (`A1_Conteo_Independiente_Codex.md`), que además cuenta solo las definiciones dentro de cada sección. Resultado de correr este bloque el 2026-11-05: 44, 33, 23, 93; RF OK, RNF OK, HU OK; y la única historia con distinto de 4 criterios es la 12 con 5.

Los CA siguen el formato `CA-HH.n`: 23 historias con 4 criterios cada una, salvo HU-12 con 5 (CA-12.5).

## 2. Secciones del documento

1. Presentación y contexto: 1.1 Datos generales; 1.2 Equipo y roles; 1.3 Contexto del problema; 1.4 Solución a desarrollar; 1.5 Propósito de este documento
2. Usuario objetivo
3. Alcance del proyecto: 3.1 Funcionalidades dentro del alcance; 3.2 Flujo objetivo del MVP; 3.3 Fuera del alcance
4. Revisión de los requerimientos y decisiones de corrección: 4.1 Resumen de la revisión; 4.2 Decisiones adoptadas (D-01 a D-14); 4.3 Puntos que dependen del cliente o del sitio existente (P-01 a P-03)
5. Requerimientos funcionales corregidos (RF-01 a RF-44)
6. Requerimientos no funcionales corregidos (RNF-01 a RNF-33)
7. Historias de usuario priorizadas (HU-01 a HU-23)
8. Criterios de aceptación (CA-01.1 a CA-23.4)
9. Matriz de trazabilidad: 9.1 Requerimientos funcionales; 9.2 Requerimientos no funcionales; 9.3 Verificación de cobertura
10. Propuesta inicial de módulos del sistema: 10.1 ¿Qué partes principales tendrá el sistema?; 10.2 ¿Qué responsabilidad tiene cada módulo?; 10.3 ¿Qué módulo implementa cada requerimiento?; 10.4 ¿Qué módulo será más difícil de probar?; 10.5 ¿Qué puede reutilizarse como manejador o utilería? (M-01 a M-11)
11. Revisión crítica de historias y criterios
12. Riesgos y ambigüedades: 12.1 Ambigüedades del documento 1.0 y su resolución; 12.2 Riesgos técnicos y cómo se atienden
13. Bitácora de uso de IA: 13.1 Definición del proyecto (versión 1.0); 13.2 Historias, criterios, trazabilidad y módulos (versión 2.0)
14. Preguntas de revisión para el equipo
Anexo A. Control de cambios respecto de la versión 1.0: A.1 Requerimientos funcionales; A.2 Requerimientos no funcionales; A.3 Historias de usuario; A.4 Criterios de aceptación; A.5 Estructura y formato del documento

## 3. Identificadores y sección donde aparecen

| Tipo | Rango | Sección donde se definen | También aparecen en |
|---|---|---|---|
| RF (requerimiento funcional) | RF-01 a RF-44 | 5 | 4.2, 9.1, 10, 12, Anexo A |
| RNF (requerimiento no funcional) | RNF-01 a RNF-33 | 6 | 9.2, 10, Anexo A |
| HU (historia de usuario) | HU-01 a HU-23 | 7 | 5 (columna Historia), 8, 9.1 |
| CA (criterio de aceptación) | CA-01.1 a CA-23.4 (CA-12.5 incluido) | 8 | 9.1, 9.3, Anexo A.4 |

Distribución de los criterios según el documento (sección 8): Normal 24, Límite 23, Error (datos) 23, Error (sistema) 23 = 93.

## 4. Totales

| Tipo | Según el documento | Conteo de este archivo | ¿Coinciden? |
|---|---|---|---|
| RF | 44 (sección 4.1) | 44 | Sí |
| RNF | 33 (sección 4.1) | 33 | Sí |
| HU | 23 (sección 4.1) | 23 | Sí |
| CA | 93 (sección 4.1) | 93 | Sí |

**Diferencia a resolver en A2:** la versión 1.0 declaraba 92 criterios (control de documento de la v2.0) y su texto tiene 92 IDs únicos. La v2.0 declara 93 porque agregó 1 criterio nuevo (CA-12.5, secciones 4.1 y 11). No es un error: para la v2.0 el total correcto es 93, y ese es el que se usa en el plan.

## 5. Ambigüedades, requerimientos sin criterio y puntos abiertos

Sin criterio de aceptación: 0 de 44 RF (sección 9.3), y los 44 RF tienen fila en la matriz 9.1 (comprobado). Sin identificador: ninguno encontrado.

Puntos que siguen abiertos (sección 4.3, dependen del cliente o del sitio existente, no se resolvieron inventando funcionalidad):

| ID | Tema | Impacto en el plan |
|---|---|---|
| P-01 | Mecanismo para marcar una ruta como pública; ningún RF lo describe y RNF-15 lo menciona | Pregunta para el profesor antes de planear lo que lo use (perfil "Creador de rutas") |
| P-02 | Proveedor de mapas y credenciales del sitio existente (D-06) | Condiciona HU-06 |
| P-03 | Valores de categoría y región dependen de los datos del catálogo | Condiciona RF-05 y la carga del catálogo |

Ambigüedades del 1.0 ya resueltas en la v2.0 (sección 12.1; se cita la decisión): D-01 (filtros del MVP: RF-05), D-02 (datos mínimos: RF-19 y RF-20), D-03 (ruta válida: RF-35), D-04 (preferencias: RF-31), D-05, D-07, D-08 y D-09. Corregidos en la v2.0: 15 RF, 8 RNF, 3 HU y 35 CA (sección 4.1).

Observaciones propias de este paso:
1. Los RF y RNF **no traen prioridad propia**: la tabla de la sección 5 solo tiene las columnas ID, requerimiento e Historia, y la de la sección 6 ID, categoría y requerimiento. La prioridad aparece solo en las historias de usuario (sección 7: Alta 12, Media 10, Baja 1). Por eso en A2 la columna de prioridad de cada RF y RNF dirá **"no indicada"**; la prioridad de la HU a la que pertenece cada RF se pondrá en una columna aparte, rotulada como dato derivado de la sección 7, nunca como prioridad explícita del RF.
2. El estado de implementación de cada RF no está en el documento; se determinará con el código y la bitácora en A2 y lo aprueba el usuario.

## 6. Verificaciones hechas

- `grep` de cuatro tipos de ID con `sort -u`: 44, 33, 23 y 93.
- Secuencias consecutivas sin saltos (RF, RNF, HU).
- Los 93 CA se encuentran dentro de la sección 8 y los 93 únicos coinciden con los que aparecen en todo el documento (sin IDs de criterio fuera de la sección 8).
- Cada una de las 44 filas RF existe en la matriz 9.1.
- No se verificó: contra el PDF original (solo contra el texto extraído); el conteo ciego de Codex lo contrasta en el paso 4.
