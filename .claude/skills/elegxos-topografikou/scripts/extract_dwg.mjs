#!/usr/bin/env node
// Εξαγωγή DWG -> κανονικοποιημένο JSON (κοινό σχήμα με extract_dxf.py)
// Χρήση: node extract_dwg.mjs <input.dwg> <out.json>
import { LibreDwg, Dwg_File_Type } from '@mlightcad/libredwg-web';
import { readFileSync, writeFileSync } from 'node:fs';

const SRC = process.argv[2];
const OUT = process.argv[3] || SRC.replace(/\.[^.]+$/, '') + '.norm.json';
if (!SRC) { console.error('usage: node extract_dwg.mjs <input.dwg> <out.json>'); process.exit(2); }

function clean(s) {
  if (s == null) return '';
  let t = String(s);
  t = t.replace(/\\P/g, ' ').replace(/\\~/g, ' ');
  t = t.replace(/\\[fF][^;]*;/g, '').replace(/\\[HhWwQqTtAaCc][^;\\]*;/g, '');
  t = t.replace(/\\S([^;]*);/g, '$1').replace(/[{}]/g, '');
  t = t.replace(/\\[LlOoKk]/g, '');
  t = t.replace(/%%[dD]/g, '°').replace(/%%[pP]/g, '±').replace(/%%[cC]/g, 'Ø').replace(/%%\d+/g, '');
  t = t.replace(/\\\\/g, '\\');
  return t.trim();
}
const r3 = n => (typeof n === 'number' && isFinite(n)) ? Math.round(n * 1000) / 1000 : null;

const buf = readFileSync(SRC);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const lib = await LibreDwg.create();
const ptr = lib.dwg_read_data(ab, Dwg_File_Type.DWG);
if (!ptr) { console.error('ΣΦΑΛΜΑ: αποτυχία ανάγνωσης DWG'); process.exit(1); }
const db = lib.convert(ptr);

const texts = [], dims = [], polylines = [], layerSet = new Set(), counts = {};

function addText(layer, raw, pt, h) {
  const text = clean(raw);
  if (text === '') return;
  texts.push({ layer, text, x: pt ? r3(pt.x) : null, y: pt ? r3(pt.y) : null, h: h != null ? r3(h) : null });
}
function walk(e) {
  counts[e.type] = (counts[e.type] || 0) + 1;
  if (e.layer) layerSet.add(e.layer);
  switch (e.type) {
    case 'TEXT': addText(e.layer, e.text, e.startPoint, e.textHeight); break;
    case 'MTEXT': addText(e.layer, e.text, e.insertionPoint, e.textHeight); break;
    case 'ATTRIB':
    case 'ATTDEF': if (e.text) addText(e.layer, e.text.text, e.text.startPoint, e.text.textHeight); break;
    case 'DIMENSION':
      dims.push({ layer: e.layer, measurement: r3(e.measurement),
        textOverride: (e.text == null || e.text === '<>') ? null : e.text });
      break;
    case 'LWPOLYLINE':
    case 'POLYLINE':
      if (e.vertices && e.vertices.length > 1)
        polylines.push({ layer: e.layer, handle: e.handle, closed: !!(e.flag & 1),
          pts: e.vertices.map(v => [r3(v.x), r3(v.y)]) });
      break;
    case 'INSERT':
      if (Array.isArray(e.attributes)) e.attributes.forEach(a => { a.layer = a.layer || e.layer; walk(a); });
      break;
  }
}
for (const e of db.entities) walk(e);

const result = {
  source: SRC, format: 'DWG', engine: '@mlightcad/libredwg-web',
  counts, totalEntities: db.entities.length,
  layers: [...layerSet].sort(),
  texts, dims, polylines
};
writeFileSync(OUT, JSON.stringify(result));
console.error(`DWG OK: ${db.entities.length} οντότητες, ${texts.length} κείμενα, ${dims.length} διαστάσεις, ${polylines.length} polylines -> ${OUT}`);
