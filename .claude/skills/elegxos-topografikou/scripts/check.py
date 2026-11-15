#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Αριθμητικός έλεγχος τοπογραφικού από κανονικοποιημένο JSON.
Χρήση: python3 -I check.py <norm.json> [out_findings.json]
Παράγει: numeric_findings (ανεξάρτητος επανυπολογισμός) + texts_for_review (συμπαγές)."""
import sys, json, re, math, statistics

SIDE_TOL = 0.015   # m
AREA_TOL = 0.05    # m^2
CLOSE_TOL = 0.01   # m
# ΕΓΣΑ87 / ΤΜ87 ευλογοφανές εύρος για Ελλάδα
X_MIN, X_MAX = 100000, 900000
Y_MIN, Y_MAX = 3800000, 4700000

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def shoelace(p):
    a = 0.0; n = len(p)
    for i in range(n):
        u, v = p[i], p[(i + 1) % n]
        a += u[0] * v[1] - v[0] * u[1]
    return abs(a) / 2.0

def perim(p):
    s = 0.0; n = len(p)
    for i in range(n):
        u, v = p[i], p[(i + 1) % n]
        s += math.hypot(v[0] - u[0], v[1] - u[1])
    return s

def parse_area(num):
    """ '6.221,05' ή '6221.05' -> float """
    raw = num.strip()
    if ',' in raw:
        return float(raw.replace('.', '').replace(',', '.'))
    return float(raw)

def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: python3 -I check.py <norm.json> [out.json]\n'); sys.exit(2)
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    out = sys.argv[2] if len(sys.argv) > 2 else None
    texts = data['texts']; polys = data['polylines']
    findings = []
    def F(sev, cat, msg, ev=None):
        findings.append({'sev': sev, 'cat': cat, 'msg': msg, 'evidence': ev})

    # ---------- auto-detect coordinate-table layer ----------
    isX = re.compile(r'^[1-9]\d{5}(\.\d+)?$')
    isY = re.compile(r'^3[89]\d{5}(\.\d+)?$|^4[0-6]\d{5}(\.\d+)?$')
    isId = re.compile(r'^\d{1,4}$')
    sideRe = re.compile(r'^\s*(\d{1,4})\s*-\s*(\d{1,4})\s*=\s*([\d.]+)\s*$')
    layer_score = {}
    for t in texts:
        if isX.match(t['text']) or isY.match(t['text']):
            layer_score[t['layer']] = layer_score.get(t['layer'], 0) + 1
    table_layer = max(layer_score, key=layer_score.get) if layer_score else None

    tbl = [t for t in texts if t['layer'] == table_layer]
    # group by row (rounded y)
    rows = {}
    for t in tbl:
        if t['y'] is None:
            continue
        rows.setdefault(round(t['y'], 2), []).append(t)
    points = {}; conflicts = []
    for _, r in rows.items():
        ids = sorted([t for t in r if isId.match(t['text'])], key=lambda t: t['x'] if t['x'] is not None else 0)
        xs = sorted([t for t in r if isX.match(t['text'])], key=lambda t: t['x'] if t['x'] is not None else 0)
        ys = sorted([t for t in r if isY.match(t['text'])], key=lambda t: t['x'] if t['x'] is not None else 0)
        if ids and xs and ys:
            n = min(len(ids), len(xs), len(ys))
            for i in range(n):
                pid = int(ids[i]['text']); X = float(xs[i]['text']); Y = float(ys[i]['text'])
                if pid in points:
                    if dist(points[pid], (X, Y)) > 0.02:
                        conflicts.append({'id': pid, 'a': points[pid], 'b': [X, Y]})
                else:
                    points[pid] = (X, Y)
    sides = []
    for t in tbl:
        m = sideRe.match(t['text'])
        if m:
            sides.append((int(m.group(1)), int(m.group(2)), float(m.group(3))))

    # ---------- CHECK 1: side lengths ----------
    s_ok = s_bad = s_no = 0; side_errs = []
    for a, b, d in sides:
        if a in points and b in points:
            dc = dist(points[a], points[b])
            if abs(dc - d) <= SIDE_TOL:
                s_ok += 1
            else:
                s_bad += 1
                side_errs.append({'side': '%d-%d' % (a, b), 'table': d, 'computed': round(dc, 3), 'diff': round(abs(dc - d), 3)})
        else:
            s_no += 1
    if s_bad:
        for e in side_errs:
            F('ΟΥΣΙΑΣΤΙΚΟ', 'πλευρά', 'Πλευρά %s: πίνακας=%.3f αλλά υπολογισμένη=%.3f (Δ=%.3f m)'
              % (e['side'], e['table'], e['computed'], e['diff']), e)
    if conflicts:
        for c in conflicts:
            F('ΟΥΣΙΑΣΤΙΚΟ', 'κορυφή', 'Κορυφή %d με δύο διαφορετικές συντεταγμένες στον πίνακα' % c['id'], c)

    # ---------- CHECK 2: areas (written E= vs shoelace) ----------
    area_re = re.compile(r'[EΕ]\s*=\s*([\d.,]+)\s*τ\.?\s*μ', re.IGNORECASE)
    written = []
    for t in texts:
        for m in area_re.finditer(t['text']):
            try:
                v = parse_area(m.group(1))
                if v > 1:
                    written.append(round(v, 2))
            except ValueError:
                pass
    written = sorted(set(written))
    poly_areas = [{'layer': p['layer'], 'handle': p['handle'], 'A': round(shoelace([tuple(x) for x in p['pts']]), 2),
                   'P': round(perim([tuple(x) for x in p['pts']]), 2), 'n': len(p['pts'])} for p in polys if len(p['pts']) >= 3]
    area_match = []
    for w in written:
        hit = next((pa for pa in poly_areas if abs(pa['A'] - w) <= AREA_TOL), None)
        area_match.append({'written': w, 'match': ('%s[%s]=%.2f' % (hit['layer'], hit['handle'], hit['A'])) if hit else None})
        if not hit:
            F('ΕΛΕΓΧΟΣ', 'εμβαδόν', 'Αναγραφόμενο εμβαδόν %.2f τ.μ. χωρίς αντίστοιχη κλειστή γεωμετρία (ίσως σε LINES ή άλλο layer)' % w, {'written': w})

    # ---------- CHECK 3: polygon closure (boundary-ish layers) ----------
    closure = []
    for p in polys:
        if len(p['pts']) >= 3 and not p['closed']:
            g = dist(tuple(p['pts'][0]), tuple(p['pts'][-1]))
            if g <= CLOSE_TOL:
                closure.append({'layer': p['layer'], 'handle': p['handle'], 'gap': round(g, 3), 'ok': True})
            # ανοικτές με μεγάλο κενό δεν θεωρούνται όρια -> αγνοούνται

    # ---------- CHECK 4: ΚΑΕΚ μορφή ----------
    kaek = sorted(set(re.findall(r'\b\d{12}\b|\b\d{14}\b', ' '.join(t['text'] for t in texts))))
    weird = sorted(set(re.findall(r'\b\d{13}\b|\b\d{15,}\b', ' '.join(t['text'] for t in texts))))
    for k in weird:
        if k[:2] in ('15', '05', '03', '04', '02', '01', '09', '12', '18', '19', '27', '35', '45', '50', '05'):
            F('ΕΛΕΓΧΟΣ', 'ΚΑΕΚ', 'Πιθανό ΚΑΕΚ με μη τυπικό πλήθος ψηφίων (%d): %s (τα γεωτεμάχια έχουν 12, οι ιδιοκτησίες 14)' % (len(k), k), {'kaek': k})

    # ---------- CHECK 5: εύρος ΕΓΣΑ87 ----------
    oor = 0
    for pid, p in points.items():
        if not (X_MIN <= p[0] <= X_MAX and Y_MIN <= p[1] <= Y_MAX):
            oor += 1
            F('ΟΥΣΙΑΣΤΙΚΟ', 'ΕΓΣΑ87', 'Κορυφή %d εκτός ευλογοφανούς εύρους ΕΓΣΑ87: (%.3f, %.3f)' % (pid, p[0], p[1]), {'id': pid})
    # outliers (απομακρυσμένες κορυφές)
    if len(points) >= 5:
        mx = statistics.median(p[0] for p in points.values())
        my = statistics.median(p[1] for p in points.values())
        for pid, p in points.items():
            if abs(p[0] - mx) > 5000 or abs(p[1] - my) > 5000:
                F('ΕΛΕΓΧΟΣ', 'κορυφή-outlier', 'Κορυφή %d πολύ μακριά από το σύνολο (πιθανό λάθος πληκτρολόγησης): (%.3f, %.3f)' % (pid, p[0], p[1]), {'id': pid})

    # ---------- texts_for_review: συμπαγές, μόνο όσα έχουν γράμματα ----------
    has_letter = re.compile(r'[A-Za-zΑ-Ωα-ωΆΈΉΊΌΎΏάέήίόύώϊϋΐΰ]')
    seen = set(); review = []
    for t in texts:
        if t['layer'] == table_layer:
            continue
        s = t['text']
        if not has_letter.search(s):
            continue
        key = (t['layer'], s)
        if key in seen:
            continue
        seen.add(key)
        review.append({'layer': t['layer'], 'text': s})

    summary = {
        'format': data.get('format'), 'layers': len(data.get('layers', [])),
        'table_layer': table_layer, 'points': len(points), 'sides': len(sides),
        'sides_ok': s_ok, 'sides_bad': s_bad, 'sides_no_coord': s_no,
        'conflicts': len(conflicts),
        'written_areas': written, 'area_match': area_match,
        'polygons_closed_ok': len(closure),
        'kaek': kaek, 'coords_out_of_range': oor,
        'numeric_findings': len([f for f in findings]),
    }
    result = {'summary': summary, 'numeric_findings': findings,
              'poly_areas': poly_areas, 'texts_for_review': review}
    if out:
        json.dump(result, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # stdout: αναφορά αριθμητικών
    print('=== ΑΡΙΘΜΗΤΙΚΟΙ ΕΛΕΓΧΟΙ ===')
    print('Μορφή: %s | layers: %d | layer πίνακα: %s' % (summary['format'], summary['layers'], table_layer))
    print('Κορυφές πίνακα: %d | Πλευρές: %d -> ΟΚ=%d ΛΑΘΟΣ=%d (χωρίς συντ.)=%d | Συγκρούσεις: %d'
          % (len(points), len(sides), s_ok, s_bad, s_no, len(conflicts)))
    print('Αναγραφόμενα εμβαδά (E=):', written)
    for am in area_match:
        print('   %.2f τ.μ. -> %s' % (am['written'], am['match'] or 'ΧΩΡΙΣ ΑΝΤΙΣΤΟΙΧΙΑ'))
    print('Κλειστά πολύγωνα (gap≈0): %d | ΚΑΕΚ: %s | εκτός εύρους: %d' % (len(closure), ','.join(kaek) or '—', oor))
    print('Αριθμητικά ευρήματα: %d' % len(findings))
    for f in findings:
        print('  [%s/%s] %s' % (f['sev'], f['cat'], f['msg']))
    print('Κείμενα προς έλεγχο (για το μοντέλο): %d' % len(review))
    if out:
        print('JSON:', out)

if __name__ == '__main__':
    main()
