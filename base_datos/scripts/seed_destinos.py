"""Carga inicial (seed) de estados y destinos curados en Supabase.

Uso:
    python scripts/seed_destinos.py

Es seguro volver a correrlo: no duplica filas, solo inserta lo que falte
(usa nombre + estado como llave). Este es el punto de partida de la
"plantilla" de destinos — capitales/ciudades principales y un primer grupo
de pueblos mágicos verificados. El equipo puede seguir agregando filas a
mano desde el Table Editor de Supabase, y más adelante la IA agregará
automáticamente los pueblos más pequeños que no estén aquí.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

ESTADOS = [
    ("Aguascalientes", "AGS"),
    ("Baja California", "BC"),
    ("Baja California Sur", "BCS"),
    ("Campeche", "CAM"),
    ("Chiapas", "CHIS"),
    ("Chihuahua", "CHIH"),
    ("Ciudad de México", "CDMX"),
    ("Coahuila", "COAH"),
    ("Colima", "COL"),
    ("Durango", "DGO"),
    ("Guanajuato", "GTO"),
    ("Guerrero", "GRO"),
    ("Hidalgo", "HGO"),
    ("Jalisco", "JAL"),
    ("México", "MEX"),
    ("Michoacán", "MICH"),
    ("Morelos", "MOR"),
    ("Nayarit", "NAY"),
    ("Nuevo León", "NL"),
    ("Oaxaca", "OAX"),
    ("Puebla", "PUE"),
    ("Querétaro", "QRO"),
    ("Quintana Roo", "QROO"),
    ("San Luis Potosí", "SLP"),
    ("Sinaloa", "SIN"),
    ("Sonora", "SON"),
    ("Tabasco", "TAB"),
    ("Tamaulipas", "TAMS"),
    ("Tlaxcala", "TLAX"),
    ("Veracruz", "VER"),
    ("Yucatán", "YUC"),
    ("Zacatecas", "ZAC"),
]

# (nombre, estado, tipo, lat, lon, descripcion, intereses)
DESTINOS = [
    # Capitales / ciudades principales
    ("Aguascalientes", "Aguascalientes", "ciudad_principal", 21.8853, -102.2916, "Capital del estado, conocida por su feria anual y su centro histórico.", ["comida"]),
    ("Mexicali", "Baja California", "ciudad_principal", 32.6245, -115.4523, "Capital fronteriza de Baja California.", ["comida"]),
    ("Tijuana", "Baja California", "ciudad_principal", 32.5149, -117.0382, "Ciudad fronteriza, gastronomía y vida nocturna.", ["comida"]),
    ("La Paz", "Baja California Sur", "ciudad_principal", 24.1426, -110.3128, "Capital costera sobre el Mar de Cortés.", ["playas", "descanso"]),
    ("Los Cabos", "Baja California Sur", "ciudad_principal", 22.8905, -109.9167, "Destino de playa de lujo al sur de la península.", ["playas", "descanso"]),
    ("San Francisco de Campeche", "Campeche", "ciudad_principal", 19.8301, -90.5349, "Capital amurallada frente al Golfo de México.", ["comida"]),
    ("Tuxtla Gutiérrez", "Chiapas", "ciudad_principal", 16.7516, -93.1029, "Capital de Chiapas, puerta al Cañón del Sumidero.", ["naturaleza"]),
    ("Chihuahua", "Chihuahua", "ciudad_principal", 28.6353, -106.0889, "Capital del estado, puerta a la Sierra Tarahumara.", ["comida"]),
    ("Ciudad de México", "Ciudad de México", "ciudad_principal", 19.4326, -99.1332, "Capital del país, historia, museos y gastronomía.", ["comida"]),
    ("Saltillo", "Coahuila", "ciudad_principal", 25.4260, -100.9959, "Capital de Coahuila, cultura e industria.", ["comida"]),
    ("Colima", "Colima", "ciudad_principal", 19.2433, -103.7247, "Capital del estado, cercana al volcán de Colima.", ["naturaleza"]),
    ("Durango", "Durango", "ciudad_principal", 24.0277, -104.6532, "Capital del estado, historia y cine western.", ["comida"]),
    ("Guanajuato", "Guanajuato", "ciudad_principal", 21.0190, -101.2574, "Capital colonial de callejones y túneles.", ["comida"]),
    ("León", "Guanajuato", "ciudad_principal", 21.1250, -101.6860, "La ciudad más grande del estado, industria del calzado.", ["comida"]),
    ("Chilpancingo", "Guerrero", "ciudad_principal", 17.5514, -99.5020, "Capital de Guerrero.", ["comida"]),
    ("Acapulco", "Guerrero", "ciudad_principal", 16.8531, -99.8237, "Icónico puerto y destino de playa.", ["playas", "descanso"]),
    ("Pachuca", "Hidalgo", "ciudad_principal", 20.1011, -98.7591, "Capital de Hidalgo, la Bella Airosa.", ["comida"]),
    ("Guadalajara", "Jalisco", "ciudad_principal", 20.6597, -103.3496, "Capital de Jalisco, cuna del mariachi y el tequila.", ["comida"]),
    ("Puerto Vallarta", "Jalisco", "ciudad_principal", 20.6534, -105.2253, "Destino de playa en la costa del Pacífico.", ["playas", "descanso"]),
    ("Toluca", "México", "ciudad_principal", 19.2926, -99.6568, "Capital del Estado de México, cercana al Nevado de Toluca.", ["naturaleza"]),
    ("Morelia", "Michoacán", "ciudad_principal", 19.7060, -101.1950, "Capital colonial, Patrimonio de la Humanidad.", ["comida"]),
    ("Cuernavaca", "Morelos", "ciudad_principal", 18.9186, -99.2342, "Capital de Morelos, la ciudad de la eterna primavera.", ["descanso"]),
    ("Tepic", "Nayarit", "ciudad_principal", 21.5041, -104.8942, "Capital de Nayarit.", ["comida"]),
    ("Monterrey", "Nuevo León", "ciudad_principal", 25.6866, -100.3161, "Capital industrial rodeada de montañas.", ["comida"]),
    ("Oaxaca de Juárez", "Oaxaca", "ciudad_principal", 17.0732, -96.7266, "Capital de Oaxaca, gastronomía y arte popular.", ["comida"]),
    ("Puebla de Zaragoza", "Puebla", "ciudad_principal", 19.0414, -98.2063, "Capital de Puebla, cocina tradicional y talavera.", ["comida"]),
    ("Querétaro", "Querétaro", "ciudad_principal", 20.5888, -100.3899, "Capital colonial, centro histórico Patrimonio de la Humanidad.", ["comida"]),
    ("Chetumal", "Quintana Roo", "ciudad_principal", 18.5001, -88.2960, "Capital de Quintana Roo, frontera con Belice.", ["playas"]),
    ("Cancún", "Quintana Roo", "ciudad_principal", 21.1619, -86.8515, "Destino de playa del Caribe mexicano.", ["playas", "descanso"]),
    ("San Luis Potosí", "San Luis Potosí", "ciudad_principal", 22.1565, -100.9855, "Capital del estado.", ["comida"]),
    ("Culiacán", "Sinaloa", "ciudad_principal", 24.8069, -107.3940, "Capital de Sinaloa.", ["comida"]),
    ("Mazatlán", "Sinaloa", "ciudad_principal", 23.2494, -106.4111, "Puerto y destino de playa en el Pacífico.", ["playas", "descanso"]),
    ("Hermosillo", "Sonora", "ciudad_principal", 29.0729, -110.9559, "Capital de Sonora.", ["comida"]),
    ("Villahermosa", "Tabasco", "ciudad_principal", 17.9895, -92.9475, "Capital de Tabasco.", ["naturaleza"]),
    ("Ciudad Victoria", "Tamaulipas", "ciudad_principal", 23.7369, -99.1411, "Capital de Tamaulipas.", ["comida"]),
    ("Tlaxcala de Xicohténcatl", "Tlaxcala", "ciudad_principal", 19.3181, -98.2375, "Capital del estado más pequeño de México.", ["comida"]),
    ("Xalapa", "Veracruz", "ciudad_principal", 19.5438, -96.9102, "Capital de Veracruz, rodeada de café y niebla.", ["naturaleza", "comida"]),
    ("Veracruz", "Veracruz", "ciudad_principal", 19.1738, -96.1342, "Puerto histórico sobre el Golfo de México.", ["playas", "comida"]),
    ("Mérida", "Yucatán", "ciudad_principal", 20.9674, -89.5926, "Capital de Yucatán, cultura maya y colonial.", ["comida"]),
    ("Zacatecas", "Zacatecas", "ciudad_principal", 22.7709, -102.5832, "Capital minera, Patrimonio de la Humanidad.", ["comida"]),

    # Pueblos mágicos (grupo inicial, verificado)
    ("Valle de Bravo", "México", "pueblo_magico", 19.1947, -100.1319, "Bosque, lago y aire fresco para un respiro tranquilo.", ["naturaleza", "descanso"]),
    ("Tequila", "Jalisco", "pueblo_magico", 20.8809, -103.8372, "Cuna del tequila, agaves y destilerías.", ["comida"]),
    ("Bernal", "Querétaro", "pueblo_magico", 20.7458, -99.9439, "Pueblo al pie de la Peña de Bernal.", ["pueblos_magicos"]),
    ("San Miguel de Allende", "Guanajuato", "pueblo_magico", 20.9153, -100.7436, "Arquitectura colonial y arte.", ["comida"]),
    ("Tepoztlán", "Morelos", "pueblo_magico", 18.9847, -99.0937, "Pueblo mágico entre montañas, cerca de la pirámide del Tepozteco.", ["naturaleza"]),
    ("San Cristóbal de las Casas", "Chiapas", "pueblo_magico", 16.7370, -92.6376, "Ciudad colonial en los Altos de Chiapas.", ["comida"]),
    ("Sayulita", "Nayarit", "pueblo_magico", 20.8698, -105.4412, "Pueblo de playa y surf en la Riviera Nayarit.", ["playas", "descanso"]),
    ("Todos Santos", "Baja California Sur", "pueblo_magico", 23.4475, -110.2231, "Pueblo de playa entre el desierto y el mar.", ["playas", "descanso"]),
    ("Real de Catorce", "San Luis Potosí", "pueblo_magico", 23.6870, -100.8850, "Antiguo pueblo minero en el desierto.", ["naturaleza"]),
    ("Pátzcuaro", "Michoacán", "pueblo_magico", 19.5138, -101.6100, "Pueblo lacustre, famoso por el Día de Muertos.", ["comida"]),
    ("Tapalpa", "Jalisco", "pueblo_magico", 19.9463, -103.7669, "Pueblo de montaña con bosques y cabañas.", ["naturaleza", "descanso"]),
    ("Cuetzalan", "Puebla", "pueblo_magico", 20.0264, -97.5225, "Pueblo de niebla en la sierra poblana.", ["naturaleza"]),
    ("Taxco", "Guerrero", "pueblo_magico", 18.5561, -99.6034, "Pueblo minero famoso por la plata.", ["comida"]),
    ("Izamal", "Yucatán", "pueblo_magico", 20.9319, -89.0181, "La ciudad amarilla, cultura maya y colonial.", ["comida"]),
    ("Valladolid", "Yucatán", "pueblo_magico", 20.6896, -88.2019, "Pueblo colonial cerca de cenotes y Chichén Itzá.", ["comida"]),
    ("Dolores Hidalgo", "Guanajuato", "pueblo_magico", 21.1569, -100.9313, "Cuna de la Independencia de México.", ["comida"]),
    ("Coatepec", "Veracruz", "pueblo_magico", 19.4569, -96.9578, "Pueblo cafetalero rodeado de niebla.", ["naturaleza", "comida"]),
    ("Álamos", "Sonora", "pueblo_magico", 27.0281, -108.9364, "Pueblo colonial en el desierto sonorense.", ["comida"]),
    ("Creel", "Chihuahua", "pueblo_magico", 27.7519, -107.6339, "Puerta a las Barrancas del Cobre.", ["naturaleza"]),
    ("Parras", "Coahuila", "pueblo_magico", 25.4436, -102.1811, "Cuna del vino mexicano.", ["comida"]),
    ("Bacalar", "Quintana Roo", "pueblo_magico", 18.6772, -88.3969, "La laguna de los siete colores.", ["playas", "descanso", "naturaleza"]),
    ("Comala", "Colima", "pueblo_magico", 19.3286, -103.7592, "Pueblo blanco al pie del volcán de Colima.", ["comida"]),
    ("Huasca de Ocampo", "Hidalgo", "pueblo_magico", 20.2003, -98.5833, "Pueblo de bosques y prismas basálticos.", ["naturaleza"]),
    ("Xilitla", "San Luis Potosí", "pueblo_magico", 21.3833, -98.9975, "Selva y el Jardín Surrealista de Edward James.", ["naturaleza"]),
    ("Mazamitla", "Jalisco", "pueblo_magico", 19.9167, -103.0167, "Pueblo de montaña con cabañas y bosque.", ["naturaleza", "descanso"]),
    ("Calvillo", "Aguascalientes", "pueblo_magico", 21.8500, -102.7167, "Región guayabera, huertas y atardeceres.", ["naturaleza", "comida"]),
    ("Tecate", "Baja California", "pueblo_magico", 32.5667, -116.6333, "Pueblo fronterizo de montaña, cervecería y panaderías tradicionales.", ["comida"]),
    ("Loreto", "Baja California Sur", "pueblo_magico", 26.0122, -111.3475, "Primera misión de las Californias, frente al Golfo de California.", ["playas", "naturaleza"]),
    ("Palizada", "Campeche", "pueblo_magico", 18.2667, -92.1000, "Pueblo ribereño de casas coloridas sobre el río Palizada.", ["naturaleza"]),
    ("Chiapa de Corzo", "Chiapas", "pueblo_magico", 16.7075, -93.0114, "Pueblo colonial a orillas del Cañón del Sumidero.", ["naturaleza"]),
    ("Palenque", "Chiapas", "pueblo_magico", 17.5091, -91.9862, "Selva y una de las zonas arqueológicas mayas más importantes.", ["naturaleza", "pueblos_magicos"]),
    ("Comitán", "Chiapas", "pueblo_magico", 16.2500, -92.1333, "Pueblo colonial cerca de las lagunas de Montebello.", ["naturaleza"]),
    ("Batopilas", "Chihuahua", "pueblo_magico", 27.0167, -107.7333, "Antiguo pueblo minero en el fondo de la Barranca del Cobre.", ["naturaleza"]),
    ("Cuatro Ciénegas", "Coahuila", "pueblo_magico", 26.9833, -102.0667, "Pozas de agua turquesa únicas en el desierto de Coahuila.", ["naturaleza"]),
    ("Mapimí", "Durango", "pueblo_magico", 25.8333, -103.8500, "Pueblo minero cerca de la Zona del Silencio.", ["naturaleza"]),
    ("Yuriria", "Guanajuato", "pueblo_magico", 20.2000, -101.1500, "Pueblo lacustre con un exconvento agustino del siglo XVI.", ["naturaleza"]),
    ("Mineral del Chico", "Hidalgo", "pueblo_magico", 20.2000, -98.7333, "Bosque de pinos y encinos en la Sierra de Pachuca.", ["naturaleza"]),
    ("Real del Monte", "Hidalgo", "pueblo_magico", 20.1333, -98.6667, "Pueblo minero de influencia inglesa, cuna del pastel mexicano.", ["comida", "naturaleza"]),
    ("Lagos de Moreno", "Jalisco", "pueblo_magico", 21.3500, -101.9333, "Pueblo colonial de cantera rosa en Los Altos de Jalisco.", ["comida"]),
    ("Mascota", "Jalisco", "pueblo_magico", 20.5236, -104.7897, "Pueblo de montaña cerca de la costa de Jalisco.", ["naturaleza", "descanso"]),
    ("Malinalco", "México", "pueblo_magico", 18.9500, -99.4833, "Pueblo entre montañas con un templo prehispánico excavado en roca.", ["naturaleza"]),
    ("Tepotzotlán", "México", "pueblo_magico", 19.7139, -99.2233, "Pueblo colonial famoso por su templo barroco y museo virreinal.", ["comida"]),
    ("Tlalpujahua", "Michoacán", "pueblo_magico", 19.8000, -100.1833, "Pueblo minero famoso por sus esferas navideñas.", ["comida"]),
    ("Cuitzeo", "Michoacán", "pueblo_magico", 19.9667, -101.1333, "Pueblo a orillas del lago de Cuitzeo.", ["naturaleza"]),
    ("Tlayacapan", "Morelos", "pueblo_magico", 18.9500, -98.9833, "Pueblo con un exconvento agustino y tradición alfarera.", ["comida"]),
    ("Jala", "Nayarit", "pueblo_magico", 21.0833, -104.4333, "Pueblo agrícola al pie del volcán Ceboruco.", ["naturaleza"]),
    ("San Blas", "Nayarit", "pueblo_magico", 21.5333, -105.2833, "Pueblo costero con manglares y playas de surf.", ["playas", "naturaleza"]),
    ("Santiago", "Nuevo León", "pueblo_magico", 25.4167, -100.1500, "Pueblo de montaña junto a la Presa de la Boca.", ["naturaleza", "descanso"]),
    ("Chignahuapan", "Puebla", "pueblo_magico", 19.8333, -98.0333, "Pueblo famoso por sus esferas de vidrio soplado.", ["comida"]),
    ("Zacatlán", "Puebla", "pueblo_magico", 19.9333, -97.9667, "Pueblo de manzanas, relojes monumentales y cascadas.", ["naturaleza", "comida"]),
    ("Tequisquiapan", "Querétaro", "pueblo_magico", 20.5333, -99.8833, "Pueblo de aguas termales y viñedos.", ["descanso", "comida"]),
    ("Tulum", "Quintana Roo", "pueblo_magico", 20.2114, -87.4654, "Ruinas frente al mar y playas de arena blanca.", ["playas", "naturaleza"]),
    ("Isla Mujeres", "Quintana Roo", "pueblo_magico", 21.2311, -86.7314, "Isla caribeña frente a Cancún.", ["playas", "descanso"]),
    ("Cosalá", "Sinaloa", "pueblo_magico", 24.4000, -106.6833, "Pueblo minero colonial en la sierra sinaloense.", ["naturaleza"]),
    ("El Fuerte", "Sinaloa", "pueblo_magico", 26.4167, -108.6167, "Pueblo colonial, punto de partida del Chepe (tren Chihuahua al Pacífico).", ["naturaleza"]),
    ("Tapijulapa", "Tabasco", "pueblo_magico", 17.4667, -92.7500, "Pueblo entre ríos y selva, cerca de Villahermosa.", ["naturaleza"]),
    ("Tula", "Tamaulipas", "pueblo_magico", 23.0000, -99.7167, "Pueblo serrano famoso por su gastronomía y textiles.", ["comida"]),
    ("Huamantla", "Tlaxcala", "pueblo_magico", 19.3167, -97.9167, "Pueblo famoso por sus tapetes de aserrín y la feria de agosto.", ["comida"]),
    ("Papantla", "Veracruz", "pueblo_magico", 20.4500, -97.3167, "Pueblo de la vainilla y los Voladores.", ["comida", "pueblos_magicos"]),
    ("Xico", "Veracruz", "pueblo_magico", 19.4258, -97.0139, "Pueblo de cascadas y mole xiqueño.", ["naturaleza", "comida"]),
    ("Jerez", "Zacatecas", "pueblo_magico", 22.6500, -103.0000, "Pueblo de arquitectura porfiriana y tradición charra.", ["comida"]),
    ("Sombrerete", "Zacatecas", "pueblo_magico", 23.6333, -103.6333, "Pueblo minero colonial del norte de Zacatecas.", ["naturaleza"]),

    # Ciudades importantes adicionales (no son la capital, pero son grandes o muy visitadas)
    ("Ensenada", "Baja California", "ciudad_principal", 31.8667, -116.6000, "Puerto y región vinícola de Baja California.", ["comida", "playas"]),
    ("Ciudad del Carmen", "Campeche", "ciudad_principal", 18.6333, -91.8167, "Ciudad portuaria sobre la Laguna de Términos.", ["playas"]),
    ("Tapachula", "Chiapas", "ciudad_principal", 14.9036, -92.2569, "Ciudad fronteriza con Guatemala, región cafetalera.", ["comida"]),
    ("Ciudad Juárez", "Chihuahua", "ciudad_principal", 31.6904, -106.4245, "La ciudad más grande del estado, frontera con El Paso.", ["comida"]),
    ("Torreón", "Coahuila", "ciudad_principal", 25.5428, -103.4068, "Ciudad industrial de La Laguna.", ["comida"]),
    ("Manzanillo", "Colima", "ciudad_principal", 19.1053, -104.3436, "Principal puerto del Pacífico mexicano, playas y pesca deportiva.", ["playas", "descanso"]),
    ("Irapuato", "Guanajuato", "ciudad_principal", 20.6767, -101.3556, "Ciudad conocida como la capital mundial de la fresa.", ["comida"]),
    ("Celaya", "Guanajuato", "ciudad_principal", 20.5231, -100.8156, "Ciudad industrial, famosa por sus cajetas.", ["comida"]),
    ("Ixtapa-Zihuatanejo", "Guerrero", "ciudad_principal", 17.6417, -101.5528, "Destino de playa gemelo: resort moderno y pueblo pesquero.", ["playas", "descanso"]),
    ("Zapopan", "Jalisco", "ciudad_principal", 20.7167, -103.3833, "Parte del área metropolitana de Guadalajara, vida cultural y gastronómica.", ["comida"]),
    ("Uruapan", "Michoacán", "ciudad_principal", 19.4167, -102.0667, "Ciudad del aguacate, junto al Parque Nacional Barranca del Cupatitzio.", ["naturaleza", "comida"]),
    ("Puerto Escondido", "Oaxaca", "ciudad_principal", 15.8700, -97.0700, "Destino de playa y surf en la costa oaxaqueña.", ["playas", "descanso"]),
    ("Huatulco", "Oaxaca", "ciudad_principal", 15.7667, -96.1333, "Bahías y playas protegidas en la costa de Oaxaca.", ["playas", "descanso"]),
    ("Playa del Carmen", "Quintana Roo", "ciudad_principal", 20.6296, -87.0739, "Ciudad costera de la Riviera Maya.", ["playas", "descanso"]),
    ("Los Mochis", "Sinaloa", "ciudad_principal", 25.7896, -108.9761, "Ciudad agrícola, punto de partida del tren Chepe.", ["comida"]),
    ("Ciudad Obregón", "Sonora", "ciudad_principal", 27.4864, -109.9306, "Ciudad agrícola del Valle del Yaqui.", ["comida"]),
    ("Puerto Peñasco", "Sonora", "ciudad_principal", 31.3167, -113.5333, "Playas del Mar de Cortés, cercanas a la frontera con Arizona.", ["playas", "descanso"]),
    ("Tampico", "Tamaulipas", "ciudad_principal", 22.2333, -97.8500, "Ciudad portuaria sobre el Golfo de México.", ["playas"]),
    ("Reynosa", "Tamaulipas", "ciudad_principal", 26.0922, -98.2775, "Ciudad fronteriza del noreste mexicano.", ["comida"]),
    ("Córdoba", "Veracruz", "ciudad_principal", 18.8901, -96.9247, "Ciudad cafetalera con un centro histórico colonial.", ["comida"]),
    ("Orizaba", "Veracruz", "ciudad_principal", 18.8501, -97.1035, "Ciudad a los pies del Pico de Orizaba, el más alto de México.", ["naturaleza"]),

    # Sitios turísticos destacados (lo más conocido dentro/cerca de una ciudad)
    ("Centro Histórico de León", "Guanajuato", "sitio_turistico", 21.1225, -101.6816, "Zona peatonal, catedral y el icónico Arco de la Calzada de León.", ["comida"]),
    ("Zona Piel y Calzado de León", "Guanajuato", "sitio_turistico", 21.1231, -101.6600, "Distrito comercial de zapaterías y artículos de piel, sello de León.", ["comida"]),
    ("Centro Histórico de la Ciudad de México", "Ciudad de México", "sitio_turistico", 19.4340, -99.1332, "Zócalo, Catedral Metropolitana y Palacio Nacional.", ["comida"]),
    ("Coyoacán", "Ciudad de México", "sitio_turistico", 19.3467, -99.1618, "Barrio bohemio, mercados y la Casa Azul de Frida Kahlo.", ["comida"]),
    ("Xochimilco", "Ciudad de México", "sitio_turistico", 19.2647, -99.1031, "Canales y trajineras, Patrimonio de la Humanidad.", ["naturaleza"]),
    ("Chichén Itzá", "Yucatán", "sitio_turistico", 20.6843, -88.5678, "Una de las nuevas siete maravillas del mundo, zona arqueológica maya.", ["pueblos_magicos"]),
    ("Centro Histórico de Guadalajara", "Jalisco", "sitio_turistico", 20.6767, -103.3475, "Catedral, Teatro Degollado y el barrio de Tlaquepaque cerca.", ["comida"]),
]


def seed():
    app = create_app()

    with app.app_context():
        estados_por_nombre = {}

        for nombre, clave in ESTADOS:
            estado = Estado.query.filter_by(nombre=nombre).first()
            if not estado:
                estado = Estado(nombre=nombre, clave=clave)
                db.session.add(estado)
            estados_por_nombre[nombre] = estado

        db.session.commit()

        nuevos = 0
        for nombre, estado_nombre, tipo, lat, lon, descripcion, intereses in DESTINOS:
            estado = estados_por_nombre[estado_nombre]
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
        print(f"Estados: {len(ESTADOS)} listos. Destinos nuevos agregados: {nuevos}.")


if __name__ == "__main__":
    seed()
