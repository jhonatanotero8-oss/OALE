"""Lee el precio interno de referencia de la Federación Nacional de Cafeteros y lo guarda en precio.json,
junto con el historial de los últimos 90 días (para mostrar si el café sube o baja)."""
import re, json, sys, pathlib, urllib.request

URL = 'https://federaciondecafeteros.org/'
req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (actualizador de precio OALE)'})
html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')

txt = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S)
txt = re.sub(r'<[^>]+>', ' ', txt)
txt = re.sub(r'\s+', ' ', txt)

m = re.search(r'Precio interno de referencia:\s*\$\s*([\d\.]+)\s.*?Fecha:\s*(\d{4}-\d{2}-\d{2})', txt)
if not m:
    sys.exit('No se pudo leer el precio: la página de la Federación cambió.')

carga = int(m.group(1).replace('.', ''))
fecha = m.group(2)
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
