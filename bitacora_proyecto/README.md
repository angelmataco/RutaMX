# Bitácora del proyecto RutaMX

Esta carpeta **sí está en GitHub** — es la fuente de verdad compartida
entre Angel (con Claude) y Roberto (con Codex) para que cualquiera de los
dos, usando cualquier IA, entienda el proyecto antes de tocar código y no
se "salga de la línea" haciendo cosas que ya se decidieron distinto o
duplicando trabajo.

Las instrucciones que hacen que una IA la lea automáticamente están en
[`../CLAUDE.md`](../CLAUDE.md) (Claude Code) y [`../AGENTS.md`](../AGENTS.md)
(Codex y otros agentes) en la raíz del proyecto — ambos apuntan aquí como
lectura obligatoria antes de cualquier cambio.

## Archivos

- **`01_LO_QUE_YA_ESTA_HECHO.md`** — todo lo que ya funciona en la app,
  organizado por tema.
- **`02_LO_QUE_FALTA.md`** — lo pendiente, con prioridad y next steps.
- **`03_DECISIONES_Y_NOTAS.md`** — el "por qué" detrás de decisiones que no
  son obvias con solo ver el código (por qué se cambió de X a Y, bugs
  raros que ya se resolvieron, cosas que probamos y no funcionaron).
- **`04_PLAN_RESTAURANTES_Y_HOTELES.md`** — el plan detallado (todavía sin
  implementar) para re-etiquetar la base de destinos y agregar restaurantes y
  hoteles con calidad, sin pagar nada, y que toda la app y la IA sigan
  fluyendo igual.

## Regla para cualquier IA (Claude, Codex, o la que sea)

1. **Antes de proponer o hacer cualquier cambio**, leer los archivos de
   esta carpeta (01, 02 y 03 siempre; el 04 si tocas destinos, etiquetas,
   restaurantes u hoteles) para tener el contexto completo del proyecto.
2. **Después de hacer un cambio real** (funcionalidad nueva, bug
   arreglado, decisión de arquitectura, o incluso una idea nueva que
   Angel o Roberto mencionen aunque no se implemente todavía), actualizar
   el archivo que corresponda en el mismo turno — no dejarlo para después
   ni esperar a que se lo pidan.
3. Si el cambio contradice algo escrito aquí (por ejemplo, una decisión
   documentada en `03_DECISIONES_Y_NOTAS.md`), avisar explícitamente antes
   de proceder — puede ser una decisión vieja que ya no aplica, pero hay
   que confirmarlo, no sobreescribirlo en silencio.
4. Mantenerlo en español y en el mismo tono directo/informal que ya
   tienen estos archivos — son para que Angel y Roberto los lean rápido,
   no documentación formal.
