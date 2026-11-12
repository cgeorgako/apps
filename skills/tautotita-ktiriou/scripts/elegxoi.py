#!/usr/bin/env python3
"""Έλεγχοι επαλήθευσης JSON ΗΤΚ (σχήμα references/schema.json).

Επίπεδα: ΣΦΑΛΜΑ (κανόνας ΤΕΕ/εγχειριδίου ή κενό υποχρεωτικό), ΑΣΥΜΦΩΝΙΑ (έγγραφα
διαφωνούν), ΠΡΟΕΙΔΟΠΟΙΗΣΗ, ΟΚ. Δεν αλλάζει το JSON — μόνο αναφέρει.

Χρήση:
    python3 -I elegxoi.py υπόθεση.json [--md αναφορά.md] [--docx αναφορά.docx]
                         [--json ευρήματα.json] [--mixanikos "Ονοματεπώνυμο"]
                         [--idiotita "Διπλωματούχος Πολιτικός Μηχανικός Ε.Μ.Π."]
                         [--rolos "Ο Συντάξας Μηχανικός"]
"""
import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

SEIRA = ["ΣΦΑΛΜΑ", "ΑΣΥΜΦΩΝΙΑ", "ΠΡΟΕΙΔΟΠΟΙΗΣΗ", "ΟΚ"]
ANOXI = 0.005  # τ.μ. / € — όριο ισότητας

# ----------------------------------------------------------------- βοηθητικά

def num(v):
    """Αριθμός από ελληνική ή διεθνή γραφή: '5.383,74' '5383,74' '245.7' '12.026,70 €'."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(" ", "").replace("€", "")
    s = re.sub(r"(τ\.?μ\.?|m2|kwh/m2|kg/m2|%)$", "", s, flags=re.I)
    if s in ("", "-", "—"):
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def gr(x, d=2):
    if x is None:
        return "—"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def kanoniko(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", s).upper()


def keno(v):
    return v is None or (isinstance(v, str) and v.strip() == "") or v == [] or v == {}


def kathara(o):
    """Αφαιρεί κλειδιά σημειώσεων (_...)."""
    if isinstance(o, dict):
        return {k: kathara(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, list):
        return [kathara(x) for x in o]
    return o


def lista(v):
    if v is None:
        return []
    if isinstance(v, dict):
        return [v] if any(not keno(x) for x in v.values()) else []
    return [x for x in v if isinstance(x, dict) and any(not keno(y) for y in x.values())]


def afm_ok(a):
    a = re.sub(r"\D", "", str(a))
    if len(a) != 9:
        return False
    s = sum(int(a[i]) * 2 ** (8 - i) for i in range(8))
    return (s % 11) % 10 == int(a[8])


def imerominia_ok(s):
    m = re.fullmatch(r"\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\s*", str(s))
    if not m:
        return False
    try:
        dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return True
    except ValueError:
        return False


XARAKTIRES = re.compile(r"^[Α-ΡΣ-Ω .\-]+$")
KAEK = re.compile(r"^\d{12}/\d{1,2}/\d{1,2}$")
AYTHAIRETA = re.compile(r"4178|4495|5306")


# ----------------------------------------------------------------- ευρήματα

class Eyrimata:
    def __init__(self):
        self.l = []

    def add(self, ep, kartela, pedio, minima, ypologismos=None, extra=None):
        self.l.append({"επιπεδο": ep, "καρτελα": kartela, "πεδιο": pedio,
                       "μηνυμα": minima, "υπολογισμος": ypologismos, **(extra or {})})

    def req(self, obj, kleidi, kartela, etiketa):
        if keno(obj.get(kleidi)):
            self.add("ΣΦΑΛΜΑ", kartela, etiketa, "Υποχρεωτικό πεδίο κενό")
            return False
        return True


# ----------------------------------------------------------------- έλεγχοι

def elegxos_oikopedou(o, E):
    K = "Οικόπεδο/Γήπεδο"
    for k, et in [("περιγραφη", "Περιγραφή"), ("οδος", "Οδός"), ("πολη_οικισμος", "Πόλη/Οικισμός"),
                  ("τκ", "ΤΚ"), ("περιοχη_τοποθεσια", "Περιοχή/Τοποθεσία"), ("επιφανεια_τμ", "Επιφάνεια (τμ)"),
                  ("εντος_σχεδιου_οικισμου", "Εντός σχεδίου/οικισμού"), ("ειδικο_καθεστως", "Ειδικό καθεστώς"),
                  ("διαιρεση_οικοπεδου", "Διαίρεση Οικοπέδου/Γηπέδου"), ("αδομητο", "Αδόμητο"),
                  ("αριθμος_κτιριων", "Αριθμός κτιρίων"), ("αριθμος_ιδιοκτησιων", "Αριθμός Ιδιοκτησιών")]:
        E.req(o, k, K, et)

    for k, et in [("οδος", "Οδός"), ("πολη_οικισμος", "Πόλη/Οικισμός"), ("περιοχη_τοποθεσια", "Περιοχή/Τοποθεσία")]:
        v = o.get(k)
        if keno(v):
            continue
        if not XARAKTIRES.match(v):
            prot = kanoniko(v)
            if XARAKTIRES.match(prot):
                E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, et, f"Πεζά ή τονισμένα — το ΤΕΕ θέλει κεφαλαία χωρίς τόνο. Πρόταση: «{prot}»")
            else:
                kaka = sorted({c for c in prot if not XARAKTIRES.match(c)})
                E.add("ΣΦΑΛΜΑ", K, et, f"Μη επιτρεπτοί χαρακτήρες {kaka} — επιτρέπονται κεφαλαία ελληνικά, κενό, τελεία, παύλα")
        else:
            E.add("ΟΚ", K, et, "Κανόνας χαρακτήρων ΤΕΕ")

    if not keno(o.get("τκ")) and not re.fullmatch(r"\d{5}", str(o["τκ"]).replace(" ", "")):
        E.add("ΣΦΑΛΜΑ", K, "ΤΚ", f"Μη έγκυρος ΤΚ «{o['τκ']}» (5 ψηφία)")
    if not keno(o.get("καεκ_οικοπεδου")):
        if KAEK.match(str(o["καεκ_οικοπεδου"]).strip()):
            E.add("ΟΚ", K, "ΚΑΕΚ Οικοπέδου", "Μορφή 12 ψηφία/x/x")
        else:
            E.add("ΣΦΑΛΜΑ", K, "ΚΑΕΚ Οικοπέδου", f"Μορφή «{o['καεκ_οικοπεδου']}» — αναμένεται 012345678901/00/00· διαφορετικά ως «Πρόσθετα στοιχεία ιδιοκτησίας»")
    ep = num(o.get("επιφανεια_τμ"))
    if not keno(o.get("επιφανεια_τμ")) and (ep is None or ep <= 0):
        E.add("ΣΦΑΛΜΑ", K, "Επιφάνεια (τμ)", f"Μη αριθμητική ή μηδενική τιμή «{o.get('επιφανεια_τμ')}»")
    ni = num(o.get("αριθμος_ιδιοκτησιων"))
    if ni is not None and ni < 1:
        E.add("ΣΦΑΛΜΑ", K, "Αριθμός Ιδιοκτησιών", "Ελάχιστο 1")

    return ep


def elegxos_idioktisias(idx, idk, oik, E):
    pre = f"Ιδιοκτησία {idx}"
    s = idk.get("στοιχεια_ιδιοκτησιας") or {}
    K = f"{pre} · Στοιχεία"
    for k, et in [("τυπος_ιδιοκτησιας", "Τύπος Ιδιοκτησίας"), ("περιγραφη", "Περιγραφή Ιδιοκτησίας"),
                  ("αιτιολογια_καταχωρισης", "Αιτιολογία"), ("αριθμος_θεσεων_σταθμευσης", "Αριθμός θέσεων στάθμευσης")]:
        E.req(s, k, K, et)
    typos = kanoniko(s.get("τυπος_ιδιοκτησιας", ""))
    diair = kanoniko(oik.get("διαιρεση_οικοπεδου", ""))
    if ("ΟΡΙΖΟΝΤΙΑ" in typos or "ΚΑΘΕΤΗ" in typos):
        if keno(s.get("χιλιοστα_επι_οικοπεδου")):
            E.add("ΣΦΑΛΜΑ", K, "Χιλιοστά", "Υποχρεωτικά για Οριζόντια/Κάθετη διηρημένη")
        if "ΧΩΡΙΣ" in diair:
            E.add("ΣΦΑΛΜΑ", K, "Τύπος Ιδιοκτησίας",
                  f"«{s.get('τυπος_ιδιοκτησιας')}» σε οικόπεδο «{oik.get('διαιρεση_οικοπεδου')}» — το σύστημα ελέγχει την αντιστοιχία")
    if "ΑΔΙΑΙΡΕΤΗ" in typos and "ΜΕ ΣΥΣΤΑΣΗ" in diair:
        E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, "Τύπος Ιδιοκτησίας", "Αδιαίρετη ιδιοκτησία σε οικόπεδο ΜΕ σύσταση — έλεγξε")
    tp = s.get("τεχνικη_περιγραφη") or ""
    if len(tp) > 4000:
        E.add("ΣΦΑΛΜΑ", K, "Τεχνική περιγραφή", f"{len(tp)} χαρακτήρες — όριο 4.000")
    if not keno(s.get("καεκ_ιδιοκτησιας")) and not KAEK.match(str(s["καεκ_ιδιοκτησιας"]).strip()):
        E.add("ΣΦΑΛΜΑ", K, "ΚΑΕΚ Ιδιοκτησίας", f"Μορφή «{s['καεκ_ιδιοκτησιας']}»")

    # ---- Υπόχρεοι
    K = f"{pre} · Υπόχρεος"
    yp = lista(idk.get("υποχρεοι"))
    if not yp:
        E.add("ΣΦΑΛΜΑ", K, "Υπόχρεοι", "Κανένας υπόχρεος")
    athr = {}
    for j, u in enumerate(yp, 1):
        onoma = f"{u.get('επωνυμο', '')} {u.get('ονομα', '')}".strip() or f"#{j}"
        for k, et in [("ιδιοτητα", "Ιδιότητα"), ("ποσοστο", "Ποσοστό"), ("επωνυμο", "Επώνυμο"),
                      ("ονομα", "Όνομα"), ("ονομα_πατερα", "Όνομα πατέρα"), ("υποχρεος", "Υπόχρεος ΝΑΙ/ΟΧΙ")]:
            E.req(u, k, K, f"{et} ({onoma})")
        if keno(u.get("αφμ")) and keno(u.get("αφμ_εξωτερικου")):
            E.add("ΣΦΑΛΜΑ", K, f"ΑΦΜ ({onoma})", "Υποχρεωτικό ΑΦΜ ή ΑΦΜ εξωτερικού")
        elif not keno(u.get("αφμ")):
            if afm_ok(u["αφμ"]):
                E.add("ΟΚ", K, f"ΑΦΜ ({onoma})", "Ψηφίο ελέγχου ΑΦΜ σωστό")
            else:
                E.add("ΣΦΑΛΜΑ", K, f"ΑΦΜ ({onoma})", f"«{u['αφμ']}» αποτυγχάνει στον έλεγχο ψηφίου — έλεγξε την ανάγνωση")
        if kanoniko(u.get("υποχρεος", "")) == "ΝΑΙ" and keno(u.get("email")):
            E.add("ΣΦΑΛΜΑ", K, f"e-mail ({onoma})", "Κενό email σε υπόχρεο ΝΑΙ (υποχρεωτικό κατά εγχειρίδιο)")
        elif keno(u.get("email")):
            E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, f"e-mail ({onoma})", "Κενό· το εγχειρίδιο το σημειώνει υποχρεωτικό (στο ζωντανό σύστημα έγινε δεκτό κενό για υπόχρεο ΟΧΙ)")
        p = num(u.get("ποσοστο"))
        if p is not None:
            athr.setdefault(kanoniko(u.get("ιδιοτητα", "")), []).append((onoma, p))
    if yp and not any(kanoniko(u.get("υποχρεος", "")) == "ΝΑΙ" for u in yp):
        E.add("ΣΦΑΛΜΑ", K, "Υπόχρεος", "Κανείς με «Υπόχρεος = ΝΑΙ»")
    pl = sum(p for _, p in athr.get("ΠΛΗΡΗΣ ΚΥΡΙΟΣ", []))
    ps = sum(p for _, p in athr.get("ΨΙΛΟΣ ΚΥΡΙΟΣ", []))
    pe = sum(p for _, p in athr.get("ΕΠΙΚΑΡΠΩΤΗΣ", []))
    elegxoi_pos = []
    if athr.get("ΨΙΛΟΣ ΚΥΡΙΟΣ") or athr.get("ΕΠΙΚΑΡΠΩΤΗΣ"):
        elegxoi_pos += [("πλήρης + ψιλός", pl + ps), ("πλήρης + επικαρπωτής", pl + pe)]
    elif athr.get("ΠΛΗΡΗΣ ΚΥΡΙΟΣ"):
        elegxoi_pos.append(("πλήρης κυριότητα", pl))
    for et, v in elegxoi_pos:
        anal = " + ".join(gr(p, 2) for k in ("ΠΛΗΡΗΣ ΚΥΡΙΟΣ", "ΨΙΛΟΣ ΚΥΡΙΟΣ", "ΕΠΙΚΑΡΠΩΤΗΣ") for _, p in athr.get(k, []))
        if abs(v - 100) <= ANOXI:
            E.add("ΟΚ", K, f"Ποσοστά ({et})", "Άθροισμα 100%", f"{anal} = {gr(v)}%")
        else:
            E.add("ΣΦΑΛΜΑ", K, f"Ποσοστά ({et})", f"Άθροισμα {gr(v)}% ≠ 100%", anal)

    # ---- Πράξεις
    K = f"{pre} · Πράξεις"
    pr = lista(idk.get("πραξεις"))
    if not pr:
        E.add("ΣΦΑΛΜΑ", K, "Πράξεις", "Καμία πράξη (για προ 1955: τύπος «Β.Δ. 9-8-1955»)")
    ayth = []
    for p in pr:
        et = f"{p.get('τυπος_πραξης', '')} {p.get('αα_πραξης', '')}".strip()
        for k, e2 in [("τυπος_πραξης", "Τύπος πράξης"), ("αα_πραξης", "Α/Α"), ("ημ_εκδοσης", "Ημ/νία έκδοσης"),
                      ("εκδουσα_αρχη", "Εκδούσα αρχή")]:
            E.req(p, k, K, f"{e2} ({et})")
        if not keno(p.get("ημ_εκδοσης")) and not imerominia_ok(p["ημ_εκδοσης"]):
            E.add("ΣΦΑΛΜΑ", K, f"Ημ/νία ({et})", f"Μη έγκυρη ημερομηνία «{p['ημ_εκδοσης']}»")
        st = lista(p.get("στατικος_ελεγχος"))
        is_ayth = bool(AYTHAIRETA.search(str(p.get("τυπος_πραξης", ""))))
        if is_ayth:
            ayth.append(p)
            if not st:
                E.add("ΣΦΑΛΜΑ", K, f"Στατικός έλεγχος ({et})",
                      "Υποχρεωτικός πίνακας «Στατικός έλεγχος» για πράξη ν.4178/13 ή ν.4495/17 (κωδ. ν.5306/26)")
            else:
                E.add("ΟΚ", K, f"Στατικός έλεγχος ({et})", f"{len(st)} γραμμή(-ές)")
            d = p.get("δηλωση_αυθαιρετου") or {}
            an = {k: num(v) for k, v in (d.get("αναλυση_προστιμου") or {}).items()}
            sy = num(d.get("συνολικο_προστιμο"))
            if an and sy is not None:
                athroisma = sum(v for v in an.values() if v is not None)
                ypol = " + ".join(gr(v) for v in an.values() if v is not None) + f" = {gr(athroisma)} €"
                if abs(athroisma - sy) <= ANOXI:
                    E.add("ΟΚ", K, f"Πρόστιμο ({et})", "Ανάλυση = συνολικό", ypol)
                else:
                    E.add("ΑΣΥΜΦΩΝΙΑ", K, f"Πρόστιμο ({et})", f"Ανάλυση {gr(athroisma)} € ≠ συνολικό {gr(sy)} €", ypol,
                          {"σοβαροτητα": "ΥΨΗΛΗ"})
        for g in st:
            t = kanoniko(g.get("τυπος", "")).replace(".", "")
            if "ΔΕΔΟΤΑ" in t or "ΤΡΩΤΟΤΗΤΑΣ" in t:
                if "4178" not in str(p.get("τυπος_πραξης", "")):
                    E.add("ΣΦΑΛΜΑ", K, f"Στατικός έλεγχος ({et})", "ΔΕ.ΔΟ.Τ.Α. επιτρέπεται μόνο σε πράξεις ν.4178/13")
                if keno(g.get("αποτελεσμα")):
                    E.add("ΣΦΑΛΜΑ", K, f"Στατικός έλεγχος ({et})", "ΔΕ.ΔΟ.Τ.Α. χωρίς Αποτέλεσμα ελέγχου")
                if "ΥΨΗΛ" in kanoniko(g.get("αποτελεσμα", "")) and not any("ΕΠΑΡΚΕΙΑΣ" in kanoniko(x.get("τυπος", "")) for x in st):
                    E.add("ΣΦΑΛΜΑ", K, f"Στατικός έλεγχος ({et})", "ΔΕ.ΔΟ.Τ.Α. Υψηλή → απαιτείται και Μελέτη Στατικής Επάρκειας")
            if "ΕΝΙΣΧΥΣ" in kanoniko(g.get("αποτελεσμα", "")) and keno(g.get("κατασταση")):
                E.add("ΣΦΑΛΜΑ", K, f"Στατικός έλεγχος ({et})", "Απαίτηση ενισχύσεων χωρίς Κατάσταση εργασιών")
    if len(ayth) > 1:
        E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, "Δηλώσεις αυθαιρέτων",
              f"{len(ayth)} πράξεις αυθαιρέτων — αν αφορούν τα ίδια αυθαίρετα, καταχωρίζεται μόνο η πιο πρόσφατη")

    # ---- Επιφάνειες / Χρήσεις
    K = f"{pre} · Επιφάνειες"
    ef = lista(idk.get("επιφανειες"))
    xr = lista(idk.get("χρησεις"))
    aa_praxeon = [str(p.get("αα_πραξης", "")).strip() for p in pr if not keno(p.get("αα_πραξης"))]
    tot_k = tot_v = 0.0
    an_orofo_ef, an_orofo_xr = {}, {}
    for j, r in enumerate(ef, 1):
        ref = str(r.get("πραξη", ""))
        if keno(ref):
            E.add("ΣΦΑΛΜΑ", K, f"Γραμμή {j}", "Χωρίς πράξη")
        elif not any(re.search(rf"(?<!\d){re.escape(a)}(?!\d)", ref) for a in aa_praxeon):
            E.add("ΣΦΑΛΜΑ", K, f"Γραμμή {j}", f"Η πράξη «{ref}» δεν υπάρχει στην καρτέλα Πράξεις")
        if keno(r.get("οροφος")):
            E.add("ΣΦΑΛΜΑ", K, f"Γραμμή {j}", "Χωρίς όροφο")
        k = num(r.get("χωρος_κυριας_χρησης_τμ")) or 0.0
        v = num(r.get("χωρος_βοηθητικης_χρησης_τμ")) or 0.0
        tot_k += k
        tot_v += v
        an_orofo_ef[r.get("οροφος", "—")] = an_orofo_ef.get(r.get("οροφος", "—"), 0.0) + k + v
    tot_xr = 0.0
    Kx = f"{pre} · Χρήσεις"
    for j, r in enumerate(xr, 1):
        for kk, e2 in [("ειδος_χρησης", "Είδος χρήσης"), ("εμβαδο_τμ", "Εμβαδό"), ("οροφος", "Όροφος")]:
            E.req(r, kk, Kx, f"{e2} (γραμμή {j})")
        e = num(r.get("εμβαδο_τμ")) or 0.0
        tot_xr += e
        an_orofo_xr[r.get("οροφος", "—")] = an_orofo_xr.get(r.get("οροφος", "—"), 0.0) + e
    if ef or xr:
        ypol = (f"Επιφάνειες: Κύρια {gr(tot_k)} + Βοηθητική {gr(tot_v)} = {gr(tot_k + tot_v)} τ.μ. · "
                f"Χρήσεις: {' + '.join(gr(num(r.get('εμβαδο_τμ')) or 0) for r in xr)} = {gr(tot_xr)} τ.μ.")
        if abs(tot_k + tot_v - tot_xr) <= ANOXI:
            E.add("ΟΚ", K, "Επιφάνειες = Χρήσεις", "Ισότητα αθροισμάτων (κανόνας εγχειριδίου σ.18)", ypol)
        else:
            E.add("ΣΦΑΛΜΑ", K, "Επιφάνειες = Χρήσεις",
                  f"Διαφορά {gr(tot_xr - tot_k - tot_v)} τ.μ. — το άθροισμα Κύριας + Βοηθητικής πρέπει να ισούται με το άθροισμα των Χρήσεων (εγχειρίδιο σ.18)",
                  ypol)
        for orofos in sorted(set(an_orofo_ef) | set(an_orofo_xr)):
            a, b = an_orofo_ef.get(orofos, 0.0), an_orofo_xr.get(orofos, 0.0)
            if abs(a - b) > ANOXI:
                E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, f"Όροφος «{orofos}»",
                      f"Επιφάνειες {gr(a)} τ.μ. vs Χρήσεις {gr(b)} τ.μ.")

    # ---- ΠΕΑ / Δίκτυα
    K = f"{pre} · ΠΕΑ-Δίκτυα"
    for p in lista(idk.get("πεα")):
        for kk, e2 in [("αρ_πρωτοκολλου", "Αρ. πρωτοκόλλου"), ("ημ_εκδοσης", "Ημ/νία έκδοσης"),
                       ("αρ_ασφαλειας", "Αρ. ασφαλείας"), ("κατηγορια", "Κατηγορία")]:
            E.req(p, kk, K, e2)
        for kk, e2 in [("ετησια_καταναλωση_κτιριου", "Ετήσια κατανάλωση"), ("ετησιες_εκπομπες_co2", "Ετήσιες εκπομπές CO2")]:
            v = num(p.get(kk))
            if v is not None and abs(v - round(v)) > 1e-9:
                E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, e2,
                      f"Δεκαδική τιμή {p.get(kk)} — το εγχειρίδιο ζητά ακέραιο (στρογγυλοποίηση → {int(round(v))}); στο ζωντανό σύστημα έχει γίνει δεκτό δεκαδικό")
        if not keno(p.get("ημ_εκδοσης")) and not imerominia_ok(p["ημ_εκδοσης"]):
            E.add("ΣΦΑΛΜΑ", K, "Ημ/νία ΠΕΑ", f"Μη έγκυρη «{p['ημ_εκδοσης']}»")
    if not lista(idk.get("δικτυα")):
        E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", K, "Στοιχεία Δικτύων", "Κενός πίνακας — δεν δηλώθηκε παροχή (λείπει λογαριασμός;)")


def diastavrosi(lista_d, E):
    for g in lista_d:
        meg = g.get("μεγεθος", "?")
        mon = g.get("μοναδα", "")
        tim = [(t.get("πηγη", "?"), t.get("τιμη"), num(t.get("τιμη"))) for t in g.get("τιμες", [])]
        arith = [x for x in tim if x[2] is not None]
        if len(arith) < 2:
            continue
        vals = [x[2] for x in arith]
        mn, mx = min(vals), max(vals)
        listing = " · ".join(f"{p}: {gr(v)} {mon}".strip() for p, _, v in arith)
        if mx - mn <= ANOXI:
            E.add("ΟΚ", "Διασταύρωση", meg, f"Συμφωνούν {len(arith)} πηγές", listing)
            continue
        rel = (mx - mn) / mx if mx else 1
        sov = "ΥΨΗΛΗ" if rel > 0.02 else "ΜΕΣΑΙΑ" if rel > 0.002 else "ΧΑΜΗΛΗ"
        epil = g.get("επιλεγμενη")
        msg = f"{len(set(round(v, 2) for v in vals))} διαφορετικές τιμές, Δmax = {gr(mx - mn)} {mon} ({gr(rel * 100, 1)}%)"
        if not keno(epil):
            msg += f". Προτεινόμενη για το πεδίο: {epil} — χρειάζεται επιβεβαίωση"
        E.add("ΑΣΥΜΦΩΝΙΑ", "Διασταύρωση", meg, msg, listing,
              {"σοβαροτητα": sov, "τιμες": [{"πηγη": p, "τιμη": t} for p, t, _ in arith], "επιλεγμενη": epil})


def trexe(d):
    E = Eyrimata()
    raw = d
    d = kathara(d)
    oik = d.get("οικοπεδο_γηπεδο") or {}
    elegxos_oikopedou(oik, E)
    idks = lista(d.get("ιδιοκτησιες"))
    if not idks:
        E.add("ΣΦΑΛΜΑ", "Ιδιοκτησίες", "—", "Καμία ιδιοκτησία")
    for i, idk in enumerate(idks, 1):
        elegxos_idioktisias(i, idk, oik, E)
    n_kt = num(oik.get("αριθμος_ιδιοκτησιων"))
    if n_kt is not None and idks and len(idks) > n_kt:
        E.add("ΣΦΑΛΜΑ", "Οικόπεδο/Γήπεδο", "Αριθμός Ιδιοκτησιών", f"Δηλώθηκαν {gr(n_kt, 0)} αλλά καταχωρίστηκαν {len(idks)}")
    diastavrosi([g for g in d.get("διασταυρωση", []) if isinstance(g, dict)], E)
    for a in (d.get("ελεγχοι_επαληθευσης") or {}).get("ασυμφωνιες", []):
        if isinstance(a, dict) and not keno(a.get("περιγραφη")):
            E.add("ΑΣΥΜΦΩΝΙΑ", "Εξαγωγή", a.get("πεδιο", "—"), a["περιγραφη"], None,
                  {"σοβαροτητα": a.get("σοβαροτητα", "ΜΕΣΑΙΑ")})
    for l in d.get("λειπουν", []) or []:
        if isinstance(l, dict) and not keno(l.get("εγγραφο")):
            E.add("ΠΡΟΕΙΔΟΠΟΙΗΣΗ", "Φάκελος", l["εγγραφο"], f"Λείπει — {l.get('τι_δινει', '')}")
    E.l.sort(key=lambda x: SEIRA.index(x["επιπεδο"]))
    meta = raw.get("_meta") or {}
    return {
        "υποθεση": meta.get("υποθεση", ""),
        "καεκ": oik.get("καεκ_οικοπεδου", ""),
        "ημερομηνια": dt.date.today().strftime("%d/%m/%Y"),
        "συνοψη": {k: sum(1 for x in E.l if x["επιπεδο"] == k) for k in SEIRA},
        "ευρηματα": E.l,
        "παραδοχες": [p for p in (d.get("παραδοχες") or []) if isinstance(p, str) and p.strip()],
    }


# ----------------------------------------------------------------- έξοδος

EIK = {"ΣΦΑΛΜΑ": "🔴", "ΑΣΥΜΦΩΝΙΑ": "🟠", "ΠΡΟΕΙΔΟΠΟΙΗΣΗ": "🟡", "ΟΚ": "🟢"}
TITLOI = {"ΣΦΑΛΜΑ": "Σφάλματα — κανόνες ΤΕΕ/εγχειριδίου ή κενά υποχρεωτικά",
          "ΑΣΥΜΦΩΝΙΑ": "Ασυμφωνίες εγγράφων — επισημαίνονται, δεν διορθώθηκαν",
          "ΠΡΟΕΙΔΟΠΟΙΗΣΗ": "Προειδοποιήσεις",
          "ΟΚ": "Επιτυχείς έλεγχοι (ανεξάρτητος επανυπολογισμός)"}


def md(r):
    s = r["συνοψη"]
    L = ["# Αναφορά Επαλήθευσης ΗΤΚ", ""]
    if r["υποθεση"]:
        L.append(f"**Υπόθεση:** {r['υποθεση']}  ")
    L += [f"**ΚΑΕΚ:** {r['καεκ'] or '—'}  ", f"**Ημερομηνία ελέγχου:** {r['ημερομηνια']}", "",
          f"**Σύνοψη:** {s['ΣΦΑΛΜΑ']} σφάλματα · {s['ΑΣΥΜΦΩΝΙΑ']} ασυμφωνίες · {s['ΠΡΟΕΙΔΟΠΟΙΗΣΗ']} προειδοποιήσεις · {s['ΟΚ']} επιτυχείς", ""]
    n = 0
    for ep in SEIRA:
        ev = [x for x in r["ευρηματα"] if x["επιπεδο"] == ep]
        if not ev:
            continue
        n += 1
        L += [f"## {n}. {EIK[ep]} {TITLOI[ep]}", "", "| Καρτέλα | Πεδίο | Εύρημα | Υπολογισμός |", "|---|---|---|---|"]
        for x in ev:
            sov = f"**[{x['σοβαροτητα']}]** " if x.get("σοβαροτητα") else ""
            L.append(f"| {x['καρτελα']} | {x['πεδιο']} | {sov}{x['μηνυμα']} | {x.get('υπολογισμος') or ''} |".replace("\n", " "))
        L.append("")
    if r["παραδοχες"]:
        n += 1
        L += [f"## {n}. Παραδοχές", ""] + [f"{i}. {p}" for i, p in enumerate(r["παραδοχες"], 1)] + [""]
    L += ["---", "*Ντετερμινιστικοί έλεγχοι skill ΗΤΚ — προς έλεγχο από τον εξουσιοδοτημένο μηχανικό.*"]
    return "\n".join(L)


def docx_out(r, path, mixanikos, idiotita, rolos):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, m, Cm(2))
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Segoe UI", Pt(10)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), "Segoe UI")
    for hn in ("Heading 1", "Heading 2"):
        h = doc.styles[hn]
        h.font.name = "Segoe UI"
        h.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)

    doc.add_heading("Αναφορά Επαλήθευσης ΗΤΚ", level=1)
    s = r["συνοψη"]
    for et, v in [("Υπόθεση", r["υποθεση"]), ("ΚΑΕΚ", r["καεκ"]), ("Ημερομηνία ελέγχου", r["ημερομηνια"]),
                  ("Σύνοψη", f"{s['ΣΦΑΛΜΑ']} σφάλματα · {s['ΑΣΥΜΦΩΝΙΑ']} ασυμφωνίες · {s['ΠΡΟΕΙΔΟΠΟΙΗΣΗ']} προειδοποιήσεις · {s['ΟΚ']} επιτυχείς")]:
        if v:
            p = doc.add_paragraph()
            p.add_run(f"{et}: ").bold = True
            p.add_run(str(v))

    xrom = {"ΣΦΑΛΜΑ": RGBColor(0xC0, 0x00, 0x00), "ΑΣΥΜΦΩΝΙΑ": RGBColor(0xC5, 0x5A, 0x11),
            "ΠΡΟΕΙΔΟΠΟΙΗΣΗ": RGBColor(0x8A, 0x6D, 0x00), "ΟΚ": RGBColor(0x1E, 0x7B, 0x34)}
    n = 0
    for ep in SEIRA:
        ev = [x for x in r["ευρηματα"] if x["επιπεδο"] == ep]
        if not ev:
            continue
        n += 1
        h = doc.add_heading(f"{n}. {TITLOI[ep]}", level=2)
        for run in h.runs:
            run.font.color.rgb = xrom[ep]
        t = doc.add_table(rows=1, cols=4)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c, txt in zip(t.rows[0].cells, ["Καρτέλα", "Πεδίο", "Εύρημα", "Υπολογισμός"]):
            c.text = ""
            c.paragraphs[0].add_run(txt).bold = True
        for x in ev:
            row = t.add_row().cells
            row[0].text, row[1].text = x["καρτελα"], x["πεδιο"]
            p = row[2].paragraphs[0]
            if ep == "ΑΣΥΜΦΩΝΙΑ":
                if x.get("σοβαροτητα"):
                    rr = p.add_run(f"[{x['σοβαροτητα']}] ")
                    rr.bold = True
                    rr.font.color.rgb = xrom[ep]
                if x.get("τιμες"):
                    for tt in x["τιμες"]:
                        p.add_run(f"{tt['πηγη']}: ")
                        hl = p.add_run(str(tt["τιμη"]))
                        hl.font.highlight_color = WD_COLOR_INDEX.YELLOW
                        p.add_run("  ")
                    note = p.add_run(f" [{x['μηνυμα']}]")
                else:
                    hl = p.add_run(x["μηνυμα"])
                    hl.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    note = None
                if note is not None:
                    note.italic = True
                    note.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
            else:
                p.add_run(x["μηνυμα"])
            row[3].text = x.get("υπολογισμος") or ""
            for c in row:
                for pp in c.paragraphs:
                    for rn in pp.runs:
                        rn.font.size = Pt(9)
        t.autofit = False
        platoi = (Cm(2.8), Cm(3.0), Cm(7.0), Cm(4.2))
        grid = t._tbl.tblGrid
        for i, w in enumerate(platoi):
            t.columns[i].width = w
            grid.gridCol_lst[i].w = w
            for row in t.rows:
                row.cells[i].width = w

    if r["παραδοχες"]:
        n += 1
        doc.add_heading(f"{n}. Παραδοχές", level=2)
        for p in r["παραδοχες"]:
            doc.add_paragraph(p, style="List Number")

    doc.add_paragraph()
    for i, line in enumerate([rolos, "", "", mixanikos, idiotita if mixanikos else ""]):
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.left_indent = Cm(9)
        p.paragraph_format.space_after = Pt(0)
        if i == 3 and p.runs:
            p.runs[0].bold = True
    doc.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_ypothesis")
    ap.add_argument("--md")
    ap.add_argument("--docx")
    ap.add_argument("--json")
    ap.add_argument("--mixanikos", default="")
    ap.add_argument("--idiotita", default="Διπλωματούχος Πολιτικός Μηχανικός Ε.Μ.Π.")
    ap.add_argument("--rolos", default="Ο Συντάξας Μηχανικός")
    a = ap.parse_args()

    d = json.loads(Path(a.json_ypothesis).read_text(encoding="utf-8"))
    r = trexe(d)
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.md:
        Path(a.md).write_text(md(r), encoding="utf-8")
    if a.docx:
        docx_out(r, a.docx, a.mixanikos, a.idiotita, a.rolos)
    s = r["συνοψη"]
    print(f"ΣΦΑΛΜΑ {s['ΣΦΑΛΜΑ']} · ΑΣΥΜΦΩΝΙΑ {s['ΑΣΥΜΦΩΝΙΑ']} · ΠΡΟΕΙΔΟΠΟΙΗΣΗ {s['ΠΡΟΕΙΔΟΠΟΙΗΣΗ']} · ΟΚ {s['ΟΚ']}")
    for x in r["ευρηματα"]:
        if x["επιπεδο"] != "ΟΚ":
            print(f"  [{x['επιπεδο']}] {x['καρτελα']} / {x['πεδιο']}: {x['μηνυμα']}")


if __name__ == "__main__":
    main()
