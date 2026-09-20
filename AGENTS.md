# Instrucciones para agentes de IA — RutaMX

Este proyecto lo trabajan dos personas con dos IAs distintas: Angel con
Claude Code, Roberto con Codex. Estas instrucciones aplican por igual a
cualquier IA que toque este repo, sin importar cuál.

## Leer primero, siempre

Antes de proponer un plan, escribir código, o responder cualquier
pregunta sobre el estado del proyecto, lee los archivos de
[`bitacora_proyecto/`](bitacora_proyecto/) (los 3 primeros siempre; el 4.º si
vas a tocar etiquetas, destinos, restaurantes u hoteles):

1. **`bitacora_proyecto/01_LO_QUE_YA_ESTA_HECHO.md`** — qué ya existe y
   funciona. No reimplementes algo que ya está hecho.
2. **`bitacora_proyecto/02_LO_QUE_FALTA.md`** — qué falta y qué se decidió
   hacer después. Si vas a trabajar en algo, checa aquí primero si ya hay
   un plan o una prioridad distinta a la que ibas a asumir.
3. **`bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`** — el porqué de
   decisiones que no son obvias leyendo el código. Si estás por deshacer
   o contradecir algo documentado aquí, dile al usuario explícitamente
   qué decisión estás cambiando y por qué, no lo hagas en silencio.

4. **`bitacora_proyecto/04_PLAN_RESTAURANTES_Y_HOTELES.md`** — el plan (aún sin
   implementar) para re-etiquetar la base de destinos y agregar restaurantes y
   hoteles. Si vas a tocar `destinos`, sus etiquetas, o cómo se recomienda
   comer/dormir, síguelo o dile al usuario qué cambia y por qué. Si lo
   implementas por fases, actualiza su checklist.

5. **`bitacora_proyecto/05_EFECTOS_VISUALES_PROTEGIDOS.md`** — los 8 efectos
   visuales de rare-ui que **nunca se quitan ni se reemplazan**. Léelo siempre
   que vayas a tocar HTML, CSS o JS del frontend, y en especial si vas a
   rediseñar la interfaz (por ejemplo con una skill de diseño): se puede
   cambiar cómo se ven, pero los efectos y sus ganchos se conservan.

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
- Pendientes nuevos (todavía sin hacer) → `02_LO_QUE_FALTA.md`
- El "por qué" de una decisión no obvia, o un bug raro que costó
  diagnosticar → `03_DECISIONES_Y_NOTAS.md`

**Regla estricta sobre `02_LO_QUE_FALTA.md`: ese archivo es SOLO lo que
todavía no está hecho.** En cuanto algo que estaba ahí se termina:
1. Escribe la explicación completa (qué se hizo, cómo, archivos
   involucrados) en `01_LO_QUE_YA_ESTA_HECHO.md`.
2. Borra por completo esa entrada de `02_LO_QUE_FALTA.md` — nunca la
   dejes ahí marcada como "✅ Ya implementado" ni nada parecido. Si algo
   quedó "✅ hecho" pero sigue escrito en el archivo de "lo que falta", es
   un error: bórralo de ahí, no lo dejes con una marca de completado.
3. Si dentro de esa feature ya terminada queda algo genuinamente
   pendiente (un caso no probado, un detalle suelto), ese pedazo específico
   sí puede quedarse en `02_LO_QUE_FALTA.md` como su propio punto — pero
   como un pendiente normal, no colgado debajo de un encabezado que diga
   que ya se implementó.

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
- Toda ventana flotante nueva debe ser un `<dialog>` nativo abierto con
  `showModal()`: `styles.css` ya congela la página de atrás mientras haya
  un `<dialog open>` (solo se mueve la ventana). No uses divs con overlay
  propio ni pongas `overflow` en `body` a mano — se rompería esa regla.
- Si cambias reglas de la app (gasto, tramos, cuándo se recomienda comer o
  dormir, qué se pregunta en el formulario), actualiza también la IA de
  "Planear con IA": los prompts de `app/services/llm_provider.py` y, sobre
  todo, `ai_service.preparar_objetivos_ia`, que hace cumplir las reglas en el
  servidor aunque el modelo se equivoque.
- Explica el "por qué" de un bug antes o junto con el arreglo, no solo
  apliques el fix sin decir la causa.
- Para cambios grandes o con varios pasos, plantea el plan y espera
  confirmación antes de tocar código — a menos que el usuario ya haya
  dado permiso explícito de avanzar sin confirmación en esa conversación.

## Stack del proyecto (referencia rápida)

Flask + vanilla JS + Supabase (Postgres, vía SQLAlchemy). Ver
`bitacora_proyecto/01_LO_QUE_YA_ESTA_HECHO.md` para el detalle completo de
cómo está armado cada módulo.
