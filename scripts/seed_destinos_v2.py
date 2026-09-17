"""Segunda carga de destinos: lleva a cada uno de los 32 estados a un
mínimo de 8 destinos, y agrega sitios turísticos clave dentro de
ciudades importantes (zonas arqueológicas, parques naturales, plazas
históricas) además de más ciudades y pueblos mágicos.

Mismo patrón que seed_destinos.py: idempotente, no duplica filas si se
vuelve a correr. Las coordenadas se afinan después corriendo
verify_coordenadas.py (igual que con el primer lote).

Uso:
    python scripts/seed_destinos_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

# (nombre, estado, tipo, lat, lon, descripcion, intereses)
DESTINOS_V2 = [
    # Aguascalientes
    ("Jesús María", "Aguascalientes", "ciudad_principal", 21.9611, -102.3444, "Ciudad conurbada con la capital, importante polo industrial automotriz.", ["cultura"]),
    ("Pabellón de Arteaga", "Aguascalientes", "pueblo_magico", 22.1500, -102.2833, "Pueblo mágico ferroviario, cuna de tradiciones de la Feria de San Marcos.", ["cultura", "naturaleza"]),
    ("Real de Asientos", "Aguascalientes", "pueblo_magico", 22.2394, -102.1044, "Antiguo real minero colonial en el norte del estado.", ["cultura", "naturaleza"]),
    ("San José de Gracia", "Aguascalientes", "pueblo_magico", 22.1667, -102.3500, "Pueblo mágico agrícola y ganadero de Aguascalientes.", ["cultura", "naturaleza"]),
    ("Zona termal de Ojocaliente", "Aguascalientes", "sitio_turistico", 21.8550, -102.2800, "Aguas termales tradicionales dentro de la capital.", ["descanso", "cultura"]),
    ("Jardín de San Marcos", "Aguascalientes", "sitio_turistico", 21.8830, -102.2960, "Jardín histórico sede de la Feria Nacional de San Marcos.", ["cultura"]),

    # Baja California
    ("Rosarito", "Baja California", "ciudad_principal", 32.3667, -117.0500, "Ciudad costera famosa por sus playas y estudios de cine.", ["playas", "descanso"]),
    ("Valle de Guadalupe", "Baja California", "sitio_turistico", 32.0833, -116.5833, "Principal región vitivinícola de México, dentro de Ensenada.", ["comida", "naturaleza"]),
    ("San Felipe", "Baja California", "ciudad_principal", 31.0167, -114.8333, "Pueblo pesquero y de playa sobre el Mar de Cortés.", ["playas", "descanso"]),
    ("La Rumorosa", "Baja California", "sitio_turistico", 32.5333, -116.0667, "Sierra de rocas graníticas famosa por escalada y vistas al desierto.", ["naturaleza"]),

    # Baja California Sur
    ("San José del Cabo", "Baja California Sur", "ciudad_principal", 23.0595, -109.7028, "Centro histórico colonial junto a los resorts de Los Cabos.", ["cultura", "playas"]),
    ("Cabo Pulmo", "Baja California Sur", "sitio_turistico", 23.4394, -109.8969, "Arrecife de coral protegido, Patrimonio Natural de la Humanidad.", ["naturaleza", "playas"]),
    ("Isla Espíritu Santo", "Baja California Sur", "sitio_turistico", 24.4667, -110.3667, "Isla protegida frente a La Paz, snorkel con lobos marinos.", ["naturaleza"]),
    ("Mulegé", "Baja California Sur", "ciudad_principal", 26.8833, -111.9833, "Oasis y misión histórica en la costa del Golfo de California.", ["naturaleza", "cultura"]),

    # Campeche
    ("Calakmul", "Campeche", "sitio_turistico", 18.1050, -89.8100, "Zona arqueológica maya dentro de la Reserva de la Biosfera de Calakmul.", ["cultura", "naturaleza"]),
    ("Edzná", "Campeche", "sitio_turistico", 19.5900, -90.2233, "Zona arqueológica maya cercana a la capital.", ["cultura"]),
    ("Champotón", "Campeche", "ciudad_principal", 19.3500, -90.7167, "Ciudad costera pesquera del Golfo de México.", ["playas", "cultura"]),
    ("Hopelchén", "Campeche", "ciudad_principal", 19.7500, -89.8500, "Cabecera agrícola y menonita en el sur de Campeche.", ["naturaleza", "cultura"]),
    ("Isla Aguada", "Campeche", "pueblo_magico", 18.7833, -91.4833, "Pueblo mágico pesquero en la Laguna de Términos.", ["playas", "naturaleza"]),

    # Chiapas
    ("Cañón del Sumidero", "Chiapas", "sitio_turistico", 16.8500, -93.0833, "Cañón de mil metros de profundidad, navegable en lancha desde Chiapa de Corzo.", ["naturaleza"]),
    ("Lagunas de Montebello", "Chiapas", "sitio_turistico", 16.1167, -91.6833, "Parque nacional de lagos multicolores cerca de Comitán.", ["naturaleza"]),

    # Chihuahua
    ("Cuauhtémoc", "Chihuahua", "ciudad_principal", 28.4050, -106.8664, "Ciudad menonita, centro agrícola y manzanero del estado.", ["comida", "cultura"]),
    ("Hidalgo del Parral", "Chihuahua", "ciudad_principal", 26.9333, -105.6667, "Ciudad minera histórica, lugar del asesinato de Pancho Villa.", ["cultura"]),
    ("Paquimé", "Chihuahua", "sitio_turistico", 30.3667, -107.9500, "Zona arqueológica de Casas Grandes, Patrimonio de la Humanidad.", ["cultura"]),
    ("Divisadero", "Chihuahua", "sitio_turistico", 27.5333, -107.8333, "Mirador icónico sobre las Barrancas del Cobre y el Teleférico.", ["naturaleza"]),

    # Ciudad de México
    ("Bosque de Chapultepec", "Ciudad de México", "sitio_turistico", 19.4204, -99.1813, "El parque urbano más grande de Latinoamérica, con castillo y museos.", ["naturaleza", "cultura"]),
    ("Basílica de Guadalupe", "Ciudad de México", "sitio_turistico", 19.4833, -99.1178, "El santuario católico más visitado de México.", ["cultura"]),
    ("San Ángel", "Ciudad de México", "sitio_turistico", 19.3467, -99.1900, "Barrio colonial famoso por el Bazar Sábado y sus calles empedradas.", ["cultura", "comida"]),
    ("Polanco", "Ciudad de México", "sitio_turistico", 19.4326, -99.1965, "Zona de alta gastronomía, arte y compras de la ciudad.", ["comida", "cultura"]),

    # Coahuila
    ("Piedras Negras", "Coahuila", "ciudad_principal", 28.6994, -100.5231, "Ciudad fronteriza, cuna del nacho.", ["comida", "cultura"]),
    ("Monclova", "Coahuila", "ciudad_principal", 26.9078, -101.4211, "Capital siderúrgica de México.", ["cultura"]),
    ("Arteaga", "Coahuila", "pueblo_magico", 25.4500, -100.8500, "Pueblo mágico de montaña, tierra de manzanas de Coahuila.", ["naturaleza", "comida"]),
    ("Melchor Múzquiz", "Coahuila", "pueblo_magico", 27.8833, -101.5167, "Pueblo mágico minero, con la comunidad kikapú cercana.", ["cultura", "naturaleza"]),

    # Colima
    ("Villa de Álvarez", "Colima", "ciudad_principal", 19.2547, -103.7317, "Ciudad conurbada con la capital, sede del Carnaval de Colima.", ["cultura"]),
    ("Volcán de Fuego de Colima", "Colima", "sitio_turistico", 19.5117, -103.6200, "Uno de los volcanes más activos de México.", ["naturaleza"]),
    ("Cuyutlán", "Colima", "pueblo_magico", 18.9167, -104.0667, "Pueblo de playa famoso por la Ola Verde.", ["playas", "naturaleza"]),
    ("Tecomán", "Colima", "ciudad_principal", 18.9089, -103.8756, "Capital mundial del limón mexicano.", ["comida"]),
    ("Laguna de Alcuzahue", "Colima", "sitio_turistico", 19.0333, -103.9667, "Humedal costero para observación de aves en Colima.", ["naturaleza"]),

    # Durango
    ("Gómez Palacio", "Durango", "ciudad_principal", 25.5667, -103.4972, "Ciudad industrial de La Laguna, junto a Torreón.", ["cultura", "comida"]),
    ("Nombre de Dios", "Durango", "pueblo_magico", 23.8500, -104.2500, "Pueblo mágico colonial del sur de Durango.", ["cultura"]),
    ("Zona del Silencio", "Durango", "sitio_turistico", 26.4667, -103.8667, "Zona desértica del Bolsón de Mapimí, famosa por fenómenos inexplicados.", ["naturaleza"]),
    ("Mexiquillo", "Durango", "sitio_turistico", 23.7833, -105.5000, "Parque natural de cascadas y bosques en la Sierra Madre Occidental.", ["naturaleza"]),
    ("Villa del Oeste (Chupaderos)", "Durango", "sitio_turistico", 24.1167, -104.5667, "Pueblos usados como set de películas del viejo oeste.", ["cultura"]),
    ("El Salto", "Durango", "ciudad_principal", 23.7833, -105.3667, "Comunidad maderera en la Sierra Madre Occidental duranguense.", ["naturaleza", "cultura"]),

    # Guanajuato (ya tenía 9, se agrega 1 sitio turístico)
    ("Minas de Valenciana", "Guanajuato", "sitio_turistico", 21.0464, -101.2419, "Antigua mina de plata y templo barroco, símbolo de la riqueza colonial de Guanajuato.", ["cultura"]),

    # Guerrero
    ("Pie de la Cuesta", "Guerrero", "sitio_turistico", 16.8833, -99.9500, "Playa de atardeceres famosos junto a la Laguna de Coyuca, cerca de Acapulco.", ["playas", "naturaleza"]),
    ("Grutas de Cacahuamilpa", "Guerrero", "sitio_turistico", 18.6667, -99.5000, "Uno de los sistemas de cavernas más grandes de América.", ["naturaleza"]),
    ("Chilapa de Álvarez", "Guerrero", "ciudad_principal", 17.5981, -99.1758, "Ciudad de tradición artesanal, famosa por su Feria del Mole.", ["cultura", "comida"]),
    ("Barra de Potosí", "Guerrero", "sitio_turistico", 17.5333, -101.4167, "Playa y laguna pesquera cerca de Zihuatanejo.", ["playas", "naturaleza"]),

    # Hidalgo
    ("Tula (zona arqueológica)", "Hidalgo", "sitio_turistico", 20.0500, -99.3333, "Zona arqueológica tolteca, hogar de los Atlantes de Tula.", ["cultura"]),
    ("Grutas de Tolantongo", "Hidalgo", "sitio_turistico", 20.8500, -99.2833, "Cascadas y pozas termales entre montañas.", ["naturaleza", "descanso"]),
    ("Huichapan", "Hidalgo", "pueblo_magico", 20.3833, -99.6500, "Pueblo mágico colonial del Valle del Mezquital.", ["cultura"]),
    ("Zimapán", "Hidalgo", "pueblo_magico", 20.7333, -99.3833, "Pueblo mágico minero conocido por su barbacoa y gastronomía.", ["comida", "cultura"]),

    # Jalisco (ya tenía 9, se agrega 1 sitio turístico)
    ("Barranca de Huentitán", "Jalisco", "sitio_turistico", 20.7333, -103.2833, "Cañón y mirador natural a las afueras de Guadalajara.", ["naturaleza"]),

    # México (Estado de México)
    ("Teotihuacán", "México", "sitio_turistico", 19.6925, -98.8438, "Zona arqueológica de las pirámides del Sol y la Luna, Patrimonio de la Humanidad.", ["cultura"]),
    ("Nevado de Toluca", "México", "sitio_turistico", 19.1083, -99.7583, "Volcán con cráter y lagunas, uno de los picos más altos de México.", ["naturaleza"]),
    ("El Oro", "México", "pueblo_magico", 19.8000, -100.1333, "Pueblo mágico minero de arquitectura porfiriana.", ["cultura"]),
    ("Metepec", "México", "sitio_turistico", 19.2500, -99.6000, "Ciudad artesanal famosa por sus árboles de la vida de barro.", ["cultura", "comida"]),

    # Michoacán
    ("Santuario El Rosario (Mariposa Monarca)", "Michoacán", "sitio_turistico", 19.5833, -100.2500, "Santuario donde hibernan millones de mariposas monarca cada invierno.", ["naturaleza"]),
    ("Santa Clara del Cobre", "Michoacán", "pueblo_magico", 19.3833, -101.6500, "Pueblo mágico famoso por su artesanía en cobre martillado.", ["cultura"]),
    ("Janitzio", "Michoacán", "sitio_turistico", 19.5667, -101.6333, "Isla en el lago de Pátzcuaro, centro de las celebraciones de Día de Muertos.", ["cultura", "naturaleza"]),

    # Morelos
    ("Cuautla", "Morelos", "ciudad_principal", 18.8111, -98.9536, "Ciudad histórica de aguas termales y sitio zapatista.", ["descanso", "cultura"]),
    ("Xochicalco", "Morelos", "sitio_turistico", 18.7972, -99.2969, "Zona arqueológica prehispánica, Patrimonio de la Humanidad.", ["cultura"]),
    ("Las Estacas", "Morelos", "sitio_turistico", 18.6167, -99.0833, "Río de aguas cristalinas para nado y buceo en manantiales.", ["naturaleza", "descanso"]),
    ("Jonacatepec", "Morelos", "pueblo_magico", 18.6167, -98.7833, "Pueblo mágico con haciendas azucareras históricas.", ["cultura"]),
    ("Oaxtepec", "Morelos", "sitio_turistico", 18.8833, -98.9667, "Antiguo balneario prehispánico, hoy parque acuático y ecoturístico.", ["descanso", "naturaleza"]),

    # Nayarit
    ("Nuevo Vallarta", "Nayarit", "ciudad_principal", 20.7333, -105.3000, "Zona turística de playas junto a Puerto Vallarta.", ["playas", "descanso"]),
    ("Islas Marietas", "Nayarit", "sitio_turistico", 20.7000, -105.5833, "Islas protegidas famosas por la Playa Escondida.", ["naturaleza", "playas"]),
    ("Mexcaltitán", "Nayarit", "sitio_turistico", 21.9000, -105.4333, "Isla lacustre llamada la 'Venecia mexicana', posible cuna de los aztecas.", ["cultura", "naturaleza"]),
    ("Compostela", "Nayarit", "ciudad_principal", 21.2333, -104.9000, "Ciudad histórica del sur de Nayarit, cercana a la costa.", ["cultura", "naturaleza"]),

    # Nuevo León
    ("San Pedro Garza García", "Nuevo León", "ciudad_principal", 25.6600, -100.4025, "Municipio de alto nivel de vida del área metropolitana de Monterrey.", ["comida", "cultura"]),
    ("Cumbres de Monterrey", "Nuevo León", "sitio_turistico", 25.5000, -100.3000, "Área natural protegida con cascadas y senderismo cerca de la ciudad.", ["naturaleza"]),
    ("Grutas de García", "Nuevo León", "sitio_turistico", 25.8167, -100.5333, "Sistema de cuevas accesible por teleférico cerca de Monterrey.", ["naturaleza"]),
    ("Parque Fundidora", "Nuevo León", "sitio_turistico", 25.6789, -100.2844, "Antigua fundidora reconvertida en parque cultural y recreativo.", ["cultura"]),
    ("Cola de Caballo", "Nuevo León", "sitio_turistico", 25.3333, -100.1667, "Cascada emblemática en el Parque Nacional Cumbres de Monterrey.", ["naturaleza"]),
    ("Linares", "Nuevo León", "ciudad_principal", 24.8578, -99.5672, "Ciudad citrícola y de tradición dulce (glorias) al sur de Nuevo León.", ["comida", "cultura"]),

    # Oaxaca
    ("Hierve el Agua", "Oaxaca", "sitio_turistico", 16.8667, -96.2750, "Cascadas petrificadas de aguas minerales en la Sierra de Oaxaca.", ["naturaleza"]),
    ("Mitla", "Oaxaca", "sitio_turistico", 16.9231, -96.3583, "Zona arqueológica zapoteca famosa por sus mosaicos de piedra.", ["cultura"]),
    ("Monte Albán", "Oaxaca", "sitio_turistico", 17.0431, -96.7675, "Zona arqueológica zapoteca, Patrimonio de la Humanidad.", ["cultura"]),
    ("Mazunte", "Oaxaca", "pueblo_magico", 15.6667, -96.5500, "Pueblo de playa ecológico famoso por el Santuario de la Tortuga.", ["playas", "naturaleza"]),
    ("Teotitlán del Valle", "Oaxaca", "sitio_turistico", 17.0333, -96.5167, "Pueblo zapoteco famoso por sus tapetes de lana tejidos a mano.", ["cultura", "comida"]),

    # Puebla
    ("Cholula", "Puebla", "sitio_turistico", 19.0578, -98.3025, "Hogar de la pirámide más grande del mundo por volumen.", ["cultura"]),
    ("Africam Safari", "Puebla", "sitio_turistico", 18.9833, -98.1333, "Parque de vida silvestre en libertad cerca de Puebla.", ["naturaleza"]),
    ("Izúcar de Matamoros", "Puebla", "ciudad_principal", 18.6000, -98.4667, "Ciudad histórica del sur poblano, famosa por su mole y alfarería.", ["cultura", "comida"]),
    ("Xicotepec", "Puebla", "pueblo_magico", 20.2833, -97.9500, "Pueblo mágico de la sierra norte poblana.", ["naturaleza", "cultura"]),

    # Querétaro
    ("San Juan del Río", "Querétaro", "ciudad_principal", 20.3900, -99.9967, "Ciudad histórica, importante centro comercial e industrial.", ["cultura", "comida"]),
    ("Sierra Gorda", "Querétaro", "sitio_turistico", 21.2000, -99.4667, "Reserva de la biosfera con misiones franciscanas, Patrimonio de la Humanidad.", ["naturaleza", "cultura"]),
    ("Cadereyta de Montes", "Querétaro", "pueblo_magico", 20.6944, -99.8189, "Pueblo mágico semidesértico famoso por su jardín botánico de cactáceas.", ["naturaleza"]),
    ("Amealco de Bonfil", "Querétaro", "pueblo_magico", 20.1833, -100.1500, "Pueblo mágico cuna de las muñecas artesanales Lele.", ["cultura"]),
    ("Jalpan de Serra", "Querétaro", "sitio_turistico", 21.2167, -99.4833, "Sede de la misión franciscana principal de la Sierra Gorda.", ["cultura"]),

    # Quintana Roo
    ("Cozumel", "Quintana Roo", "sitio_turistico", 20.5083, -86.9458, "Isla caribeña, uno de los mejores sitios de buceo del mundo.", ["playas", "naturaleza"]),
    ("Kohunlich", "Quintana Roo", "sitio_turistico", 18.4083, -88.7667, "Zona arqueológica maya famosa por sus máscaras de estuco gigantes.", ["cultura"]),

    # San Luis Potosí
    ("Ciudad Valles", "San Luis Potosí", "ciudad_principal", 21.9833, -99.0167, "Puerta a la Huasteca Potosina, región de cascadas y ríos turquesa.", ["naturaleza"]),
    ("Cascada de Tamul", "San Luis Potosí", "sitio_turistico", 21.8333, -99.0000, "Una de las cascadas más espectaculares de la Huasteca Potosina.", ["naturaleza"]),
    ("Laguna de la Media Luna", "San Luis Potosí", "sitio_turistico", 21.8167, -99.1667, "Manantial de aguas turquesas para buceo y nado.", ["naturaleza", "descanso"]),
    ("Aquismón", "San Luis Potosí", "pueblo_magico", 21.6167, -99.1667, "Pueblo huasteco cerca del Sótano de las Golondrinas.", ["naturaleza", "cultura"]),
    ("Sótano de las Golondrinas", "San Luis Potosí", "sitio_turistico", 21.5500, -99.1000, "Uno de los abismos más profundos del mundo, refugio de miles de aves.", ["naturaleza"]),

    # Sinaloa
    ("Centro Histórico de Mazatlán", "Sinaloa", "sitio_turistico", 23.2004, -106.4189, "Zona colonial y malecón, sede del Carnaval de Mazatlán.", ["cultura"]),
    ("Copala", "Sinaloa", "sitio_turistico", 23.3500, -106.0833, "Pueblo minero colonial en la sierra sinaloense.", ["cultura"]),
    ("Isla de la Piedra", "Sinaloa", "sitio_turistico", 23.1833, -106.4167, "Playa e isla frente a Mazatlán, accesible en panga.", ["playas", "descanso"]),

    # Sonora
    ("Nogales", "Sonora", "ciudad_principal", 31.3167, -110.9500, "Ciudad fronteriza comercial del norte de Sonora.", ["cultura", "comida"]),
    ("Bahía de Kino", "Sonora", "sitio_turistico", 28.8256, -111.9414, "Playa del Mar de Cortés y cultura seri.", ["playas", "naturaleza"]),
    ("San Carlos", "Sonora", "sitio_turistico", 27.9667, -111.0667, "Bahía y cerro Tetakawi, destino de playa y buceo.", ["playas", "naturaleza"]),
    ("Magdalena de Kino", "Sonora", "pueblo_magico", 30.6333, -110.9500, "Pueblo mágico, tumba del misionero Eusebio Kino.", ["cultura"]),

    # Tabasco
    ("Comalcalco (zona arqueológica)", "Tabasco", "sitio_turistico", 18.2667, -93.2167, "Única zona arqueológica maya construida con ladrillos de barro cocido.", ["cultura"]),
    ("Parque-Museo La Venta", "Tabasco", "sitio_turistico", 17.9917, -92.9389, "Museo al aire libre con las Cabezas Olmecas originales.", ["cultura"]),
    ("Cascadas de Agua Blanca", "Tabasco", "sitio_turistico", 17.4000, -91.9667, "Río de pozas color turquesa en la selva tabasqueña.", ["naturaleza"]),
    ("Pantanos de Centla", "Tabasco", "sitio_turistico", 18.3667, -92.6167, "El humedal más grande de Norteamérica.", ["naturaleza"]),
    ("Comalcalco", "Tabasco", "ciudad_principal", 18.2647, -93.2222, "Capital cacaotera de México.", ["comida", "cultura"]),
    ("Paraíso", "Tabasco", "ciudad_principal", 18.3958, -93.2144, "Puerto y playas del Golfo de México en Tabasco.", ["playas"]),

    # Tamaulipas
    ("Nuevo Laredo", "Tamaulipas", "ciudad_principal", 27.4764, -99.5164, "La mayor frontera terrestre comercial de México.", ["comida", "cultura"]),
    ("Matamoros", "Tamaulipas", "ciudad_principal", 25.8797, -97.5044, "Ciudad histórica fronteriza sobre el Río Bravo.", ["cultura", "comida"]),
    ("Reserva de la Biosfera El Cielo", "Tamaulipas", "sitio_turistico", 23.1667, -99.1500, "Bosque de niebla, una de las reservas más biodiversas de México.", ["naturaleza"]),
    ("Playa Miramar", "Tamaulipas", "sitio_turistico", 22.3167, -97.8167, "Una de las playas más largas del Golfo de México.", ["playas", "descanso"]),

    # Tlaxcala
    ("Cacaxtla", "Tlaxcala", "sitio_turistico", 19.2333, -98.3333, "Zona arqueológica famosa por sus murales prehispánicos a color.", ["cultura"]),
    ("La Malinche", "Tlaxcala", "sitio_turistico", 19.2325, -98.0294, "Volcán y parque nacional entre Tlaxcala y Puebla.", ["naturaleza"]),
    ("Tlaxco", "Tlaxcala", "pueblo_magico", 19.6167, -98.1000, "Pueblo mágico ganadero, tierra de charros y toros bravos.", ["naturaleza", "cultura"]),
    ("Xicohtzinco", "Tlaxcala", "sitio_turistico", 19.2833, -98.2500, "Pueblo con tradición en la elaboración de globos aerostáticos.", ["cultura"]),
    ("Apizaco", "Tlaxcala", "ciudad_principal", 19.4128, -98.1461, "Importante nudo ferroviario histórico de Tlaxcala.", ["cultura", "naturaleza"]),
    ("Santuario de Ocotlán", "Tlaxcala", "sitio_turistico", 19.3225, -98.2306, "Basílica barroca, uno de los templos más importantes de México.", ["cultura"]),

    # Veracruz
    ("El Tajín", "Veracruz", "sitio_turistico", 20.4494, -97.3739, "Zona arqueológica totonaca, Patrimonio de la Humanidad, cerca de Papantla.", ["cultura"]),

    # Yucatán
    ("Uxmal", "Yucatán", "sitio_turistico", 20.3597, -89.7692, "Zona arqueológica maya, Patrimonio de la Humanidad, estilo Puuc.", ["cultura"]),
    ("Celestún", "Yucatán", "sitio_turistico", 20.8667, -90.4000, "Reserva de biosfera famosa por sus flamencos rosados.", ["naturaleza"]),
    ("Río Lagartos", "Yucatán", "sitio_turistico", 21.5964, -88.1592, "Reserva costera de flamencos y manglares.", ["naturaleza"]),
    ("Progreso", "Yucatán", "ciudad_principal", 21.2833, -89.6667, "Puerto y playa más cercana a Mérida.", ["playas", "descanso"]),

    # Zacatecas
    ("Guadalupe", "Zacatecas", "ciudad_principal", 22.7500, -102.5167, "Ciudad conurbada con la capital, sede del Ex-Convento franciscano.", ["cultura"]),
    ("La Quemada", "Zacatecas", "sitio_turistico", 22.3667, -102.7167, "Zona arqueológica prehispánica en la meseta zacatecana.", ["cultura"]),
    ("Fresnillo", "Zacatecas", "ciudad_principal", 23.1833, -102.8667, "Uno de los mayores productores de plata del mundo.", ["cultura", "comida"]),
    ("Pinos", "Zacatecas", "pueblo_magico", 22.3000, -101.5833, "Pueblo mágico minero colonial del altiplano zacatecano.", ["cultura"]),
    ("Teúl de González Ortega", "Zacatecas", "pueblo_magico", 21.4667, -103.4667, "Pequeño pueblo mágico entre montañas boscosas.", ["naturaleza", "cultura"]),

    # --- Segunda tanda: cerrar huecos para que cada estado tenga mínimo 8
    # ciudades/pueblos mágicos Y mínimo 3 sitios turísticos por separado
    # (la primera tanda mezclaba ambos conteos). Ciudad de México es la
    # excepción: es una sola ciudad, no tiene "8 ciudades" que agregar, así
    # que ahí se compensa con más sitios turísticos en vez de forzar
    # ciudades que no existen.

    ("Rincón de Romos", "Aguascalientes", "ciudad_principal", 22.2333, -102.3167, "Ciudad vitivinícola y agrícola cerca de la capital.", ["comida", "cultura"]),
    ("Tepezalá", "Aguascalientes", "ciudad_principal", 22.2833, -102.1667, "Antiguo pueblo minero histórico de Aguascalientes.", ["cultura", "naturaleza"]),

    ("San Quintín", "Baja California", "ciudad_principal", 30.5667, -115.9500, "Bahía agrícola y pesquera en la costa del Pacífico.", ["naturaleza", "playas"]),
    ("Guerrero Negro", "Baja California", "ciudad_principal", 27.9769, -114.0611, "Puerta a la laguna de avistamiento de ballenas grises.", ["naturaleza"]),

    ("Ciudad Constitución", "Baja California Sur", "ciudad_principal", 25.0167, -111.6667, "Capital agrícola del municipio de Comondú.", ["cultura"]),
    ("Santa Rosalía", "Baja California Sur", "pueblo_magico", 27.3333, -112.2833, "Pueblo mágico minero de arquitectura francesa junto al Golfo de California.", ["cultura", "naturaleza"]),

    ("Calkiní", "Campeche", "ciudad_principal", 20.3667, -90.0500, "Ciudad maya agrícola en la zona henequenera de Campeche.", ["cultura"]),
    ("Candelaria", "Campeche", "pueblo_magico", 18.1833, -91.0167, "Pueblo mágico ribereño en la selva de Campeche.", ["naturaleza", "cultura"]),

    ("Ocozocoautla de Espinosa", "Chiapas", "pueblo_magico", 16.7833, -93.3667, "Pueblo mágico de tradiciones y fiestas de parachicos.", ["cultura", "naturaleza"]),
    ("Copainalá", "Chiapas", "pueblo_magico", 17.0833, -93.1833, "Pueblo mágico zoque a orillas del Cañón del Sumidero.", ["cultura", "naturaleza"]),

    ("Guachochi", "Chihuahua", "pueblo_magico", 26.8167, -107.0667, "Pueblo mágico en la Sierra Tarahumara, junto a la Barranca de Sinforosa.", ["naturaleza", "cultura"]),
    ("Delicias", "Chihuahua", "ciudad_principal", 28.1833, -105.4667, "Ciudad agrícola del Valle de Delicias.", ["comida", "cultura"]),

    ("Templo Mayor", "Ciudad de México", "sitio_turistico", 19.4344, -99.1332, "Ruinas del principal templo mexica, en pleno Centro Histórico.", ["cultura"]),
    ("Museo Nacional de Antropología", "Ciudad de México", "sitio_turistico", 19.4260, -99.1861, "El museo más importante de culturas prehispánicas de México.", ["cultura"]),
    ("Ángel de la Independencia", "Ciudad de México", "sitio_turistico", 19.4270, -99.1677, "Monumento icónico sobre el Paseo de la Reforma.", ["cultura"]),

    ("Ciudad Acuña", "Coahuila", "ciudad_principal", 29.3238, -100.9330, "Ciudad fronteriza frente a Del Río, Texas.", ["cultura"]),
    ("Sabinas", "Coahuila", "ciudad_principal", 27.8500, -101.1167, "Ciudad carbonífera del norte de Coahuila.", ["cultura"]),
    ("Candela", "Coahuila", "pueblo_magico", 26.8333, -100.9500, "Pueblo mágico de misiones franciscanas y aguas termales.", ["cultura", "naturaleza"]),
    ("General Cepeda", "Coahuila", "pueblo_magico", 25.3833, -101.4667, "Pueblo mágico al pie de la Sierra de Parras.", ["cultura", "naturaleza"]),
    ("Museo del Desierto", "Coahuila", "sitio_turistico", 25.4667, -100.9833, "Museo de paleontología y ecología del desierto, en Saltillo.", ["cultura"]),
    ("Presa de la Amistad", "Coahuila", "sitio_turistico", 29.4667, -101.0667, "Embalse binacional para pesca y deportes acuáticos.", ["naturaleza"]),
    ("Bosque Venustiano Carranza", "Coahuila", "sitio_turistico", 25.4200, -100.9700, "Parque urbano principal de Saltillo.", ["naturaleza"]),

    ("Coquimatlán", "Colima", "ciudad_principal", 19.2333, -103.8000, "Ciudad agrícola cercana a la capital de Colima.", ["cultura"]),
    ("Quesería", "Colima", "ciudad_principal", 19.2833, -103.7167, "Comunidad azucarera del Valle de Colima.", ["comida"]),

    ("Canatlán", "Durango", "ciudad_principal", 24.5167, -104.7833, "Región agrícola conocida por su manzana y durazno.", ["naturaleza", "comida"]),
    ("Pueblo Nuevo", "Durango", "ciudad_principal", 23.3833, -105.3833, "Municipio forestal en la Sierra Madre Occidental.", ["naturaleza"]),
    ("Vicente Guerrero", "Durango", "ciudad_principal", 23.7333, -103.9667, "Región nuecera y agrícola del centro de Durango.", ["comida"]),
    ("Santiago Papasquiaro", "Durango", "ciudad_principal", 25.0500, -105.4167, "Puerta a la sierra duranguense y sus bosques.", ["naturaleza", "cultura"]),

    ("Salvatierra", "Guanajuato", "pueblo_magico", 20.2167, -100.8833, "Pueblo mágico colonial a orillas del río Lerma.", ["cultura", "naturaleza"]),

    ("Iguala", "Guerrero", "ciudad_principal", 18.3444, -99.5392, "Cuna de la bandera nacional mexicana.", ["cultura"]),
    ("Ixcateopan de Cuauhtémoc", "Guerrero", "pueblo_magico", 18.5167, -99.7833, "Pueblo mágico donde se resguardan los restos del último tlatoani.", ["cultura"]),
    ("Coyuca de Benítez", "Guerrero", "ciudad_principal", 16.9833, -99.9333, "Ciudad agrícola cerca de la Laguna de Coyuca.", ["naturaleza"]),
    ("Petatlán", "Guerrero", "ciudad_principal", 17.5167, -101.2667, "Ciudad costera de peregrinaje religioso y playas.", ["playas", "cultura"]),

    ("Metztitlán", "Hidalgo", "pueblo_magico", 20.5833, -98.7667, "Pueblo mágico en un valle desértico con un exconvento agustino.", ["naturaleza", "cultura"]),
    ("Tulancingo", "Hidalgo", "ciudad_principal", 20.0833, -98.3667, "Ciudad histórica de la región Valle-Sierra de Hidalgo.", ["cultura"]),

    ("Ixtapan de la Sal", "México", "pueblo_magico", 18.8167, -99.6667, "Pueblo mágico famoso por sus balnearios de aguas termales.", ["descanso", "cultura"]),
    ("Aculco", "México", "pueblo_magico", 20.0833, -99.8333, "Pueblo mágico ganadero con cascadas cercanas.", ["naturaleza", "cultura"]),
    ("Atlacomulco", "México", "ciudad_principal", 19.7986, -99.8742, "Ciudad histórica del norte del Estado de México.", ["cultura"]),

    ("Zamora de Hidalgo", "Michoacán", "ciudad_principal", 19.9853, -102.2833, "Ciudad conocida por su producción de fresa.", ["comida"]),
    ("Tzintzuntzan", "Michoacán", "pueblo_magico", 19.6167, -101.5833, "Pueblo mágico, antigua capital del imperio purépecha.", ["cultura"]),

    ("Jiutepec", "Morelos", "ciudad_principal", 18.8794, -99.1789, "Ciudad industrial del área metropolitana de Cuernavaca.", ["cultura"]),
    ("Tlaltizapán", "Morelos", "pueblo_magico", 18.6833, -99.1333, "Pueblo mágico histórico, cuartel general de Emiliano Zapata.", ["cultura"]),
    ("Yautepec", "Morelos", "ciudad_principal", 18.8781, -99.0636, "Ciudad de huertos y manantiales en Morelos.", ["naturaleza"]),
    ("Zacatepec", "Morelos", "ciudad_principal", 18.6500, -99.2000, "Ciudad azucarera del sur de Morelos.", ["cultura"]),

    ("Ixtlán del Río", "Nayarit", "ciudad_principal", 21.0333, -104.3667, "Ciudad con ruinas prehispánicas toltecas cercanas.", ["cultura"]),
    ("Xalisco", "Nayarit", "ciudad_principal", 21.4667, -104.9000, "Municipio agrícola conurbado con Tepic.", ["cultura"]),

    ("Montemorelos", "Nuevo León", "ciudad_principal", 25.1878, -99.8267, "Región citrícola conocida como la 'Ciudad de las Naranjas'.", ["comida"]),
    ("Galeana", "Nuevo León", "ciudad_principal", 24.8333, -100.0667, "Puerta a la Sierra Madre Oriental neoleonesa.", ["naturaleza"]),
    ("Doctor Arroyo", "Nuevo León", "ciudad_principal", 23.6667, -100.1833, "Municipio semidesértico del altiplano de Nuevo León.", ["naturaleza"]),
    ("General Terán", "Nuevo León", "ciudad_principal", 25.2667, -99.6167, "Pueblo agrícola del centro de Nuevo León.", ["cultura"]),

    ("Tlacolula de Matamoros", "Oaxaca", "ciudad_principal", 16.9500, -96.4833, "Sede del famoso mercado dominical y región mezcalera.", ["comida", "cultura"]),
    ("Ocotlán de Morelos", "Oaxaca", "ciudad_principal", 16.7944, -96.6708, "Ciudad de artesanos y mercados tradicionales del Valle de Oaxaca.", ["cultura"]),
    ("Juchitán de Zaragoza", "Oaxaca", "ciudad_principal", 16.4333, -95.0167, "Ciudad zapoteca del Istmo de Tehuantepec.", ["cultura"]),
    ("Pinotepa Nacional", "Oaxaca", "ciudad_principal", 16.3406, -98.0522, "Ciudad de la Costa Chica oaxaqueña.", ["cultura"]),

    ("Tehuacán", "Puebla", "ciudad_principal", 18.4636, -97.3928, "Ciudad famosa por sus aguas minerales embotelladas.", ["comida"]),
    ("Atlixco", "Puebla", "pueblo_magico", 18.9083, -98.4361, "Pueblo mágico florero, famoso por su festival de globos.", ["cultura", "naturaleza"]),

    ("Corregidora", "Querétaro", "ciudad_principal", 20.5236, -100.4383, "Municipio industrial del área metropolitana de Querétaro.", ["cultura"]),
    ("Landa de Matamoros", "Querétaro", "ciudad_principal", 21.1833, -99.3333, "Puerta a las misiones franciscanas de la Sierra Gorda.", ["naturaleza", "cultura"]),
    ("Pinal de Amoles", "Querétaro", "ciudad_principal", 21.1333, -99.6167, "Pueblo de montaña en la Sierra Gorda queretana.", ["naturaleza"]),

    ("Felipe Carrillo Puerto", "Quintana Roo", "ciudad_principal", 19.5794, -88.0431, "Ciudad histórica maya, capital de la rebelión de Castas.", ["cultura"]),
    ("Mahahual", "Quintana Roo", "ciudad_principal", 18.7167, -87.7000, "Pueblo de playa y arrecife en la Costa Maya.", ["playas", "descanso"]),

    ("Matehuala", "San Luis Potosí", "ciudad_principal", 23.6539, -100.6419, "Puerta de entrada a Real de Catorce.", ["cultura"]),
    ("Río Verde", "San Luis Potosí", "ciudad_principal", 21.9333, -99.9833, "Ciudad de manantiales en la Media Luna potosina.", ["naturaleza"]),
    ("Tamazunchale", "San Luis Potosí", "ciudad_principal", 21.2667, -98.7833, "Ciudad de la Huasteca Potosina, entre ríos y montañas.", ["naturaleza"]),
    ("Tancanhuitz", "San Luis Potosí", "pueblo_magico", 21.6167, -98.7500, "Pueblo mágico huasteco entre cascadas y ríos.", ["cultura", "naturaleza"]),

    ("Guasave", "Sinaloa", "ciudad_principal", 25.5667, -108.4667, "Ciudad agrícola del norte de Sinaloa.", ["comida"]),
    ("Guamúchil", "Sinaloa", "ciudad_principal", 25.4667, -108.0833, "Ciudad comercial del Valle de Évora.", ["cultura"]),
    ("Escuinapa", "Sinaloa", "ciudad_principal", 22.8333, -105.7667, "Capital mundial del mango, al sur de Sinaloa.", ["comida"]),

    ("Navojoa", "Sonora", "ciudad_principal", 27.0833, -109.4500, "Ciudad agrícola del sur de Sonora, cerca del río Mayo.", ["cultura"]),
    ("Agua Prieta", "Sonora", "ciudad_principal", 31.3167, -109.5667, "Ciudad fronteriza del noreste de Sonora.", ["cultura"]),
    ("Caborca", "Sonora", "ciudad_principal", 30.7167, -112.1500, "Región agrícola conocida por su producción de uva y aceituna.", ["comida"]),

    ("Cunduacán", "Tabasco", "ciudad_principal", 18.0667, -93.1667, "Municipio petrolero y agrícola del centro de Tabasco.", ["cultura"]),
    ("Macuspana", "Tabasco", "ciudad_principal", 17.7667, -92.6000, "Municipio ganadero junto al río Tulijá.", ["naturaleza"]),
    ("Teapa", "Tabasco", "ciudad_principal", 17.5500, -92.9500, "Ciudad de aguas termales al pie de la sierra tabasqueña.", ["descanso", "naturaleza"]),
    ("Jalpa de Méndez", "Tabasco", "ciudad_principal", 18.1833, -93.0667, "Municipio cacaotero del centro de Tabasco.", ["comida"]),

    ("Ciudad Mante", "Tamaulipas", "ciudad_principal", 22.7333, -98.9667, "Ciudad cañera del sur de Tamaulipas.", ["comida"]),
    ("Soto la Marina", "Tamaulipas", "ciudad_principal", 23.7667, -98.2167, "Municipio ganadero y pesquero costero de Tamaulipas.", ["naturaleza"]),

    ("Calpulalpan", "Tlaxcala", "ciudad_principal", 19.5833, -98.5667, "Ciudad industrial del poniente de Tlaxcala.", ["cultura"]),
    ("Chiautempan", "Tlaxcala", "ciudad_principal", 19.3167, -98.1833, "Ciudad textilera tradicional de Tlaxcala.", ["cultura"]),
    ("Zacatelco", "Tlaxcala", "ciudad_principal", 19.2000, -98.2167, "Ciudad conocida por su mole y tradición gastronómica.", ["comida"]),
    ("Nativitas", "Tlaxcala", "ciudad_principal", 19.2333, -98.3667, "Municipio agrícola a orillas del río Zahuapan.", ["cultura"]),

    ("Ticul", "Yucatán", "ciudad_principal", 20.4000, -89.5333, "Ciudad alfarera famosa por sus panuchos y calzado.", ["comida", "cultura"]),
    ("Motul", "Yucatán", "ciudad_principal", 21.0975, -89.2867, "Ciudad henequenera, cuna de la cochinita pibil.", ["comida", "cultura"]),
    ("Tizimín", "Yucatán", "ciudad_principal", 21.1417, -88.1500, "Capital ganadera del oriente de Yucatán.", ["cultura"]),
    ("Maní", "Yucatán", "ciudad_principal", 20.3833, -89.3833, "Pueblo histórico maya, sede de un convento franciscano del siglo XVI.", ["cultura"]),

    ("Villanueva", "Zacatecas", "ciudad_principal", 22.3500, -102.8833, "Ciudad agrícola del centro-sur de Zacatecas.", ["cultura"]),
    ("Ojocaliente", "Zacatecas", "ciudad_principal", 22.5667, -102.2500, "Ciudad de aguas termales del sureste zacatecano.", ["descanso"]),

    # --- Tercera tanda: llegar a mínimo 3 sitios turísticos en los
    # estados que se quedaron cortos, y sumar en cada uno un lugar
    # realmente famoso que valga la pena el desvío aunque no esté en una
    # zona grande (el caso "Peña de Bernal" que mencionó el equipo).
    ("Museo Nacional de la Muerte", "Aguascalientes", "sitio_turistico", 21.8814, -102.2958, "Museo único en su tipo dedicado al imaginario de la muerte en México.", ["cultura"]),
    ("Cañón de Guadalupe", "Baja California", "sitio_turistico", 32.3333, -115.6333, "Cañón desértico con pozas de aguas termales naturales.", ["naturaleza", "descanso"]),
    ("Arco de Cabo San Lucas", "Baja California Sur", "sitio_turistico", 22.8697, -109.9066, "La formación rocosa más famosa de México, donde se unen el Pacífico y el Golfo de California.", ["naturaleza", "playas"]),
    ("Fuerte de San Miguel", "Campeche", "sitio_turistico", 19.8167, -90.5500, "Fuerte colonial con vistas al Golfo, hoy museo arqueológico.", ["cultura"]),
    ("Bonampak", "Chiapas", "sitio_turistico", 16.7050, -91.0644, "Zona arqueológica maya famosa por sus murales a color mejor conservados de Mesoamérica.", ["cultura", "naturaleza"]),
    ("Cascada de Basaseachi", "Chihuahua", "sitio_turistico", 28.1833, -108.2167, "Una de las cascadas más altas de México, con más de 240 metros de caída.", ["naturaleza"]),
    ("Boca de Pascuales", "Colima", "sitio_turistico", 18.7667, -103.9333, "Playa famosa mundialmente entre surfistas por su ola tubular.", ["playas", "naturaleza"]),
    ("Parque Nacional El Chico", "Hidalgo", "sitio_turistico", 20.1667, -98.7333, "Bosque de pinos y formaciones rocosas para escalada, cerca de Pachuca.", ["naturaleza"]),
    ("Lago de Chapala", "Jalisco", "sitio_turistico", 20.2833, -103.0667, "El lago natural más grande de México, junto al pueblo de Ajijic.", ["naturaleza", "descanso"]),
    ("Volcán Paricutín", "Michoacán", "sitio_turistico", 19.4833, -102.2500, "El volcán más joven de América, nacido en un campo de maíz en 1943.", ["naturaleza"]),
    ("San Pancho", "Nayarit", "sitio_turistico", 21.1667, -105.2500, "Pueblo de playa bohemio en la Riviera Nayarit.", ["playas", "descanso"]),
    ("Cascada Las Brisas", "Puebla", "sitio_turistico", 20.0300, -97.5100, "Cascada escondida en la selva de niebla cerca de Cuetzalan.", ["naturaleza"]),
    ("Peña de Bernal", "Querétaro", "sitio_turistico", 20.7500, -99.9450, "Uno de los monolitos más altos del mundo, símbolo de Querétaro.", ["naturaleza", "cultura"]),
    ("Xcaret", "Quintana Roo", "sitio_turistico", 20.5794, -87.1197, "Parque ecoarqueológico con ríos subterráneos, cerca de Playa del Carmen.", ["naturaleza", "cultura"]),
    ("El Pinacate y Gran Desierto de Altar", "Sonora", "sitio_turistico", 31.7667, -113.5000, "Reserva de la biosfera volcánica, Patrimonio de la Humanidad.", ["naturaleza"]),
    ("Laguna Madre", "Tamaulipas", "sitio_turistico", 24.0000, -97.7500, "Uno de los sistemas de lagunas hipersalinas más grandes del mundo.", ["naturaleza"]),
    ("Poza Rica", "Veracruz", "ciudad_principal", 20.5333, -97.4500, "Ciudad petrolera cercana a la zona arqueológica de El Tajín.", ["cultura"]),
    ("Cascada de Texolo", "Veracruz", "sitio_turistico", 19.4667, -96.9500, "Cascada de 80 metros rodeada de selva, cerca de Xico.", ["naturaleza"]),
    ("Pico de Orizaba", "Veracruz", "sitio_turistico", 19.0303, -97.2683, "El pico más alto de México, visible desde varios estados.", ["naturaleza"]),
    ("Cerro de la Bufa", "Zacatecas", "sitio_turistico", 22.7822, -102.5644, "Mirador emblemático sobre la capital, accesible en teleférico.", ["naturaleza", "cultura"]),
    ("Mina El Edén", "Zacatecas", "sitio_turistico", 22.7736, -102.5789, "Antigua mina de plata del siglo XVI, hoy recorrido turístico.", ["cultura"]),
]


def seed():
    app = create_app()

    with app.app_context():
        estados_por_nombre = {e.nombre: e for e in Estado.query.all()}

        nuevos = 0
        for nombre, estado_nombre, tipo, lat, lon, descripcion, intereses in DESTINOS_V2:
            estado = estados_por_nombre.get(estado_nombre)
            if not estado:
                print(f"AVISO: estado no encontrado, se omite: {estado_nombre} ({nombre})")
                continue

            existe = Destino.query.filter_by(nombre=nombre, estado_id=estado.id).first()
            if existe:
                continue

            db.session.add(
                Destino(
                    nombre=nombre,
                    estado_id=estado.id,
                    tipo=tipo,
                    lat=lat,
                    lon=lon,
                    descripcion=descripcion,
                    intereses=intereses,
                    fuente="curada",
                )
            )
            nuevos += 1

        db.session.commit()
        print(f"Destinos nuevos agregados: {nuevos}")


if __name__ == "__main__":
    seed()
