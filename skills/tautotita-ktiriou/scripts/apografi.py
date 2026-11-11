#!/usr/bin/env python3
"""Απογραφή φακέλου ΗΤΚ.

Για κάθε PDF/εικόνα: σελίδες, αν έχει στρώμα κειμένου ή είναι σάρωση, πιθανός τύπος
εγγράφου. Σώζει το κείμενο σε <out>/txt και τις σαρωμένες σελίδες ως PNG σε <out>/img.
Στο τέλος δίνει τι λείπει σε σχέση με τη λίστα πληρότητας (references/eggrafa.md §Δ).

Χρήση:
    python3 -I apografi.py <αρχεία ή φάκελοι...> --out <φάκελος> [--dpi 150] [--no-img]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

EXT_PDF = {".pdf"}
EXT_IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# (κωδικός, περιγραφή, μοτίβα κειμένου, μοτίβα ονόματος αρχείου). Η σειρά μετράει.
TYPOI = [
    ("KF", "Κτηματολογικό Φύλλο", [r"ΑΠΟΣΠΑΣΜΑ ΠΕΡΙΓΡΑΦΙΚΗΣ ΒΑΣΗΣ", r"ΚΤΗΜΑΤΟΛΟΓΙΚΟ ΦΥΛΛΟ"], [r"(^|[-_])KF([-_.]|$)"]),
    ("KD", "Απόσπασμα Χωρικής Βάσης", [r"ΑΠΟΣΠΑΣΜΑ ΧΩΡΙΚΗΣ ΒΑΣΗΣ", r"ΚΤΗΜΑΤΟΛΟΓΙΚΟΥ ΔΙΑΓΡΑΜΜΑΤΟΣ"], [r"(^|[-_])KD([-_.]|$)"]),
    ("ΠΕΑ", "Πιστοποιητικό Ενεργειακής Απόδοσης", [r"ΠΙΣΤΟΠΟΙΗΤΙΚΟ ΕΝΕΡΓΕΙΑΚΗΣ ΑΠΟΔΟΣΗΣ"], [r"PEA", r"ΠΕΑ"]),
    ("ΔΗΛΩΣΗ", "Δήλωση αυθαιρέτου (βεβαίωση περαίωσης/υπαγωγής)", [r"ΒΕΒΑΙΩΣΗ ΠΕΡΑΙΩΣΗΣ", r"A/A ΔΗΛΩΣΗΣ", r"Α/Α ΔΗΛΩΣΗΣ", r"ΔΗΛΩΣΗ ΥΠΑΓΩΓΗΣ"], [r"DILOSI", r"ΔΗΛΩΣΗ"]),
    ("ΤΕΧΝ_ΕΚΘΕΣΗ", "Τεχνική έκθεση", [r"ΤΕΧΝΙΚΗ ΕΚΘΕΣΗ"], [r"EKTHESI", r"ΕΚΘΕΣΗ"]),
    ("ΕΞΟΥΣΙΟΔΟΤΗΣΗ", "Υ.Δ. εξουσιοδότησης υπόχρεου", [r"ΥΠΕΥΘΥΝΗ ΔΗΛΩΣΗ.*ΕΞΟΥΣΙΟΔΟΤ", r"ΕΞΟΥΣΙΟΔΟΤ.*ΤΑΥΤΟΤΗΤΑΣ ΚΤΙΡΙΟΥ"], [r"EXOUSIODOT", r"ΕΞΟΥΣΙΟΔΟΤ"]),
    ("ΑΔΕΙΑ", "Οικοδομική άδεια / άδεια δόμησης", [r"ΑΔΕΙΑ ΟΙΚΟΔΟΜΗΣ", r"ΑΔΕΙΑ ΔΟΜΗΣΗΣ", r"ΟΙΚΟΔΟΜΙΚΗ ΑΔΕΙΑ"], [r"ADEIA", r"ΑΔΕΙΑ"]),
    ("ΧΙΛΙΟΣΤΑ", "Πίνακας χιλιοστών", [r"ΠΙΝΑΚΑΣ ΧΙΛΙΟΣΤΩΝ"], [r"XILIOST", r"ΧΙΛΙΟΣΤ"]),
    ("ΣΥΜΒΟΛΑΙΟ", "Συμβόλαιο / σύσταση", [r"ΣΥΣΤΑΣΗ ΟΡΙΖΟΝΤΙ", r"ΣΥΣΤΑΣΗ ΚΑΘΕΤ", r"ΣΥΜΒΟΛΑΙΟΓΡΑΦ.*ΠΡΑΞΗ", r"ΑΡΙΘΜΟΣ ΣΥΜΒΟΛΑΙΟΥ"], [r"SYMBOLAIO", r"ΣΥΜΒΟΛΑΙΟ", r"SYSTASI", r"ΣΥΣΤΑΣΗ"]),
    ("ΤΟΠΟΓΡΑΦΙΚΟ", "Τοπογραφικό / διάγραμμα κάλυψης", [r"ΤΟΠΟΓΡΑΦΙΚΟ ΔΙΑΓΡΑΜΜΑ", r"ΔΙΑΓΡΑΜΜΑ ΚΑΛΥΨΗΣ"], [r"TOPO", r"ΤΟΠΟΓΡ", r"KALYPS"]),
    ("ΛΟΓΑΡΙΑΣΜΟΣ", "Λογαριασμός ρεύματος/νερού", [r"ΑΡΙΘΜΟΣ ΠΑΡΟΧΗΣ", r"ΛΟΓΑΡΙΑΣΜΟΣ ΡΕΥΜΑΤΟΣ"], [r"DEI", r"ΔΕΗ", r"LOGARIASMOS"]),
    ("ΠΙΣΤ_ΕΛΕΓΧΟΥ", "Πιστοποιητικό ελέγχου κατασκευής", [r"ΠΙΣΤΟΠΟΙΗΤΙΚΟ ΕΛΕΓΧΟΥ ΚΑΤΑΣΚΕΥΗΣ"], []),
]

PLIROTITA_VASIKA = [
    ("ΕΞΟΥΣΙΟΔΟΤΗΣΗ", "Υπόχρεος και στοιχεία του· επισυνάπτεται πριν την εισαγωγή"),
    ("KF", "ΚΑΕΚ, εμβαδόν, δικαιούχοι, ποσοστά, τίτλος"),
    (("KD", "ΤΟΠΟΓΡΑΦΙΚΟ"), "Κορυφές ΕΓΣΑ87 για τον γεωχωρικό εντοπισμό, εμβαδόν"),
    ("ΑΔΕΙΑ", "Πράξεις, όροφοι, νόμιμα τ.μ. (ή απόδειξη προ 1955)"),
    ("ΣΥΜΒΟΛΑΙΟ", "Αρ./έτος συμβολαίου, συμβολαιογράφος, σύσταση, χιλιοστά (εν μέρει από KF)"),
]
PLIROTITA_PROAIR = [
    ("ΠΕΑ", "Καρτέλα ΠΕΑ"),
    ("ΛΟΓΑΡΙΑΣΜΟΣ", "Δίκτυα: αρ. παροχής"),
]


def kanoniko(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", s).upper()


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return None


def selides_pdf(p: Path) -> int:
    r = run(["pdfinfo", str(p)])
    if r and r.returncode == 0:
        m = re.search(r"^Pages:\s+(\d+)", r.stdout, re.M)
        if m:
            return int(m.group(1))
    return 0


def keimeno_pdf(p: Path) -> str:
    r = run(["pdftotext", "-layout", "-q", str(p), "-"])
    return r.stdout if r and r.returncode == 0 else ""


def taxinomisi(keimeno: str, onoma: str):
    k = kanoniko(keimeno)
    for kod, per, mot_k, _ in TYPOI:
        if any(re.search(m, k, re.S) for m in mot_k):
            return kod, per, "κείμενο"
    o = kanoniko(onoma)
    for kod, per, _, mot_o in TYPOI:
        if any(re.search(m, o) for m in mot_o):
            return kod, per, "όνομα αρχείου"
    return "ΑΓΝΩΣΤΟ", "Προς αναγνώριση με όραση", "—"


def asfales_onoma(p: Path, i: int) -> str:
    base = re.sub(r"[^\w.-]+", "_", p.stem, flags=re.U).strip("_") or "arxeio"
    return f"{i:02d}_{base[:60]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eisodos", nargs="+", help="αρχεία ή φάκελοι")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--no-img", action="store_true", help="να μην αποδοθούν PNG")
    a = ap.parse_args()

    arxeia = []
    for e in a.eisodos:
        p = Path(e)
        if p.is_dir():
            arxeia += sorted(x for x in p.rglob("*") if x.suffix.lower() in EXT_PDF | EXT_IMG)
        elif p.is_file():
            arxeia.append(p)
        else:
            print(f"Δεν βρέθηκε: {e}", file=sys.stderr)

    out = Path(a.out)
    (out / "txt").mkdir(parents=True, exist_ok=True)
    (out / "img").mkdir(parents=True, exist_ok=True)

    apotel = []
    for i, p in enumerate(arxeia, 1):
        onoma = asfales_onoma(p, i)
        eggr = {"αρχειο": str(p), "κωδ": onoma}
        if p.suffix.lower() in EXT_PDF:
            sel = selides_pdf(p)
            txt = keimeno_pdf(p)
            xar = len(re.sub(r"\s", "", txt))
            sarosi = xar < 40 * max(sel, 1)
            (out / "txt" / f"{onoma}.txt").write_text(txt, encoding="utf-8")
            eggr.update(σελιδες=sel, χαρακτηρες_κειμενου=xar, σαρωση=sarosi)
            if sarosi and not a.no_img:
                run(["pdftoppm", "-r", str(a.dpi), "-png", str(p), str(out / "img" / onoma)])
        else:
            txt = ""
            eggr.update(σελιδες=1, χαρακτηρες_κειμενου=0, σαρωση=True)
            if not a.no_img:
                shutil.copy(p, out / "img" / f"{onoma}{p.suffix.lower()}")
        kod, per, vasi = taxinomisi(txt, p.name)
        eggr.update(τυπος=kod, περιγραφη=per, αναγνωριση_απο=vasi)
        apotel.append(eggr)

    vrethikan = {e["τυπος"] for e in apotel}
    agnosta = sum(1 for e in apotel if e["τυπος"] == "ΑΓΝΩΣΤΟ")
    leipoun = []
    for kod, ti in PLIROTITA_VASIKA:
        kodikoi = kod if isinstance(kod, tuple) else (kod,)
        if not vrethikan.intersection(kodikoi):
            leipoun.append({"εγγραφο": " ή ".join(kodikoi), "τι_δινει": ti, "βασικο": True})
    for kod, ti in PLIROTITA_PROAIR:
        if kod not in vrethikan:
            leipoun.append({"εγγραφο": kod, "τι_δινει": ti, "βασικο": False})

    (out / "apografi.json").write_text(
        json.dumps({"εγγραφα": apotel, "λειπουν": leipoun, "αγνωστα": agnosta}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    print("| # | Αρχείο | Σελ. | Κείμενο/Σάρωση | Τύπος | Αναγνώριση από |")
    print("|---|---|---|---|---|---|")
    for i, e in enumerate(apotel, 1):
        ks = "σάρωση" if e["σαρωση"] else f"κείμενο ({e['χαρακτηρες_κειμενου']} χαρ.)"
        print(f"| {i} | {Path(e['αρχειο']).name} | {e['σελιδες']} | {ks} | {e['τυπος']} | {e['αναγνωριση_απο']} |")
    if leipoun:
        print("\nΛείπουν (εφόσον δεν καλύπτονται από τα ΑΓΝΩΣΤΑ):")
        for l in leipoun:
            print(f"- {'[βασικό] ' if l['βασικο'] else ''}{l['εγγραφο']}: {l['τι_δινει']}")
    if agnosta:
        print(f"\n{agnosta} αρχεία ΑΓΝΩΣΤΟΥ τύπου — διάβασέ τα από {out / 'img'} και όρισε τύπο. "
              "Η λίστα «λείπουν» ξαναϋπολογίζεται μετά.")
    print(f"\nΚείμενα: {out / 'txt'}  ·  Εικόνες: {out / 'img'}  ·  JSON: {out / 'apografi.json'}")


if __name__ == "__main__":
    main()
