"""Catálogo con repositorio falso: privacidad, filtros y errores."""
from unittest.mock import Mock
import pytest
from v2.negocio.catalogo import Catalogo, ErrorCatalogo, RutaNoEncontrada
from v2.utilerias import ErrorValidacion
from base_datos.repositorios.catalogo_repositorio import ErrorMigracionPendiente


def fila():
    return dict(id=1, nombre='Ruta', origen='A', destino='B', duracion_dias=3,
                num_paradas=1, categoria='Cultural', region='Centro', es_rutamx=False,
                autor={'nombre':'Persona', 'inicial_apellido':'XYZ', 'pin_hash':'secreto'},
                usuario_id=8, pin_hash='secreto', descripcion='Visita',
                paradas=[{'nombre':'C', 'descripcion':'Museo', 'usuario_id':8}])


def test_lista_proyecta_solo_datos_publicos():
    repo=Mock(); repo.listar_publicas.return_value=[fila()]
    r=Catalogo(repo).listar('  museo  ',3,'Cultural','Centro')[0]
    assert r['autor']=='Persona X.'
    assert 'usuario_id' not in r and 'pin_hash' not in str(r)
    repo.listar_publicas.assert_called_once_with(palabra_clave='museo',duracion_dias=3,categoria='Cultural',region='Centro')


def test_autor_rutamx_solo_con_marca_explicita():
    repo=Mock(); f=fila(); f.update(es_rutamx=True, autor=None)
    repo.listar_publicas.return_value=[f]
    assert Catalogo(repo).listar()[0]['autor']=='RutaMx'
    f['es_rutamx']=False
    assert Catalogo(repo).listar()[0]['autor']=='Autor no disponible'


def test_detalle_conserva_orden_y_descarta_datos_privados():
    repo=Mock(); repo.obtener_publica.return_value=fila()
    assert Catalogo(repo).detalle(1)['paradas']==[{'orden':1,'nombre':'C','descripcion':'Museo'}]


@pytest.mark.parametrize('filtros',[{'palabra_clave':'x'*81},{'palabra_clave':4},
    {'duracion_dias':True},{'duracion_dias':0},{'duracion_dias':'3'},
    {'categoria':'otra'},{'region':'otra'}])
def test_filtros_invalidos_no_consultan(filtros):
    repo=Mock()
    with pytest.raises(ErrorValidacion): Catalogo(repo).listar(**filtros)
    repo.listar_publicas.assert_not_called()


def test_filtros_vacios_y_sin_resultados():
    repo=Mock(); repo.listar_publicas.return_value=[]
    assert Catalogo(repo).listar(' ',categoria='',region='')==[]
    repo.listar_publicas.assert_called_once_with(palabra_clave=None,duracion_dias=None,categoria=None,region=None)


def test_privada_e_inexistente_mismo_error():
    repo=Mock(); repo.obtener_publica.return_value=None
    for identificador in (1,2):
        with pytest.raises(RutaNoEncontrada,match='No se encontró la ruta'): Catalogo(repo).detalle(identificador)


@pytest.mark.parametrize('operacion',['listar','detalle'])
@pytest.mark.parametrize('fallo',[RuntimeError('SECRETO'),ErrorMigracionPendiente('SQL SECRETO')])
def test_errores_seguros(operacion,fallo):
    repo=Mock(); repo.listar_publicas.side_effect=fallo; repo.obtener_publica.side_effect=fallo
    with pytest.raises(ErrorCatalogo) as info:
        getattr(Catalogo(repo),operacion)(*([1] if operacion=='detalle' else []))
    assert 'SECRETO' not in str(info.value)
    if isinstance(fallo,ErrorMigracionPendiente): assert 'migración' in str(info.value)


@pytest.mark.parametrize('identificador',[True,0,-1,'1',None])
def test_id_invalido(identificador):
    repo=Mock()
    with pytest.raises(ErrorValidacion): Catalogo(repo).detalle(identificador)
    repo.obtener_publica.assert_not_called()


# ------------------------------------------------ mapa del detalle (v0.5.0)

def lugar(lat, lon):
    return {'id': 'osm:1', 'latitud': lat, 'longitud': lon}


def con_resumen(origen=None, paradas=None, destino=None, **extra):
    ruta = {'origen': 'Lugar A', 'destino': 'Lugar B',
            'origen_lugar': origen if origen is not None else lugar(19.4, -99.1),
            'destino_lugar': destino if destino is not None else lugar(17.0, -96.7),
            'paradas': paradas if paradas is not None else [
                {'nombre': 'Parada 1', 'lugar': lugar(19.0, -98.2)},
                {'nombre': 'Parada 2', 'lugar': lugar(18.0, -97.0)}]}
    ruta.update(extra)
    f = fila()
    f['resumen'] = {'rutamx_v2': {'version': 1, 'ruta': ruta}}
    return f


def detalle_de(f):
    repo = Mock()
    repo.obtener_publica.return_value = f
    return Catalogo(repo).detalle(1)


def test_puntos_del_mapa_van_en_orden_origen_paradas_destino():
    d = detalle_de(con_resumen())
    assert [(p['orden'], p['tipo'], p['nombre']) for p in d['puntos_mapa']] == [
        (1, 'origen', 'Lugar A'), (2, 'parada', 'Parada 1'), (3, 'parada', 'Parada 2'), (4, 'destino', 'Lugar B')]
    assert d['puntos_mapa'][1]['latitud'] == 19.0 and d['puntos_mapa'][1]['longitud'] == -98.2
    assert d['puntos_omitidos'] == 0


def test_ruta_sin_paradas_dibuja_origen_y_destino():
    d = detalle_de(con_resumen(paradas=[]))
    assert [p['tipo'] for p in d['puntos_mapa']] == ['origen', 'destino']


@pytest.mark.parametrize('mala', [
    None, 'texto', {}, {'latitud': 1}, {'latitud': True, 'longitud': 2}, {'latitud': 'x', 'longitud': 2},
    {'latitud': float('nan'), 'longitud': 2}, {'latitud': float('inf'), 'longitud': 2},
    {'latitud': 91, 'longitud': 0}, {'latitud': 0, 'longitud': 181}, {'latitud': -90.1, 'longitud': 0},
])
def test_parada_con_coordenadas_invalidas_se_omite_y_se_cuenta(mala):
    d = detalle_de(con_resumen(paradas=[
        {'nombre': 'Buena', 'lugar': lugar(19.0, -98.2)}, {'nombre': 'Mala', 'lugar': mala}]))
    assert [p['nombre'] for p in d['puntos_mapa']] == ['Lugar A', 'Buena', 'Lugar B']
    assert d['puntos_omitidos'] == 1
    assert [p['orden'] for p in d['puntos_mapa']] == [1, 2, 4]


@pytest.mark.parametrize('parada', [None, 'texto', {}, {'nombre': ''}, {'nombre': 4, 'lugar': lugar(1, 1)},
                                    {'lugar': lugar(1, 1)}])
def test_parada_sin_nombre_o_con_forma_rara_se_omite(parada):
    d = detalle_de(con_resumen(paradas=[parada]))
    assert [p['tipo'] for p in d['puntos_mapa']] == ['origen', 'destino'] and d['puntos_omitidos'] == 1


def test_limites_validos_de_coordenadas_se_aceptan():
    d = detalle_de(con_resumen(origen=lugar(90, 180), destino=lugar(-90, -180), paradas=[]))
    assert len(d['puntos_mapa']) == 2 and d['puntos_omitidos'] == 0


def test_extremo_invalido_tambien_se_omite():
    d = detalle_de(con_resumen(origen={'latitud': 200, 'longitud': 0}))
    assert [p['tipo'] for p in d['puntos_mapa']][0] == 'parada' and d['puntos_omitidos'] == 1


@pytest.mark.parametrize('resumen', [None, {}, [], 'x', {'rutamx_v2': None}, {'rutamx_v2': 'x'},
    {'rutamx_v2': {}}, {'rutamx_v2': {'ruta': None}}, {'rutamx_v2': {'ruta': 'x'}},
    {'rutamx_v2': {'ruta': {'paradas': 'no es lista'}}}, {'rutamx_v2': {'ruta': {}}}])
def test_sin_ruta_estructurada_no_hay_puntos_ni_falla(resumen):
    f = fila()
    f['resumen'] = resumen
    d = detalle_de(f)
    assert d['puntos_mapa'] == [] and d['puntos_omitidos'] == 0


def test_detalle_sin_columna_resumen_no_falla():
    d = detalle_de(fila())
    assert d['puntos_mapa'] == [] and d['puntos_omitidos'] == 0


def test_proyeccion_no_expone_resumen_ni_datos_privados():
    f = con_resumen()
    f['resumen']['secreto'] = 'pin_hash'
    d = detalle_de(f)
    assert 'resumen' not in d and 'usuario_id' not in d and 'pin_hash' not in str(d)
    assert set(d['puntos_mapa'][0]) == {'orden', 'tipo', 'nombre', 'latitud', 'longitud'}
