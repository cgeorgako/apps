#!/usr/bin/env python3
"""Υπεύθυνες δηλώσεις εξουσιοδότησης ιδιοκτήτη προς μηχανικό για την ΗΤΚ (ν.1599/1986, άρθρο 8).

Παράγει από το πρότυπο του γραφείου (templates/yd_exousiodotisis.docx) ένα .docx ανά ιδιοκτήτη
και ανά μηχανικό, συμπληρώνοντας τα placeholders από το JSON της υπόθεσης. Δεν αλλάζει το
κείμενο ή τη μορφοποίηση του εντύπου. Ό,τι δεν υπάρχει στο JSON μένει ΚΕΝΟ και αναφέρεται.

Χρήση:
    python3 -I yd_exousiodotisis.py υπόθεση.json --mixanikos georgakopoulos|fountas|both --out φάκελος
        [--idioktisia 1] [--idioktes 1,2] [--imerominia 17/11/2026] [--pdf]

Πεδία JSON που διαβάζονται:
  εξουσιοδοτηση.περιγραφη_ακινητου   (υποχρεωτικό)  ·  εξουσιοδοτηση.ημερομηνια / .προς (προαιρετικά)
  οικοπεδο_γηπεδο.επιφανεια_τμ       (για έλεγχο εμβαδού στην περιγραφή)
  ιδιοκτησιες[i].υποχρεοι[]: ιδιοτητα, ποσοστο, επωνυμο, ονομα, ονομα_πατερα, ονομα_μητερας,
      ημ_γεννησης, τοπος_γεννησης, αδτ, αφμ, κινητο|τηλεφωνο, τοπος_κατοικιας|πολη,
      οδος_κατοικιας, αριθμος_κατοικιας, τκ, email
Μηχανικοί: references/mixanikoi.json.
"""
import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from docx import Document

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "templates" / "yd_exousiodotisis.docx"
REGISTRY = SKILL / "references" / "mixanikoi.json"

KYRIOI = ("ΠΛΗΡΗΣ ΚΥΡΙΟΣ", "ΨΙΛΟΣ ΚΥΡΙΟΣ", "ΕΠΙΚΑΡΠΩΤΗΣ")
KENA_ETIKETES = [("ΟΝΟΜΑ", "Όνομα"), ("ΕΠΩΝΥΜΟ", "Επώνυμο"), ("ΠΑΤΕΡΑΣ", "Όνομα πατέρα"), ("ΜΗΤΕΡΑ", "Όνομα μητέρας"),
                 ("ΗΜ_ΓΕΝΝΗΣΗΣ", "Ημερομηνία γέννησης"), ("ΤΟΠΟΣ_ΓΕΝΝΗΣΗΣ", "Τόπος γέννησης"),
                 ("ΑΔΤ", "Αριθμός Δελτίου Ταυτότητας"), ("ΤΗΛΕΦΩΝΟ", "Τηλέφωνο"),
                 ("ΤΟΠΟΣ_ΚΑΤΟΙΚΙΑΣ", "Τόπος κατοικίας"), ("ΤΚ", "ΤΚ"), ("ΑΦΜ", "ΑΦΜ"), ("EMAIL", "Email")]


def kanoniko(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", s).upper().strip()


def katharo(v):
    """Κείμενο σε μία γραμμή, χωρίς χαρακτήρες ελέγχου."""
    v = "" if v is None else str(v)
    v = re.sub(r"[\x00-\x08\x0b-\x1f]", "", v)
    return re.sub(r"\s+", " ", v).strip()


def num(v):
    s = katharo(v).replace("€", "").replace("τ.μ.", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def afm_ok(a):
    a = re.sub(r"\D", "", str(a))
    if len(a) != 9:
        return False
    return (sum(int(a[i]) * 2 ** (8 - i) for i in range(8)) % 11) % 10 == int(a[8])


def imerominia_ok(s):
    m = re.fullmatch(r"\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\s*", str(s))
    if not m:
        return False
    try:
        dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return True
    except ValueError:
        return False


def fatal(msg):
    print(f"ΣΦΑΛΜΑ: {msg}", file=sys.stderr)
    sys.exit(2)


def epilogi_mixanikon(timi, reg):
    ep = katharo(timi).lower()
    if ep in ("both", "oloi", "dyo", "οι δύο", "οι δυο", "και οι δύο", "και οι δυο"):
        return list(k for k in reg if not k.startswith("_"))
    out = []
    for tok in re.split(r"[,;+]| και ", ep):
        tok = tok.strip()
        if not tok:
            continue
        key = next((k for k, v in reg.items() if not k.startswith("_") and (tok == k or tok in v.get("συνωνυμα", []))), None)
        if key is None:
            fatal(f"Άγνωστος μηχανικός «{tok}». Διαθέσιμοι: {', '.join(k for k in reg if not k.startswith('_'))}, both")
        if key not in out:
            out.append(key)
    if not out:
        fatal("Δεν ορίστηκε μηχανικός (--mixanikos)")
    return out


def poso_keimeno(u, warns):
    idio = kanoniko(u.get("ιδιοτητα", ""))
    v = katharo(u.get("ποσοστο", ""))
    if not v:
        warns.append("Δεν υπάρχει ποσοστό — το πεδίο μένει «Π.Κ.%»")
        v = ""
    if "/" in v:
        pct = v
    else:
        n = re.sub(r"[%\s]", "", v)
        if re.fullmatch(r"\d+\.\d+", n):
            n = n.replace(".", ",")
        n = re.sub(r",0+$", "", n)
        pct = n + "%"
    if idio == "ΠΛΗΡΗΣ ΚΥΡΙΟΣ":
        return "Π.Κ." + pct
    eti = katharo(u.get("ιδιοτητα", "")) or "κύριος"
    warns.append(f"Ιδιότητα «{eti}»: γράφτηκε ολογράφως — το πρότυπο του γραφείου έχει μόνο τη συντομογραφία Π.Κ.")
    return f"{eti} {pct}"


def timi_pediou(u, *kleidia):
    for k in kleidia:
        v = katharo(u.get(k, ""))
        if v:
            return v
    return ""


def pedia_idioktiti(u, ex, warns):
    tel = timi_pediou(u, "κινητο", "τηλεφωνο")
    m = {
        "ΠΡΟΣ": katharo(ex.get("προς")) or "Τ.Ε.Ε.",
        "ΟΝΟΜΑ": timi_pediou(u, "ονομα"),
        "ΕΠΩΝΥΜΟ": timi_pediou(u, "επωνυμο"),
        "ΠΑΤΕΡΑΣ": timi_pediou(u, "ονομα_πατερα"),
        "ΜΗΤΕΡΑ": timi_pediou(u, "ονομα_μητερας"),
        "ΗΜ_ΓΕΝΝΗΣΗΣ": timi_pediou(u, "ημ_γεννησης"),
        "ΤΟΠΟΣ_ΓΕΝΝΗΣΗΣ": timi_pediou(u, "τοπος_γεννησης"),
        "ΑΔΤ": timi_pediou(u, "αδτ"),
        "ΤΗΛΕΦΩΝΟ": tel,
        "ΤΟΠΟΣ_ΚΑΤΟΙΚΙΑΣ": timi_pediou(u, "τοπος_κατοικιας", "πολη"),
        "ΟΔΟΣ": timi_pediou(u, "οδος_κατοικιας"),
        "ΑΡΙΘΜΟΣ": timi_pediou(u, "αριθμος_κατοικιας"),
        "ΤΚ": timi_pediou(u, "τκ"),
        "ΑΦΜ": timi_pediou(u, "αφμ", "αφμ_εξωτερικου"),
        "EMAIL": timi_pediou(u, "email"),
        "ΠΟΣΟΣΤΟ": poso_keimeno(u, warns),
    }
    if m["ΑΦΜ"] and katharo(u.get("αφμ")) and not afm_ok(m["ΑΦΜ"]):
        warns.append(f"ΑΦΜ {m['ΑΦΜ']}: αποτυγχάνει στον έλεγχο ψηφίου — έλεγξε την ανάγνωση")
    if m["ΗΜ_ΓΕΝΝΗΣΗΣ"] and not imerominia_ok(m["ΗΜ_ΓΕΝΝΗΣΗΣ"]):
        warns.append(f"Ημερομηνία γέννησης «{m['ΗΜ_ΓΕΝΝΗΣΗΣ']}»: μη έγκυρη μορφή (ηη/μμ/εεεε)")
    return m


def elegxos_perigrafis(perigrafi, epifaneia, warns):
    """Αν η περιγραφή αφορά γεωτεμάχιο/οικόπεδο, το εμβαδόν της πρέπει να ταυτίζεται με το επιβεβαιωμένο."""
    if not re.match(r"\s*(Γεωτεμάχιο|Οικόπεδο|Γήπεδο|Αγρός)", perigrafi, re.I):
        return
    m = re.search(r"εμβαδ(?:ού|ου|όν|ον)\s+([\d.,]+)\s*τ", perigrafi, re.I)
    ep = num(epifaneia)
    if not m or ep is None:
        return
    st = num(m.group(1))
    if st is not None and abs(st - ep) > 0.005:
        warns.append(f"ΕΜΒΑΔΟΝ: η περιγραφή γράφει {m.group(1)} τ.μ. αλλά το επιβεβαιωμένο εμβαδόν της υπόθεσης είναι "
                     f"{epifaneia} τ.μ. — η δήλωση δεν πρέπει να υπογραφεί πριν ταυτιστούν")


def symplirosi(doc, mapping):
    """Αντικατάσταση {{ΤΟΚΕΝ}} μέσα σε runs — μόνο το κείμενο, η μορφοποίηση του run μένει."""
    def paragraphs():
        for p in doc.paragraphs:
            yield p
        for t in doc.tables:
            for row in t.rows:
                for c in row.cells:
                    yield from c.paragraphs
        for s in doc.sections:
            for part in (s.header, s.footer):
                yield from part.paragraphs
    for p in paragraphs():
        for r in p.runs:
            if "{{" in r.text:
                tx = r.text
                for k, v in mapping.items():
                    tx = tx.replace("{{" + k + "}}", v)
                r.text = tx


def leipoun_tokens(path):
    import zipfile
    with zipfile.ZipFile(path) as z:
        return sorted({t for n in z.namelist() if n.endswith(".xml") for t in re.findall(r"\{\{[^}]*\}\}", z.read(n).decode("utf-8", "ignore"))})


def selides_via_pdf(docx_path, keep_pdf_to=None):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(docx_path)],
                           capture_output=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired):
            return None
        pdf = Path(td) / (Path(docx_path).stem + ".pdf")
        if not pdf.exists():
            return None
        raw = pdf.read_bytes()
        n = len(re.findall(rb"/Type\s*/Page[^s]", raw))
        if keep_pdf_to:
            shutil.copy(pdf, keep_pdf_to)
        return n or None


def onoma_arxeiou(u, eng):
    base = "_".join(x for x in (katharo(u.get("επωνυμο")), katharo(u.get("ονομα"))) if x) or "Ιδιοκτήτης"
    s = re.sub(r"[^\w-]+", "_", f"ΥΔ_Εξουσιοδότησης_ΗΤΚ_{base}_{eng['αρχειο']}", flags=re.U)
    return re.sub(r"_+", "_", s).strip("_") + ".docx"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_ypothesis")
    ap.add_argument("--mixanikos", required=True, help="georgakopoulos | fountas | both (ή κλειδιά με κόμμα)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--idioktisia", type=int, default=1, help="ποια ιδιοκτησία του JSON (1-based, προεπιλογή 1)")
    ap.add_argument("--idioktes", default="all", help="all ή αριθμοί ιδιοκτητών με κόμμα, π.χ. 1,2")
    ap.add_argument("--imerominia", help="ηη/μμ/εεεε· χωρίς αυτήν η ημερομηνία μένει κενή")
    ap.add_argument("--pdf", action="store_true", help="κράτα και PDF δίπλα στο .docx")
    a = ap.parse_args()

    if not TEMPLATE.exists():
        fatal(f"Λείπει το πρότυπο {TEMPLATE}")
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    engs = epilogi_mixanikon(a.mixanikos, reg)
    case = json.loads(Path(a.json_ypothesis).read_text(encoding="utf-8"))
    ex = case.get("εξουσιοδοτηση") or {}
    perigrafi = katharo(ex.get("περιγραφη_ακινητου"))
    if not perigrafi:
        fatal("Λείπει το εξουσιοδοτηση.περιγραφη_ακινητου (π.χ. «Γεωτεμάχιο εμβαδού 1234,56 τ.μ. με ισόγεια κατοικία …»)")
    imer = katharo(a.imerominia or ex.get("ημερομηνια"))
    if imer and not imerominia_ok(imer):
        fatal(f"Μη έγκυρη ημερομηνία «{imer}» (ηη/μμ/εεεε)")

    idks = [x for x in (case.get("ιδιοκτησιες") or []) if isinstance(x, dict)]
    if not (1 <= a.idioktisia <= len(idks)):
        fatal(f"Δεν υπάρχει ιδιοκτησία {a.idioktisia} (το JSON έχει {len(idks)})")
    ypoxreoi = [u for u in (idks[a.idioktisia - 1].get("υποχρεοι") or []) if isinstance(u, dict)]
    kyrioi = [(i, u) for i, u in enumerate(ypoxreoi, 1) if kanoniko(u.get("ιδιοτητα", "")) in KYRIOI]
    paraleipomenoi = [f"{katharo(u.get('επωνυμο'))} {katharo(u.get('ονομα'))} ({katharo(u.get('ιδιοτητα')) or 'χωρίς ιδιότητα'})"
                      for i, u in enumerate(ypoxreoi, 1) if (i, u) not in kyrioi]
    if a.idioktes != "all":
        try:
            zita = {int(x) for x in a.idioktes.split(",")}
        except ValueError:
            fatal("--idioktes: αριθμοί με κόμμα ή all")
        kyrioi = [(i, u) for i, u in kyrioi if i in zita]
    if not kyrioi:
        fatal("Δεν βρέθηκε ιδιοκτήτης (ιδιότητα πλήρης/ψιλός κύριος ή επικαρπωτής) στις υποχρεοι")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    apotelesma, genikes = [], []
    if paraleipomenoi:
        genikes.append("Δεν παράχθηκε δήλωση για (δεν είναι κύριοι/επικαρπωτές): " + "; ".join(paraleipomenoi))

    for i, u in kyrioi:
        for ek in engs:
            eng = reg[ek]
            warns = []
            m = pedia_idioktiti(u, ex, warns)
            elegxos_perigrafis(perigrafi, (case.get("οικοπεδο_γηπεδο") or {}).get("επιφανεια_τμ"), warns)
            m.update({"ΑΚΙΝΗΤΟ": perigrafi, "ΜΗΧΑΝΙΚΟΣ": eng["ονομα_αιτιατικη"], "ΕΙΔΙΚΟΤΗΤΑ": eng["ειδικοτητα"],
                      "ΑΜ_ΤΕΕ": eng["αμ_τεε"], "ΗΜΕΡΟΜΗΝΙΑ": imer})
            m = {k: katharo(v) for k, v in m.items()}
            kena = [et for tok, et in KENA_ETIKETES if not m.get(tok)]
            doc = Document(str(TEMPLATE))
            symplirosi(doc, m)
            path = out / onoma_arxeiou(u, eng)
            doc.save(str(path))
            upoloipa = leipoun_tokens(path)
            if upoloipa:
                fatal(f"Έμειναν placeholders στο {path.name}: {upoloipa}")
            sel = selides_via_pdf(path, path.with_suffix(".pdf") if a.pdf else None)
            if sel and sel > 1:
                warns.append(f"Το έγγραφο βγήκε {sel} σελίδες (το έντυπο είναι μονοσέλιδο) — συντόμευσε την περιγραφή ακινήτου")
            apotelesma.append({"αρχειο": path.name, "ιδιοκτητης": f"{m['ΕΠΩΝΥΜΟ']} {m['ΟΝΟΜΑ']}".strip(), "αριθμος_ιδιοκτητη": i,
                               "προς": eng["ονοματεπωνυμο"], "αμ_τεε": eng["αμ_τεε"], "σελιδες": sel,
                               "κενα_πεδια": kena, "προειδοποιησεις": warns})

    (out / "yd_apotelesma.json").write_text(json.dumps({"αρχεια": apotelesma, "γενικα": genikes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Υπεύθυνες δηλώσεις εξουσιοδότησης: {len(apotelesma)} αρχεία → {out}")
    print("| # | Αρχείο | Ιδιοκτήτης | Προς (ΑΜ ΤΕΕ) | Σελ. | Κενά πεδία |")
    print("|---|---|---|---|---|---|")
    for n, r in enumerate(apotelesma, 1):
        print(f"| {n} | {r['αρχειο']} | {r['ιδιοκτητης']} | {r['προς']} ({r['αμ_τεε']}) | {r['σελιδες'] or '—'} | {', '.join(r['κενα_πεδια']) or '—'} |")
    print(f"\nΗμερομηνία: {imer or 'ΚΕΝΗ — συμπληρώνεται κατά την υπογραφή'}")
    for g in genikes:
        print(f"ΠΡΟΣΟΧΗ: {g}")
    for r in apotelesma:
        for w in r["προειδοποιησεις"]:
            print(f"ΠΡΟΣΟΧΗ [{r['αρχειο']}]: {w}")


if __name__ == "__main__":
    main()
