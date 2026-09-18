# Instrucciones para agentes de IA — RutaMX

Este proyecto lo trabajan dos personas con dos IAs distintas: Angel con
Claude Code, Roberto con Codex. Estas instrucciones aplican por igual a
cualquier IA que toque este repo, sin importar cuál.

## Leer primero, siempre

Antes de proponer un plan, escribir código, o responder cualquier
pregunta sobre el estado del proyecto, lee los 3 archivos de
[`bitacora_proyecto/`](bitacora_proyecto/):

1. **`bitacora_proyecto/01_LO_QUE_YA_ESTA_HECHO.md`** — qué ya existe y
   funciona. No reimplementes algo que ya está hecho.
2. **`bitacora_proyecto/02_LO_QUE_FALTA.md`** — qué falta y qué se decidió
   hacer después. Si vas a trabajar en algo, checa aquí primero si ya hay
   un plan o una prioridad distinta a la que ibas a asumir.
3. **`bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`** — el porqué de
   decisiones que no son obvias leyendo el código. Si estás por deshacer
   o contradecir algo documentado aquí, dile al usuario explícitamente
   qué decisión estás cambiando y por qué, no lo hagas en silencio.

Esto evita que dos IAs trabajando en paralelo (Claude y Codex) se
contradigan, dupliquen trabajo, o reintroduzcan un bug que ya se arregló
por una razón específica documentada ahí.

## Mantener la bitácora actualizada

Cada vez que hagas un cambio real en el proyecto — una funcionalidad
nueva, un bug arreglado, una decisión de arquitectura, o incluso una idea
nueva que el usuario mencione aunque todavía no se implemente — actualiza
el archivo de `bitacora_proyecto/` que corresponda, en el mismo turno en
el que haces el cambio. No es opcional ni hay que esperar a que te lo
pidan explícitamente.

- Cosas que ya quedaron funcionando → `01_LO_QUE_YA_ESTA_HECHO.md`
- Pendientes nuevos, o pendientes que se resolvieron → `02_LO_QUE_FALTA.md`
- El "por qué" de una decisión no obvia, o un bug raro que costó
  diagnosticar → `03_DECISIONES_Y_NOTAS.md`

Escribe en español, directo y sin relleno — igual que el tono que ya
tienen esos archivos. Actualiza la fecha de "Última actualización" al
inicio del archivo que edites.

## Reglas de trabajo del proyecto (ya validadas con el usuario)

- Verifica los cambios en la app corriendo de verdad (navegador), no solo
  con `pytest` — varios bugs reales de esta app solo se detectaron
  probando en vivo.
- No inventes datos: coordenadas, población, o cualquier dato geográfico
  siempre se verifica contra una fuente real (Nominatim/OpenStreetMap para
  coordenadas), nunca se aproxima a mano.
- Explica el "por qué" de un bug antes o junto con el arreglo, no solo
  apliques el fix sin decir la causa.
- Para cambios grandes o con varios pasos, plantea el plan y espera
  confirmación antes de tocar código — a menos que el usuario ya haya
  dado permiso explícito de avanzar sin confirmación en esa conversación.

## Stack del proyecto (referencia rápida)

Flask + vanilla JS + Supabase (Postgres, vía SQLAlchemy). Ver
`bitacora_proyecto/01_LO_QUE_YA_ESTA_HECHO.md` para el detalle completo de
cómo está armado cada módulo.
