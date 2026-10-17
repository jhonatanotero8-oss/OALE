"""Descarga de OpenStreetMap las tiendas agrícolas de Colombia y las guarda en proveedores_osm.json.

Se ejecuta UNA vez por semana desde GitHub Actions (una sola consulta para todo el país), así los celulares
no consultan el servicio del mapa: solo leen este archivo. Datos: (c) colaboradores de OpenStreetMap, licencia ODbL.
Si la descarga falla, NO se borra el archivo anterior.
"""
import json, sys, time, pathlib, datetime, urllib.request, urllib.parse

ENDPOINTS = ['https://overpass-api.de/api/interpreter',
             'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
UA = 'OALE-actualizador/1.0 (https://github.com/jhonatanotero8-oss/OALE)'
QUERY = '''[out:json][timeout:180];
area["ISO3166-1"="CO"][admin_level=2]->.co;
(
  nwr["shop"="agrarian"](area.co);
  nwr["shop"="trade"]["trade"="agricultural_supplies"](area.co);
  nwr["shop"="agricultural_supplies"](area.co);
  nwr["shop"="agro"](area.co);
  nwr["shop"="garden_centre"](area.co);
  nwr["shop"="country_store"](area.co);
  nwr["shop"="tractor"](area.co);
);
out center tags;'''

PRODUCTOS = {'fertilizer': 'Abonos y fertilizantes', 'seed': 'Semillas', 'pesticide': 'Venenos y fungicidas',
             'tools': 'Herramientas', 'feed': 'Concentrados para animales',
             'agricultural_machinery': 'Maquinaria agrícola', 'machine_parts': 'Repuestos de maquinaria',
             'yes': 'Insumos agrícolas'}


def limpio(t, n=120):
    return ' '.join(str(t or '').split())[:n]


def categoria(t):
    ag = (t.get('agrarian') or '').lower()
    if 'fertilizer' in ag:
        return 'abonos'
    if 'seed' in ag or t.get('shop') == 'garden_centre':
        return 'semillas'
    if 'tools' in ag or 'machine' in ag or t.get('shop') == 'tractor':
        return 'herramientas'
    return 'insumos'


def productos(t):
    out = []
    for v in (t.get('agrarian') or '').lower().replace(',', ';').split(';'):
        p = PRODUCTOS.get(v.strip())
        if p and p not in out:
            out.append(p)
    if t.get('shop') == 'garden_centre' and 'Plantas y viveros' not in out:
        out.append('Plantas y viveros')
    if t.get('shop') == 'tractor' and 'Maquinaria agrícola' not in out:
        out.append('Maquinaria agrícola')
    if t.get('shop') == 'country_store':
        out.append('Artículos del campo')
    return out


def telefono(t):
    for k in ('phone', 'contact:phone', 'mobile', 'contact:mobile'):
        v = t.get(k)
        if v:
            return limpio(str(v).split(';')[0], 30)
    return ''


def transform(elements):
    """Convierte la respuesta de Overpass en la lista que lee la app. Solo lugares con nombre y coordenadas."""
    vistos, lugares = set(), []
    for e in elements or []:
        t = e.get('tags') or {}
        nombre = limpio(t.get('name'))
        if not nombre:
            continue
        lat = e.get('lat', (e.get('center') or {}).get('lat'))
        lon = e.get('lon', (e.get('center') or {}).get('lon'))
        if lat is None or lon is None:
            continue
        if not (-5 < lat < 14 and -82 < lon < -66):      # fuera de Colombia: descartar
            continue
        clave = (nombre.lower(), round(lat, 3), round(lon, 3))
        if clave in vistos:
            continue
        vistos.add(clave)
        calle = limpio(' '.join(x for x in (t.get('addr:street'), t.get('addr:housenumber')) if x), 80)
        lugares.append({
            'id': e.get('type', 'n')[0] + str(e.get('id')),
            'nombre': nombre,
            'categoria': categoria(t),
            'lat': round(lat, 5), 'lon': round(lon, 5),
            'direccion': calle,
            'ciudad': limpio(t.get('addr:city') or t.get('addr:town') or t.get('addr:village') or t.get('addr:suburb'), 60),
            'telefono': telefono(t),
            'productos': productos(t),
        })
    lugares.sort(key=lambda x: (x['ciudad'], x['nombre']))
    return lugares[:8000]


def descargar():
    datos = urllib.parse.urlencode({'data': QUERY}).encode()
    ultimo = None
    for url in ENDPOINTS:
        for intento in range(3):
            try:
                req = urllib.request.Request(url, data=datos, headers={'User-Agent': UA})
                j = json.loads(urllib.request.urlopen(req, timeout=200).read().decode('utf-8'))
                if 'remark' in j and 'error' in str(j['remark']).lower():
                    raise RuntimeError(j['remark'])
                if not isinstance(j.get('elements'), list):
                    raise RuntimeError('respuesta sin elementos')
                return j['elements']
            except Exception as ex:                       # reintentar con calma
                ultimo = ex
                print('Intento fallido', url, intento + 1, ex)
                time.sleep(20)
    sys.exit('No se pudo descargar del mapa: %s' % ultimo)


def main():
    p = pathlib.Path('proveedores_osm.json')
    viejo = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'lugares': []}
    lugares = transform(descargar())
    if len(lugares) < 10 and len(viejo.get('lugares', [])) > len(lugares):
        sys.exit('Solo llegaron %d lugares y antes había %d: no se reemplaza.' % (len(lugares), len(viejo['lugares'])))
    if viejo.get('lugares') == lugares:
        print('Sin cambios (%d lugares)' % len(lugares))
        return
    nuevo = {'fuente': 'OpenStreetMap', 'licencia': 'ODbL', 'actualizado': datetime.date.today().isoformat(),
             'total': len(lugares), 'lugares': lugares}
    p.write_text(json.dumps(nuevo, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print('Actualizado: %d lugares' % len(lugares))


if __name__ == '__main__':
    main()
