#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Εξαγωγή DXF -> κανονικοποιημένο JSON (κοινό σχήμα με extract_dwg.mjs).
Χρήση: python3 -I extract_dxf.py <input.dxf> <out.json>
Απαιτεί ezdxf (pip install ezdxf)."""
import sys, json, re

def clean(s):
    if s is None:
        return ''
    t = str(s)
    t = t.replace('\\P', ' ').replace('\\~', ' ')
    t = re.sub(r'\\[fF][^;]*;', '', t)
    t = re.sub(r'\\[HhWwQqTtAaCc][^;\\]*;', '', t)
    t = re.sub(r'\\S([^;]*);', r'\1', t)
    t = t.replace('{', '').replace('}', '')
    t = re.sub(r'\\[LlOoKk]', '', t)
    t = t.replace('%%d', '°').replace('%%D', '°').replace('%%p', '±').replace('%%P', '±')
    t = t.replace('%%c', 'Ø').replace('%%C', 'Ø')
    t = re.sub(r'%%\d+', '', t)
    return t.strip()

def r3(n):
    try:
        f = float(n)
        return round(f, 3)
    except (TypeError, ValueError):
        return None

def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: python3 -I extract_dxf.py <input.dxf> <out.json>\n'); sys.exit(2)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else re.sub(r'\.[^.]+$', '', src) + '.norm.json'
    try:
        import ezdxf
    except ImportError:
        sys.stderr.write('ΣΦΑΛΜΑ: λείπει το ezdxf (pip install ezdxf)\n'); sys.exit(1)

    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    texts, dims, polylines = [], [], []
    layers, counts = set(), {}

    def add_text(layer, raw, x, y, h):
        t = clean(raw)
        if t == '':
            return
        texts.append({'layer': layer, 'text': t, 'x': r3(x), 'y': r3(y), 'h': r3(h)})

    def handle_entity(e, inherit_layer=None):
        et = e.dxftype()
        counts[et] = counts.get(et, 0) + 1
        layer = getattr(e.dxf, 'layer', None) or inherit_layer
        if layer:
            layers.add(layer)
        if et == 'TEXT':
            p = e.dxf.insert
            add_text(layer, e.dxf.text, p.x, p.y, getattr(e.dxf, 'height', None))
        elif et == 'MTEXT':
            p = e.dxf.insert
            add_text(layer, e.text, p.x, p.y, getattr(e.dxf, 'char_height', None))
        elif et in ('ATTRIB', 'ATTDEF'):
            p = e.dxf.insert
            add_text(layer, e.dxf.text, p.x, p.y, getattr(e.dxf, 'height', None))
        elif et == 'DIMENSION':
            txt = getattr(e.dxf, 'text', '') or ''
            override = None if txt in ('', '<>') else txt
            meas = None
            try:
                meas = r3(e.get_measurement())
            except Exception:
                meas = r3(getattr(e.dxf, 'actual_measurement', None))
            dims.append({'layer': layer, 'measurement': meas, 'textOverride': override})
        elif et == 'LWPOLYLINE':
            pts = [[r3(p[0]), r3(p[1])] for p in e.get_points('xy')]
            if len(pts) > 1:
                polylines.append({'layer': layer, 'handle': e.dxf.handle,
                                  'closed': bool(e.closed), 'pts': pts})
        elif et == 'POLYLINE':
            pts = [[r3(v.dxf.location.x), r3(v.dxf.location.y)] for v in e.vertices]
            if len(pts) > 1:
                polylines.append({'layer': layer, 'handle': e.dxf.handle,
                                  'closed': bool(e.is_closed), 'pts': pts})
        elif et == 'INSERT':
            for a in e.attribs:
                handle_entity(a, inherit_layer=layer)

    for e in msp:
        handle_entity(e)

    result = {
        'source': src, 'format': 'DXF', 'engine': 'ezdxf',
        'counts': counts, 'totalEntities': sum(counts.values()),
        'layers': sorted(layers),
        'texts': texts, 'dims': dims, 'polylines': polylines,
    }
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    sys.stderr.write('DXF OK: %d οντότητες, %d κείμενα, %d διαστάσεις, %d polylines -> %s\n'
                     % (result['totalEntities'], len(texts), len(dims), len(polylines), out))

if __name__ == '__main__':
    main()
