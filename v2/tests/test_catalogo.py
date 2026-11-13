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
