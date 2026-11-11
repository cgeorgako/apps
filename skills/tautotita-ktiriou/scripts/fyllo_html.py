#!/usr/bin/env python3
"""Φύλλο Συμπλήρωσης ΗΤΚ — αυτόνομο HTML με κουμπί αντιγραφής ανά πεδίο.

Χρήση:
    python3 -I fyllo_html.py υπόθεση.json --out fyllo.html [--elegxoi ευρήματα.json]
"""
import argparse
import html
import json
from pathlib import Path

E = html.escape


def keno(v):
    return v is None or (isinstance(v, str) and v.strip() == "") or v == [] or v == {}


def lista(v):
    if isinstance(v, dict):
        v = [v]
    return [x for x in (v or []) if isinstance(x, dict) and any(not keno(y) for k, y in x.items() if not str(k).startswith("_"))]


def timi(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    if isinstance(v, dict):
        return ""
    return "" if v is None else str(v)


def pedio(etiketa, v, ypoxr=False):
    v = timi(v)
    ast = '<span class="ast">*</span>' if ypoxr else ""
    if v == "":
        return f'<div class="f empty"><label>{E(etiketa)}{ast}</label><span class="v">—</span></div>'
    return (f'<div class="f"><label>{E(etiketa)}{ast}</label>'
            f'<span class="v" data-v="{E(v)}">{E(v)}</span><button class="cp" title="Αντιγραφή">⧉</button></div>')


def pinakas(stiles, grammes, synola=None):
    th = "".join(f"<th>{E(s)}</th>" for s, _ in stiles)
    body = []
    for g in grammes:
        tds = []
        for _, k in stiles:
            v = timi(k(g) if callable(k) else g.get(k))
            tds.append(f'<td class="c" data-v="{E(v)}">{E(v)}</td>' if v else "<td></td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    if synola:
        body.append('<tr class="tot">' + "".join(f"<td>{E(timi(x))}</td>" for x in synola) + "</tr>")
    if not grammes:
        body.append(f'<tr><td colspan="{len(stiles)}" class="none">Δεν υπάρχουν εγγραφές</td></tr>')
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def num(v):
    try:
        s = str(v).strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def gr(x):
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_ypothesis")
    ap.add_argument("--out", required=True)
    ap.add_argument("--elegxoi")
    a = ap.parse_args()

    d = json.loads(Path(a.json_ypothesis).read_text(encoding="utf-8"))
    meta = d.get("_meta") or {}
    o = d.get("οικοπεδο_γηπεδο") or {}
    tabs = []

    # --- Οικόπεδο
    rows = [("Περιφέρεια", "περιφερεια", 0), ("Περιφερειακή Ενότητα", "περιφερειακη_ενοτητα", 0), ("Δήμος", "δημος", 0),
            ("Υ.ΔΟΜ.", "υδομ", 0), ("Περιγραφή Οικοπέδου/Γηπέδου", "περιγραφη", 1), ("Οδός", "οδος", 1),
            ("Αριθμός", "αριθμος", 0), ("Πόλη/Οικισμός", "πολη_οικισμος", 1), ("ΤΚ", "τκ", 1),
            ("Περιοχή/Τοποθεσία", "περιοχη_τοποθεσια", 1), ("ΟΤ", "οτ", 0), ("ΚΑΕΚ Οικοπέδου", "καεκ_οικοπεδου", 0),
            ("Επιφάνεια (τμ)", "επιφανεια_τμ", 1), ("Εντός σχεδίου/οικισμού", "εντος_σχεδιου_οικισμου", 1),
            ("Ειδικό καθεστώς", "ειδικο_καθεστως", 1), ("Διαίρεση Οικοπέδου/Γηπέδου", "διαιρεση_οικοπεδου", 1),
            ("Αδόμητο", "αδομητο", 1), ("Αριθμός κτιρίων", "αριθμος_κτιριων", 1),
            ("Αριθμός Ιδιοκτησιών", "αριθμος_ιδιοκτησιων", 1), ("Κοινόχρηστοι χώροι", "κοινοχρηστοι_χωροι", 0),
            ("Σχόλια", "σχολια", 0), ("Όροφοι", "οροφοι", 0)]
    tabs.append(("Οικόπεδο", "".join(pedio(l, o.get(k), r) for l, k, r in rows)))

    # --- Γεωχωρικά
    geo = o.get("γεωχωρικες_συντεταγμενες_εγσα87") or {}
    kor = lista(geo.get("κορυφες"))
    s = ",".join(f"{k.get('Χ', '')} {k.get('Υ', '')}" for k in kor)
    g_html = pedio("Γεωχωρικές συντεταγμένες (μορφή ΤΕΕ: X Y,X Y,…)", s)
    g_html += pinakas([("#", "#"), ("Χ (ΕΓΣΑ87)", "Χ"), ("Υ (ΕΓΣΑ87)", "Υ")],
                      [{"#": str(i), **k} for i, k in enumerate(kor, 1)])
    if geo.get("πηγη"):
        g_html += f'<p class="note">Πηγή: {E(geo["πηγη"])} · κανόνας 1:1 (X→X, Y→Y)</p>'
    tabs.append(("Γεωχωρικά", g_html))

    for i, idk in enumerate(lista(d.get("ιδιοκτησιες")), 1):
        p = f"Ιδ.{i} · " if len(lista(d.get("ιδιοκτησιες"))) > 1 else ""
        st = idk.get("στοιχεια_ιδιοκτησιας") or {}
        rows = [("Τύπος Ιδιοκτησίας", "τυπος_ιδιοκτησιας", 1), ("Περιγραφή Ιδιοκτησίας", "περιγραφη", 1),
                ("Υλοποιημένη Ιδιοκτησία", "υλοποιημενη_ιδιοκτησια", 0), ("ΚΑΕΚ Ιδιοκτησίας", "καεκ_ιδιοκτησιας", 0),
                ("Χιλιοστά επί του Οικοπέδου/Γηπέδου", "χιλιοστα_επι_οικοπεδου", 0),
                ("Αριθμός/Έτος Συμβολαίου", "αριθμος_ετος_συμβολαιου", 0), ("Στοιχεία Εκδότη", "στοιχεια_εκδοτη", 0),
                ("Αριθμός θέσεων στάθμευσης", "αριθμος_θεσεων_σταθμευσης", 1), ("Αιτιολογία", "αιτιολογια_καταχωρισης", 1),
                ("Τεχνική περιγραφή", "τεχνικη_περιγραφη", 0)]
        tabs.append((p + "Στοιχεία Ιδιοκτησίας",
                     pedio("Κωδικός Ιδιοκτησίας", idk.get("κωδικος_ιδιοκτησιας")) +
                     "".join(pedio(l, st.get(k) if k != "στοιχεια_εκδοτη" else (st.get(k) or st.get("στοιχεια_συμβολαιογραφου")), r)
                             for l, k, r in rows)))

        yp = lista(idk.get("υποχρεοι"))
        tabs.append((p + "Υπόχρεος", pinakas(
            [("Ιδιότητα", "ιδιοτητα"), ("Ποσοστό", "ποσοστο"), ("Επώνυμο", "επωνυμο"), ("Όνομα", "ονομα"),
             ("Όνομα πατέρα", "ονομα_πατερα"), ("Υπόχρεος", "υποχρεος"), ("Διεύθυνση", "διευθυνση"), ("Πόλη", "πολη"),
             ("ΤΚ", "τκ"), ("Τηλέφωνο", "τηλεφωνο"), ("Κινητό", "κινητο"), ("email", "email"), ("ΑΦΜ", "αφμ"),
             ("ΑΦΜ εξωτερικού", "αφμ_εξωτερικου"), ("ΑΔΤ", "αδτ")], yp) +
            "<h3>Συμμετέχοντες μηχανικοί</h3>" +
            pinakas([("ΑΜ ΤΕΕ", "αμ_τεε"), ("Στοιχεία μέλους", "ονοματεπωνυμο")], lista(idk.get("συμμετεχοντες_μηχανικοι")))))

        pr = lista(idk.get("πραξεις"))
        stat = []
        for x in pr:
            for g in lista(x.get("στατικος_ελεγχος")):
                stat.append({"πραξη": f"{x.get('τυπος_πραξης', '')} {x.get('αα_πραξης', '')}", **g})
        tabs.append((p + "Πράξεις", pinakas(
            [("Τύπος πράξης", "τυπος_πραξης"), ("Α/Α πράξης", "αα_πραξης"), ("Ημ/νία έκδοσης", "ημ_εκδοσης"),
             ("Τίτλος πράξης", "τιτλος_πραξης"), ("Εκδούσα Αρχή", "εκδουσα_αρχη"),
             ("Στοιχεία Εκδούσας Αρχής", "στοιχεια_εκδουσας_αρχης"), ("Πρόσθετα Στοιχεία", "προσθετα_στοιχεια")], pr) +
            "<h3>Στατικός έλεγχος</h3>" +
            pinakas([("Πράξη", "πραξη"), ("Τύπος στατικού ελέγχου", "τυπος"), ("Αποτέλεσμα ελέγχου", "αποτελεσμα"),
                     ("Κατάσταση", "κατασταση")], stat)))

        ef = lista(idk.get("επιφανειες"))
        sk = lambda key: gr(sum(num(r.get(key)) for r in ef))
        sp = lambda key: gr(sum(num((r.get("θεσεις_σταθμευσης") or {}).get(key)) for r in ef))
        tabs.append((p + "Επιφάνειες", pinakas(
            [("Πράξη", "πραξη"), ("Όροφος", "οροφος"), ("Είδος επιπέδου", "ειδος_επιπεδου"),
             ("Κύριας Χρήσης", "χωρος_κυριας_χρησης_τμ"), ("Βοηθητικής Χρήσης", "χωρος_βοηθητικης_χρησης_τμ"),
             ("Ημιυπαίθριοι", "ημιυπαιθριοι_τμ"), ("Pilotis", "pilotis_τμ"), ("Λοιποί Χώροι", "λοιποι_χωροι_τμ"),
             ("Υπαίθριες Θ.Σ.", lambda r: (r.get("θεσεις_σταθμευσης") or {}).get("υπαιθριες_τμ")),
             ("Κλειστές Θ.Σ.", lambda r: (r.get("θεσεις_σταθμευσης") or {}).get("κλειστες_τμ")),
             ("Στεγασμένες Θ.Σ.", lambda r: (r.get("θεσεις_σταθμευσης") or {}).get("στεγασμενες_τμ")),
             ("Σχόλια", "σχολια")], ef,
            ["Σύνολα", "", "", sk("χωρος_κυριας_χρησης_τμ"), sk("χωρος_βοηθητικης_χρησης_τμ"), sk("ημιυπαιθριοι_τμ"),
             sk("pilotis_τμ"), sk("λοιποι_χωροι_τμ"), sp("υπαιθριες_τμ"), sp("κλειστες_τμ"), sp("στεγασμενες_τμ"), ""])))

        xr = lista(idk.get("χρησεις"))
        tabs.append((p + "Χρήσεις", pinakas(
            [("Είδος χρήσης", "ειδος_χρησης"), ("Περιγραφή", "περιγραφη"), ("Εμβαδό (τμ)", "εμβαδο_τμ"),
             ("Όροφος", "οροφος"), ("Είδος επιπέδου", "ειδος_επιπεδου")], xr,
            ["Σύνολο", "", gr(sum(num(r.get("εμβαδο_τμ")) for r in xr)), "", ""])))

        tabs.append((p + "Π.Ε.Α.-Δίκτυα", "<h3>Π.Ε.Α.</h3>" + pinakas(
            [("Αρ. πρωτοκόλλου", "αρ_πρωτοκολλου"), ("Ημ/νία έκδοσης", "ημ_εκδοσης"), ("Αρ. Ασφαλείας", "αρ_ασφαλειας"),
             ("Κατηγορία", "κατηγορια"), ("Ετήσια κατανάλωση κτιρίου", "ετησια_καταναλωση_κτιριου"),
             ("Ετήσιες εκπομπές CO2", "ετησιες_εκπομπες_co2")], lista(idk.get("πεα"))) +
            "<h3>Στοιχεία Δικτύων</h3>" + pinakas(
            [("Δίκτυο", "δικτυο"), ("Περιγραφή", "περιγραφη"), ("Αρ. μετρητή", "αρ_μετρητη"),
             ("Αρ. παροχής", lambda r: r.get("αρ_παροχης") or r.get("αρ_παροχης_λογαριασμου"))], lista(idk.get("δικτυα")))))

        eg = idk.get("εγγραφα") or {}
        h = ""
        for kat, et in [("εγγραφα_πραξεων", "Έγγραφα πράξεων"), ("εγγραφα_πεα", "Έγγραφα Π.Ε.Α."), ("γενικα_εγγραφα", "Γενικά έγγραφα")]:
            items = eg.get(kat) or []
            li = []
            for it in items:
                if isinstance(it, str):
                    li.append(f"<li><input type=checkbox> {E(it)}</li>")
                elif isinstance(it, dict) and any(it.values()):
                    t = " · ".join(E(str(it.get(k))) for k in ("πραξη", "τυπος_εγγραφου", "αρχειο") if it.get(k))
                    li.append(f"<li><input type=checkbox> {t}</li>")
            h += f"<h3>{et}</h3><ul class='chk'>{''.join(li) or '<li class=none>—</li>'}</ul>"
        tabs.append((p + "Συνημμένα", h + '<p class="note">PDF ≤30 MB/αρχείο · ≤8 αρχεία/αποστολή · σαρώσεις ≥300 dpi · χωρίς crop/κλείδωμα</p>'))

    if a.elegxoi and Path(a.elegxoi).exists():
        r = json.loads(Path(a.elegxoi).read_text(encoding="utf-8"))
        cls = {"ΣΦΑΛΜΑ": "err", "ΑΣΥΜΦΩΝΙΑ": "dis", "ΠΡΟΕΙΔΟΠΟΙΗΣΗ": "warn", "ΟΚ": "ok"}
        s = r.get("συνοψη", {})
        h = "<div class='sum'>" + "".join(f"<span class='b {cls[k]}'>{E(k)} {s.get(k, 0)}</span>" for k in cls) + "</div>"
        h += "<div class='tw'><table><thead><tr><th>Επίπεδο</th><th>Καρτέλα</th><th>Πεδίο</th><th>Εύρημα</th><th>Υπολογισμός</th></tr></thead><tbody>"
        for x in r.get("ευρηματα", []):
            sov = f"[{x['σοβαροτητα']}] " if x.get("σοβαροτητα") else ""
            h += (f"<tr class='{cls.get(x['επιπεδο'], '')}'><td>{E(x['επιπεδο'])}</td><td>{E(x['καρτελα'])}</td>"
                  f"<td>{E(x['πεδιο'])}</td><td>{E(sov + x['μηνυμα'])}</td><td>{E(x.get('υπολογισμος') or '')}</td></tr>")
        h += "</tbody></table></div>"
        if r.get("παραδοχες"):
            h += "<h3>Παραδοχές</h3><ol>" + "".join(f"<li>{E(p)}</li>" for p in r["παραδοχες"]) + "</ol>"
        n_bad = s.get("ΣΦΑΛΜΑ", 0) + s.get("ΑΣΥΜΦΩΝΙΑ", 0)
        tabs.append((f"Έλεγχοι ({n_bad})" if n_bad else "Έλεγχοι", h))

    titlos = meta.get("υποθεση") or "Υπόθεση ΗΤΚ"
    nav = "".join(f'<button class="t{" on" if i == 0 else ""}" data-i="{i}">{E(t)}</button>' for i, (t, _) in enumerate(tabs))
    panes = "".join(f'<section class="p{" on" if i == 0 else ""}" data-i="{i}">{c}</section>' for i, (_, c) in enumerate(tabs))
    out = TEMPLATE.replace("%TITLE%", E(titlos)).replace("%KAEK%", E(str(o.get("καεκ_οικοπεδου", "")))) \
        .replace("%NAV%", nav).replace("%PANES%", panes)
    Path(a.out).write_text(out, encoding="utf-8")
    print(f"Φύλλο Συμπλήρωσης: {a.out} ({len(tabs)} καρτέλες)")


TEMPLATE = """<!doctype html>
<html lang="el"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Φύλλο Συμπλήρωσης ΗΤΚ</title>
<style>
:root{--bg:#121519;--pn:#1a1e24;--ln:#2a3038;--tx:#e4e7eb;--mu:#8b949e;--or:#ff8a3d;--te:#2ec4b6;--er:#ff5d5d;--wa:#e3b341;--ok:#3fb950}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.45 "IBM Plex Sans","Segoe UI",system-ui,sans-serif}
header{padding:14px 16px;border-bottom:1px solid var(--ln);display:flex;flex-wrap:wrap;gap:6px 18px;align-items:baseline}
header h1{margin:0;font-size:17px;font-weight:600}header .k{color:var(--te);font-family:"IBM Plex Mono",Consolas,monospace}
header .h{color:var(--mu);font-size:12px;margin-left:auto}
nav{display:flex;gap:4px;padding:8px 16px;overflow-x:auto;border-bottom:1px solid var(--ln);position:sticky;top:0;background:var(--bg);z-index:2}
nav .t{background:var(--pn);color:var(--mu);border:1px solid var(--ln);border-radius:6px;padding:6px 10px;cursor:pointer;white-space:nowrap;font:inherit}
nav .t.on{color:var(--bg);background:var(--or);border-color:var(--or);font-weight:600}
main{padding:16px;max-width:1400px}section.p{display:none}section.p.on{display:block}
.f{display:grid;grid-template-columns:minmax(140px,260px) 1fr auto;gap:10px;align-items:start;padding:7px 10px;border-bottom:1px solid var(--ln);background:var(--pn)}
.f label{color:var(--mu)}.f .v{white-space:pre-wrap;word-break:break-word;font-family:"IBM Plex Mono",Consolas,monospace;font-size:13px}
.f.empty .v{color:#555}.ast{color:var(--or);margin-left:2px}
.cp{background:transparent;border:1px solid var(--ln);color:var(--te);border-radius:5px;cursor:pointer;padding:2px 8px;font-size:14px}
.cp:hover{border-color:var(--te)}.cp.done,.c.done{background:var(--te);color:var(--bg)}
h3{color:var(--or);font-size:14px;margin:18px 0 6px}
.tw{overflow-x:auto;border:1px solid var(--ln);border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:13px}th{background:#202630;color:var(--mu);font-weight:500;text-align:left;padding:6px 8px;white-space:nowrap}
td{padding:6px 8px;border-top:1px solid var(--ln);vertical-align:top}td.c{cursor:copy;font-family:"IBM Plex Mono",Consolas,monospace}td.c:hover{background:#243040}
tr.tot td{color:var(--te);font-weight:600}td.none{color:#555;text-align:center}
.note{color:var(--mu);font-size:12px}ul.chk{list-style:none;padding:0}ul.chk li{padding:4px 0}
.sum{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}.b{padding:4px 10px;border-radius:12px;font-weight:600;font-size:12px}
.b.err{background:#3a1717;color:var(--er)}.b.dis{background:#3a2614;color:var(--or)}.b.warn{background:#33290f;color:var(--wa)}.b.ok{background:#12301a;color:var(--ok)}
tr.err td:first-child{color:var(--er)}tr.dis td:first-child{color:var(--or)}tr.warn td:first-child{color:var(--wa)}tr.ok td:first-child{color:var(--ok)}
@media(max-width:640px){.f{grid-template-columns:1fr auto}.f label{grid-column:1/-1}}
</style></head><body>
<header><h1>%TITLE%</h1><span class="k">ΚΑΕΚ %KAEK%</span><span class="h">Κλικ σε ⧉ ή σε κελί = αντιγραφή · Ο έλεγχος και η υποβολή στο ΤΕΕ γίνονται από τον μηχανικό</span></header>
<nav>%NAV%</nav><main>%PANES%</main>
<script>
document.querySelectorAll('nav .t').forEach(b=>b.onclick=()=>{document.querySelectorAll('.on').forEach(x=>x.classList.remove('on'));
b.classList.add('on');document.querySelector('section.p[data-i="'+b.dataset.i+'"]').classList.add('on');});
function cp(t,el){const ok=()=>{el.classList.add('done');setTimeout(()=>el.classList.remove('done'),700)};
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(ok,()=>fb(t,ok))}else fb(t,ok)}
function fb(t,ok){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');ok()}catch(e){}a.remove()}
document.addEventListener('click',e=>{const b=e.target.closest('.cp');if(b){cp(b.previousElementSibling.dataset.v,b);return}
const c=e.target.closest('td.c');if(c)cp(c.dataset.v,c)});
</script></body></html>"""

if __name__ == "__main__":
    main()
