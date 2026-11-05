# [V2] A1: conteo independiente de la especificación

Fecha: 2026-11-05. Responsable: codex-par.

Fuente única del conteo: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf`.
No leí `A1_Verificacion_Especificacion.md` antes de entregar este conteo. Los
números adelantados en la tabla de trabajo se trataron como hipótesis; este
resultado sale directamente del PDF. El contraste con el análisis de Claude
corresponde al paso 4 y todavía no se ha realizado aquí.

| Tipo | IDs únicos definidos | Sección | Páginas del PDF |
| --- | ---: | --- | --- |
| RF | 44 | 5 | 11–13 |
| RNF | 33 | 6 | 14–15 |
| HU | 23 | 7 | 16–17 |
| CA individuales | 93 | 8 | 18–25 |

Los RF van de RF-01 a RF-44, los RNF de RNF-01 a RNF-33 y las HU de HU-01
a HU-23, sin huecos ni definiciones duplicadas. Hay 23 grupos de criterios:
cada grupo contiene los sufijos .1 a .4, salvo CA-12, que contiene .1 a .5.
No faltan grupos ni sufijos intermedios. Las listas completas quedan en la
salida reproducible de abajo. Se cuentan las definiciones en su sección y se
contrastan con los IDs únicos de todo el PDF para evitar sumar referencias
repetidas en matrices, anexos o bitácoras. En RNF se exige la categoría
después del ID para excluir una referencia a RNF-29 que PDFKit coloca al
inicio de una línea dentro del texto de RNF-25 (página 15).

## Diferencia interna del documento

El control del documento (página 2) menciona **92 criterios** al describir la
versión 1.0. La sección 8 de la versión 2.0 define **93**: en la página 22
aparece **CA-12.5**, que exige consistencia del chat, itinerario y mapa con la
ruta estructurada. El anexo **A.4**, página 45, lo identifica expresamente
como criterio nuevo para cubrir **RF-43**. Por tanto, 23 × 4 = 92 omite este
criterio adicional. Para el inventario y la trazabilidad de v2.0 se propone
usar los **93 criterios realmente definidos**, sin modificar el PDF.

## Comando reproducible

Ejecutar desde la raíz del repositorio, con el entorno `venv` y PDFKit de
macOS disponibles. No usa la base, la red ni archivos temporales. El sufijo
decimal de CA es obligatorio: contar solo `CA-[0-9]+` contaría 23 grupos.

```sh
PYTHONDONTWRITEBYTECODE=1 venv/bin/python - <<'PY'
import hashlib, json, re, subprocess
from pathlib import Path
pdf = Path("documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf")
swift = '''import Foundation
import PDFKit
let d = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
let pages = (0..<d.pageCount).map { d.page(at: $0)!.string ?? "" }
let data = try JSONSerialization.data(withJSONObject: pages)
print(String(data: data, encoding: .utf8)!)
'''
r = subprocess.run(["swift", "-e", swift, str(pdf)], capture_output=True, text=True, check=True)
pages = json.loads(r.stdout)
text = "\n".join(pages)
print("SHA256:", hashlib.sha256(pdf.read_bytes()).hexdigest())
print("Páginas:", len(pages))
for kind, first, last in [("RF",11,13),("RNF",14,15),("HU",16,17),("CA",18,25)]:
    pattern = rf"\b{kind}-\d+" + (r"\.\d+" if kind == "CA" else "") + r"\b"
    section = "\n".join(pages[first-1:last])
    # RNF-29 también aparece como referencia al inicio de una línea de RNF-25.
    row_pattern = pattern + (r"(?: \(\*\))? (?:Usabilidad|Rendimiento|Seguridad|Mantenibilidad|Modularidad|Compatibilidad|Pruebas|Documentación)" if kind == "RNF" else "")
    definitions = [m.group(0).split()[0] for m in re.finditer(r"^" + row_pattern, section, re.M)]
    unique = set(definitions)
    all_mentions = set(re.findall(pattern, text))
    nums = sorted({int(x.split("-")[1].split(".")[0]) for x in unique})
    missing = sorted(set(range(1, max(nums)+1)) - set(nums))
    duplicates = sorted(x for x in unique if definitions.count(x)>1)
    print(f"{kind}: definiciones={len(definitions)}, únicos={len(unique)}, únicos PDF completo={len(all_mentions)}, huecos={missing}, duplicados={duplicates}, coincide={unique == all_mentions}")
    if kind == "CA":
        for group in nums:
            suffixes = sorted(int(x.split(".")[1]) for x in unique if int(x.split("-")[1].split(".")[0]) == group)
            gaps = sorted(set(range(1,max(suffixes)+1))-set(suffixes))
            print(f"  CA-{group:02}: sufijos={suffixes}, huecos={gaps}")
    print("  IDs:", ", ".join(sorted(unique, key=lambda x: tuple(map(int,x.split("-")[1].split("."))))))
PY
```

## Resultado real

Salida del comando anterior (código de salida 0):

```text
SHA256: ebc5d58398693f5e8f28fcf49a2c2c5ee48ce86b5f855ddbb1c09f868a8915df
Páginas: 46
RF: definiciones=44, únicos=44, únicos PDF completo=44, huecos=[], duplicados=[], coincide=True
  IDs: RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08, RF-09, RF-10, RF-11, RF-12, RF-13, RF-14, RF-15, RF-16, RF-17, RF-18, RF-19, RF-20, RF-21, RF-22, RF-23, RF-24, RF-25, RF-26, RF-27, RF-28, RF-29, RF-30, RF-31, RF-32, RF-33, RF-34, RF-35, RF-36, RF-37, RF-38, RF-39, RF-40, RF-41, RF-42, RF-43, RF-44
RNF: definiciones=33, únicos=33, únicos PDF completo=33, huecos=[], duplicados=[], coincide=True
  IDs: RNF-01, RNF-02, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-08, RNF-09, RNF-10, RNF-11, RNF-12, RNF-13, RNF-14, RNF-15, RNF-16, RNF-17, RNF-18, RNF-19, RNF-20, RNF-21, RNF-22, RNF-23, RNF-24, RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-32, RNF-33
HU: definiciones=23, únicos=23, únicos PDF completo=23, huecos=[], duplicados=[], coincide=True
  IDs: HU-01, HU-02, HU-03, HU-04, HU-05, HU-06, HU-07, HU-08, HU-09, HU-10, HU-11, HU-12, HU-13, HU-14, HU-15, HU-16, HU-17, HU-18, HU-19, HU-20, HU-21, HU-22, HU-23
CA: definiciones=93, únicos=93, únicos PDF completo=93, huecos=[], duplicados=[], coincide=True
  CA-01: sufijos=[1, 2, 3, 4], huecos=[]
  CA-02: sufijos=[1, 2, 3, 4], huecos=[]
  CA-03: sufijos=[1, 2, 3, 4], huecos=[]
  CA-04: sufijos=[1, 2, 3, 4], huecos=[]
  CA-05: sufijos=[1, 2, 3, 4], huecos=[]
  CA-06: sufijos=[1, 2, 3, 4], huecos=[]
  CA-07: sufijos=[1, 2, 3, 4], huecos=[]
  CA-08: sufijos=[1, 2, 3, 4], huecos=[]
  CA-09: sufijos=[1, 2, 3, 4], huecos=[]
  CA-10: sufijos=[1, 2, 3, 4], huecos=[]
  CA-11: sufijos=[1, 2, 3, 4], huecos=[]
  CA-12: sufijos=[1, 2, 3, 4, 5], huecos=[]
  CA-13: sufijos=[1, 2, 3, 4], huecos=[]
  CA-14: sufijos=[1, 2, 3, 4], huecos=[]
  CA-15: sufijos=[1, 2, 3, 4], huecos=[]
  CA-16: sufijos=[1, 2, 3, 4], huecos=[]
  CA-17: sufijos=[1, 2, 3, 4], huecos=[]
  CA-18: sufijos=[1, 2, 3, 4], huecos=[]
  CA-19: sufijos=[1, 2, 3, 4], huecos=[]
  CA-20: sufijos=[1, 2, 3, 4], huecos=[]
  CA-21: sufijos=[1, 2, 3, 4], huecos=[]
  CA-22: sufijos=[1, 2, 3, 4], huecos=[]
  CA-23: sufijos=[1, 2, 3, 4], huecos=[]
  IDs: CA-01.1, CA-01.2, CA-01.3, CA-01.4, CA-02.1, CA-02.2, CA-02.3, CA-02.4, CA-03.1, CA-03.2, CA-03.3, CA-03.4, CA-04.1, CA-04.2, CA-04.3, CA-04.4, CA-05.1, CA-05.2, CA-05.3, CA-05.4, CA-06.1, CA-06.2, CA-06.3, CA-06.4, CA-07.1, CA-07.2, CA-07.3, CA-07.4, CA-08.1, CA-08.2, CA-08.3, CA-08.4, CA-09.1, CA-09.2, CA-09.3, CA-09.4, CA-10.1, CA-10.2, CA-10.3, CA-10.4, CA-11.1, CA-11.2, CA-11.3, CA-11.4, CA-12.1, CA-12.2, CA-12.3, CA-12.4, CA-12.5, CA-13.1, CA-13.2, CA-13.3, CA-13.4, CA-14.1, CA-14.2, CA-14.3, CA-14.4, CA-15.1, CA-15.2, CA-15.3, CA-15.4, CA-16.1, CA-16.2, CA-16.3, CA-16.4, CA-17.1, CA-17.2, CA-17.3, CA-17.4, CA-18.1, CA-18.2, CA-18.3, CA-18.4, CA-19.1, CA-19.2, CA-19.3, CA-19.4, CA-20.1, CA-20.2, CA-20.3, CA-20.4, CA-21.1, CA-21.2, CA-21.3, CA-21.4, CA-22.1, CA-22.2, CA-22.3, CA-22.4, CA-23.1, CA-23.2, CA-23.3, CA-23.4
```
