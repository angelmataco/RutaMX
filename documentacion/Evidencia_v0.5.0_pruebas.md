# [V2] Evidencia de pruebas del incremento v0.5.0

- Fecha: **19 de noviembre de 2026 (CDMX)**. Todo con datos ficticios, sin red y sin tocar Supabase.
- Alcance: editar por chat (eliminar, reordenar, preferencias y aviso de acción no soportada), copiar rutas públicas, mapa del detalle de Descubrir y cierre.
- Estados usados: «programado», «probado en simulación», «verificado en uso real (fecha)» y «sin verificar (fecha)».

## 1. Regresión disponible sin PostgreSQL

Comando, desde la raíz del repositorio:

```sh
env -u RUTAMX_TEST_DB_URL \
  PYTHONDONTWRITEBYTECODE=1 \
  venv/bin/python -m pytest base_datos/tests v2/tests \
  -q -p no:cacheprovider \
  -k 'not test_navegador_escritorio_y_movil'
```

| Corrida | Resultado | Nota |
|---|---|---|
| Base del v0.4.0 (17 de noviembre) | 529 passed, 34 skipped, 1 deselected | Punto de partida. |
| Tras el paso del mapa (M6), primera corrida con la prueba de contrato nueva | 1 failed, 745 passed, 39 skipped, 1 deselected | La prueba buscaba un texto de `descubrir.js` que la corrección posterior cambió (`listos === 2` por `listos === necesarios`). Se actualizó la aserción; el código era correcto. |
| **Final, 19 de noviembre** | **746 passed, 39 skipped, 1 deselected, 0 failed** | Corrida del cierre. |

Las **39 omitidas** son pruebas de integración que exigen un PostgreSQL desechable (`RUTAMX_TEST_DB_URL`): 26 en `test_rutas_repositorio.py` (un caso parametrizado cuenta dos), 5 en `test_migracion_catalogo.py` y 8 en `test_catalogo_repositorio.py`. Son las 34 de antes más **5 integraciones nuevas** de la copia de rutas. La **1 excluida** es la prueba de navegador de Planear (`-k`): no pasó ni se ejecutó.

No se exigió superar 529: se informa lo que dio. Subió a 746 porque se agregaron 217 pruebas (casos parametrizados incluidos).

## 2. Lo que no se ejecutó

El ensayo en Node del mapa (sección 3) **sí se ejecutó**, pero como simulación: un DOM, `fetch` y Leaflet falsos corren el `descubrir.js` real. Apoya «probado en simulación», no «verificado en uso real», y no sustituye al navegador. El script vive fuera del repositorio.

| Qué | Por qué | Consecuencia |
|---|---|---|
| Integraciones con PostgreSQL (39) | `127.0.0.1:55433` no respondió el 19 de noviembre; no se levantó otra base | El SQL de `copiar_publica` y sus 5 integraciones nuevas **no se ejecutaron contra PostgreSQL**. Sin verificar (2026-11-19). |
| Navegador (escritorio 1280×900 y móvil 375×812) | Chromium sigue bloqueado; no se reintentó por otra vía | Mapa, aviso de fallo del proveedor, botón de copiar y mensajes de Planear sin verificar (2026-11-19). |
| Regresión de v1 | Fuera del comando acordado | Sin verificar (2026-11-19). |
| IA real, login real, Supabase | Sin llave, sin credenciales de prueba, sin migración en la base real | Sin verificar (2026-11-19). |

## 3. Ensayo en Node del mapa (11 escenarios, todos correctos)

Carga de Leaflet 1.9.4 desde unpkg (estilos y script); dibujo de tres marcadores con extremos rellenos; textos del popup como texto, no HTML; destrucción del mapa al cerrar; aviso de «N ubicaciones omitidas»; un solo punto con zoom 10; sin puntos (no carga Leaflet); fallo de Leaflet con detalle y Copiar vivos; teselas fallidas; respuesta tardía descartada; `window.L` ya presente sin estilos (espera los estilos); estilos fallidos y luego otro detalle (reintenta solo los estilos y no dibuja sin ellos); paso del detalle A al B sin cruce de temporizadores.

## 4. Matriz RF → prueba (RNF-26 y RNF-33)

Todas las pruebas están en `v2/tests/` salvo las marcadas `repo` (`base_datos/tests/test_catalogo_repositorio.py`). Todas **probadas en simulación**; las marcadas «omitida» exigen PostgreSQL y no se ejecutaron.

| CP | RF | Archivo: prueba |
|---|---|---|
| CP-27 | RF-27 eliminar parada | `test_adaptador_ia.py`: `test_modificaciones_normalizadas`, `test_modificacion_invalida`. `test_gestor_rutas.py`: `test_eliminar_conserva_demas_paradas_y_extremos`, `test_eliminar_ultima_parada_es_valido`, `test_eliminar_invalido_preserva_ruta`, `test_eliminar_nombre_ambiguo_pide_posicion`. `test_orquestador.py`: `test_eliminar_por_chat_actualiza_itinerario_y_permite_cero_paradas`. |
| CP-28 | RF-28 itinerario sin afectar las demás | `test_gestor_rutas.py`: `test_eliminar_conserva_demas_paradas_y_extremos`, `test_modificacion_con_fallo_geografico_intermedio_es_atomica`. `test_orquestador.py`: `test_cambios_invalidos_por_chat_conservan_itinerario`. |
| CP-29 | RF-29 reordenar | `test_adaptador_ia.py`: `test_modificaciones_normalizadas`, `test_modificacion_invalida`. `test_gestor_rutas.py`: `test_reordenar_preserva_contenido_y_actualiza_vistas`, `test_reordenar_invalido_preserva_ruta`, `test_reordenar_mismo_orden_no_consulta_geografia`. `test_orquestador.py`: `test_reordenar_por_chat_actualiza_secuencia_sin_generar_otra_ruta`, `test_reordenar_una_parada_informa_sin_cambios`. |
| CP-30 | RF-30 nueva secuencia visible | `test_gestor_rutas.py`: `test_reordenar_preserva_contenido_y_actualiza_vistas`. `test_orquestador.py`: `test_reordenar_por_chat_actualiza_secuencia_sin_generar_otra_ruta`. |
| CP-31 | RF-31 solo duración y tipo de lugares | `test_adaptador_ia.py`: `test_modificaciones_normalizadas`, `test_modificacion_invalida`. `test_orquestador.py`: `test_preferencias_regeneran_y_actualizan_itinerario`, `test_preferencias_iguales_no_regeneran`, `test_preferencias_invalidas_no_cambian_datos_ni_ruta`, `test_quitar_intereses_regenera_con_lista_vacia`, `test_preferencia_extraida_valida_actualiza_ruta`. |
| CP-32 | RF-32 itinerario actualizado tras preferencias | `test_orquestador.py`: `test_preferencias_regeneran_y_actualizan_itinerario`, `test_preferencias_con_fallo_geografico_preservan_ambos_estados`, `test_preferencias_pendientes_no_confirman_datos_hasta_aceptar`, `test_fallo_preferencias_conserva_datos_anteriores_y_no_regenera_luego`. |
| CP-34 | RF-34 acción no soportada | `test_orquestador.py`: `test_rf34_enumera_operaciones_y_conserva_ruta`. `test_adaptador_ia.py`: `test_instruccion_del_proveedor_lista_las_cinco_intenciones`. |
| CP-13 | RF-13 copiar con sesión | `test_interfaz_descubrir.py`: `test_copiar_usa_sesion_e_ignora_usuario_en_cuerpo`, `test_copiar_csrf_invalido_da_403`, `test_copiar_id_invalido_no_llama_servicio`. `test_copia_rutas.py`: `test_copia_devuelve_id_y_nombre_limpio`, `test_ruta_inexistente_o_privada_no_se_copia`. `test_pantalla_descubrir.py`: `test_detalle_incluye_copia_sesion_y_csrf`. |
| CP-14 | RF-14 copia propia sin tocar la original | repo: `test_copiar_es_una_sola_sentencia_con_condicion_publica`, `test_copiar_no_escribe_autor_ni_toca_la_original`; `test_integracion_copiar_crea_copia_privada_y_no_toca_la_original` y `test_integracion_copiar_dos_veces_crea_dos_copias_independientes` (omitidas). |
| CP-15 | RF-15 pedir sesión al anónimo | `test_interfaz_descubrir.py`: `test_copiar_sin_sesion_valida_da_401_sin_copiar`, `test_anonimo_puede_iniciar_sesion_y_copiar_misma_ruta`. `test_pantalla_descubrir.py`: `test_detalle_incluye_copia_sesion_y_csrf`. |
| CP-16 | RF-16 error sin copia incompleta | `test_interfaz_descubrir.py`: `test_copiar_errores_del_servicio_se_traducen`. `test_copia_rutas.py`: `test_fallo_del_repositorio_es_mensaje_seguro`, `test_migracion_pendiente_tiene_mensaje_propio`, `test_datos_invalidos_se_rechazan_sin_copiar`. repo: `test_copiar_con_otro_error_es_mensaje_seguro_sin_commit`, `test_copiar_con_columnas_faltantes_da_migracion_pendiente`; `test_integracion_copiar_con_fallo_no_deja_copia_parcial` (omitida). |
| CP-11 | RF-11 mapa del recorrido | `test_catalogo.py`: `test_puntos_del_mapa_van_en_orden_origen_paradas_destino`, `test_ruta_sin_paradas_dibuja_origen_y_destino`, `test_limites_validos_de_coordenadas_se_aceptan`. `test_interfaz_descubrir.py`: `test_detalle_con_resumen_devuelve_puntos_en_orden_sin_el_resumen`. `test_pantalla_descubrir.py`: `test_detalle_incluye_bloque_del_mapa_con_avisos_accesibles`, `test_js_carga_leaflet_del_mismo_cdn_que_v1_y_solo_bajo_demanda`, `test_css_del_mapa_tiene_alto_fijo_de_escritorio_y_movil`. repo: `test_detalle_trae_resumen_solo_para_el_mapa`. |
| CP-12 | RF-12 aviso si el mapa falla | `test_catalogo.py`: `test_parada_con_coordenadas_invalidas_se_omite_y_se_cuenta`, `test_sin_ruta_estructurada_no_hay_puntos_ni_falla`, `test_proyeccion_no_expone_resumen_ni_datos_privados`. `test_interfaz_descubrir.py`: `test_detalle_sin_resumen_trae_mapa_vacio_y_no_expone_resumen`. `test_pantalla_descubrir.py`: `test_js_del_mapa_trae_los_textos_acordados`, `test_js_del_mapa_protege_contra_mapas_viejos_y_espera_css_y_js`. Más el ensayo en Node. |

Cada RF del incremento tiene al menos un caso (RNF-26). La parte de JavaScript (mapa, botón de copiar, avisos) solo se ejecutó en el ensayo en Node y en pruebas de contrato sobre el texto del archivo.

## 5. Criterios de aceptación con tratamiento especial

| CA | Estado | Detalle |
|---|---|---|
| CA-18.4 (varias operaciones en un mensaje) | **Limitación** | El contrato de M-07 interpreta una acción por mensaje. Si la IA responde `no_soportada`, no cambia nada. No se fingió. |
| CA-08.4 (completar la copia tras iniciar sesión) | **Parcial** | La prueba `test_anonimo_puede_iniciar_sesion_y_copiar_misma_ruta` cubre el servidor; que el detalle abierto se conserve tras el login en el navegador queda sin verificar (2026-11-19). |

## 6. Comprobaciones adicionales

- `node --check v2/static/descubrir.js`: sin errores.
- `git diff --check` sobre `v2`, `base_datos` y `bitacora_proyecto`: sin espacios sobrantes.
- `descubrir.js` no usa `innerHTML` ni `insertAdjacentHTML` (prueba `test_js_no_usa_innerhtml`).
