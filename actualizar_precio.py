"""Lee el precio interno de referencia de la Federación Nacional de Cafeteros y lo guarda en precio.json."""
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

nuevo = {'carga': carga, 'fecha': fecha, 'fuente': 'Federación Nacional de Cafeteros'}
p = pathlib.Path('precio.json')
viejo = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
if viejo != nuevo:
    p.write_text(json.dumps(nuevo, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Actualizado:', nuevo)
else:
    print('Sin cambios:', nuevo)
