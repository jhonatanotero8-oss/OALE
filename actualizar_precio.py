"""Lee el precio interno de referencia de la Federación Nacional de Cafeteros y lo guarda en precio.json,
junto con el historial de los últimos 90 días (para mostrar si el café sube o baja).

Prueba varias páginas de la Federación, vuelve a intentar si hay un fallo pasajero y,
si no puede leer el precio, explica en el registro exactamente qué pasó."""
import re, json, sys, time, html as _html, pathlib, urllib.request, urllib.error

PAGINAS = [
    'https://federaciondecafeteros.org/publicaciones/',
    'https://federaciondecafeteros.org/estadisticas-cafeteras/',
    'https://federaciondecafeteros.org/',
]
CABEZAS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'es-CO,es;q=0.9',
}


def bajar(url):
    """Descarga la página; si falla, espera y vuelve a intentar (3 veces)."""
    ultimo = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=CABEZAS)
            return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
        except Exception as e:
            ultimo = e
            print('   intento %d falló: %s' % (i + 1, e))
            time.sleep(3 * (i + 1))
    raise ultimo


def leer(pagina_html):
    """Saca (carga, fecha) del texto de la página, o None si no los encuentra."""
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', pagina_html, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = _html.unescape(t)
    t = re.sub(r'\s+', ' ', t)
    m = re.search(r'Precio interno de referencia:?\s*\$\s*([\d\.,]+)\s.{0,400}?Fecha:?\s*(\d{4}-\d{2}-\d{2})', t)
    if not m:
        i = t.find('Precio interno')
        print('   no encontré el precio. Texto cerca de "Precio interno":', t[i:i + 260] if i >= 0 else '(esa frase no aparece en la página)')
        return None
    return int(re.sub(r'[\.,]', '', m.group(1))), m.group(2)


encontrado = None
errores = []
for url in PAGINAS:
    print('Probando', url)
    try:
        r = leer(bajar(url))
    except Exception as e:
        errores.append('%s -> %s' % (url, e))
        continue
    if r:
        encontrado = r
        print('   precio leído:', r)
        break
    errores.append('%s -> la página no trae el precio con el formato esperado' % url)

if not encontrado:
    sys.exit('No se pudo leer el precio en ninguna página de la Federación.\n  ' + '\n  '.join(errores))

carga, fecha = encontrado
if not (500000 < carga < 20000000):
    sys.exit('Precio fuera de rango: %s' % carga)

p = pathlib.Path('precio.json')
viejo = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

# historial: se conserva lo que ya estaba y se agrega (o corrige) el precio de esa fecha
hist = {}
for x in viejo.get('historial', []):
    try:
        hist[str(x[0])] = int(x[1])
    except Exception:
        pass
hist[fecha] = carga
hist = dict(sorted(hist.items())[-90:])

nuevo = {'carga': carga, 'fecha': fecha, 'fuente': 'Federación Nacional de Cafeteros',
         'historial': [[f, c] for f, c in hist.items()]}
if viejo != nuevo:
    p.write_text(json.dumps(nuevo, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Actualizado:', fecha, carga, '| días en el historial:', len(hist))
else:
    print('Sin cambios:', fecha, carga)
