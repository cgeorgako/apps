/* ------------------------------------------------------------------
   GF Office Manager — Λίστες / Μητρώο ΤΟΤΕΕ
   Drop-in module, vanilla JS, χωρίς εξαρτήσεις.

   Εγκατάσταση:
     1. Αντιγράψτε το αρχείο στον φάκελο js/ της εφαρμογής.
     2. <script src="js/gf-office-totee.js"></script> πριν το κλείσιμο του body.
     3. Στο tab «Λίστες» προσθέστε ένα κενό container:
          <div id="totee-list"></div>
     4. Όταν ανοίγει το tab, καλέστε:
          GFTotee.render(document.getElementById('totee-list'));
        (ασφαλές να κληθεί πολλές φορές — κάνει re-render)

   Προαιρετικά, ανάγνωση από Firebase αντί για τα ενσωματωμένα δεδομένα:
     firebase.database().ref('lists/totee').once('value').then(function(s){
       GFTotee.render(el, { data: s.val() });
     });
   ------------------------------------------------------------------ */
(function (global) {
  'use strict';

  var PAYLOAD = {
  "titlos": "Μητρώο ΤΟΤΕΕ",
  "perigrafi": "Τεχνικές Οδηγίες ΤΕΕ — πλήρης κατάλογος με καθεστώς ισχύος",
  "pigi": "https://web.tee.gr/d-e-k-a-d/tmima-epistimonikoy-kai-anaptyxiakoy-ergoy/totee/",
  "enimerosi": "01.12.2025",
  "kategories": [
    {
      "id": "egk",
      "titlos": "Εγκαταστάσεις σε κτίρια",
      "perigrafi": "Η πρώτη σειρά ΤΟΤΕΕ (σύμβαση ΥΠΕΧΩΔΕ–ΤΕΕ 24.07.1985) που αντικατέστησε τον κανονισμό «Περί Υδραυλικών Εγκαταστάσεων» του 1936."
    },
    {
      "id": "en",
      "titlos": "Ενεργειακή σειρά 20701 — ΚΕΝΑΚ",
      "perigrafi": "Το μεθοδολογικό υπόβαθρο κάθε ενεργειακής μελέτης και ΠΕΑ που εκδίδει το γραφείο."
    },
    {
      "id": "auto",
      "titlos": "Αυτοτελείς οδηγίες",
      "perigrafi": "Εκδόσεις ΤΕΕ χωρίς αρίθμηση σειράς και χωρίς εγκριτική υπουργική απόφαση."
    },
    {
      "id": "ekp",
      "titlos": "Υπό εκπόνηση ή διαβούλευση",
      "perigrafi": "Ανακοινωμένες αλλά μη εκδοθείσες. Καμία δεν παράγει υποχρέωση σήμερα."
    },
    {
      "id": "ist",
      "titlos": "Ιστορικές εκδόσεις",
      "perigrafi": "Αντικαταστάθηκαν, αλλά χρειάζονται για τον έλεγχο παλαιότερων φακέλων."
    }
  ],
  "katastaseis": {
    "ypoxreotiki": {
      "etiketa": "Υποχρεωτική",
      "perigrafi": "Εν ισχύι με εγκριτική απόφαση σε ΦΕΚ"
    },
    "systasi": {
      "etiketa": "Σύσταση",
      "perigrafi": "Εν ισχύι χωρίς εγκριτικό ΦΕΚ — κανόνας τέχνης και επιστήμης"
    },
    "anatheorisi": {
      "etiketa": "Υπό αναθεώρηση",
      "perigrafi": "Εν ισχύι, με ενεργή ομάδα εργασίας αναθεώρησης"
    },
    "katargimeni": {
      "etiketa": "Καταργημένη",
      "perigrafi": "Έπαυσε να ισχύει"
    },
    "ekponisi": {
      "etiketa": "Δεν έχει εκδοθεί",
      "perigrafi": "Ανακοινωμένη ή σε διαβούλευση"
    },
    "istoriko": {
      "etiketa": "Ιστορική",
      "perigrafi": "Αντικαταστάθηκε από νεότερη έκδοση"
    }
  },
  "eggrafes": [
    {
      "id": "2411",
      "kodikos": "ΤΟΤΕΕ 2411/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια και οικόπεδα. Διανομή κρύου – ζεστού νερού",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Δ΄ έκδοση",
      "fek": "ΦΕΚ 843/Β/16-11-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=710908",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2411_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2412",
      "kodikos": "ΤΟΤΕΕ 2412/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια και οικόπεδα. Αποχετεύσεις",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Ε΄ έκδοση",
      "fek": "ΦΕΚ 177/Β/31-3-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=719285",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2412_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2421-1",
      "kodikos": "ΤΟΤΕΕ 2421/1986 — Μέρος 1",
      "titlos": "Εγκαταστάσεις σε κτίρια. Δίκτυα διανομής ζεστού νερού για θέρμανση κτιριακών έργων",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Δ΄ έκδοση",
      "fek": "ΦΕΚ 67/Β/4-2-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=719175",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2421_1_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2421-2",
      "kodikos": "ΤΟΤΕΕ 2421/1986 — Μέρος 2",
      "titlos": "Εγκαταστάσεις σε κτίρια. Λεβητοστάσια παραγωγής ζεστού νερού για θέρμανση κτιριακών έργων",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Δ΄ έκδοση",
      "fek": "ΦΕΚ 148/Β/17-3-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=719256",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2421_2_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2423",
      "kodikos": "ΤΟΤΕΕ 2423/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Κλιματισμός κτιριακών χώρων",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Γ΄ έκδοση",
      "fek": "ΦΕΚ 177/Β/31-3-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=719285",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2423_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2425",
      "kodikos": "ΤΟΤΕΕ 2425/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Στοιχεία υπολογισμού φορτίων κλιματισμού κτιριακών χώρων",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Ε΄ έκδοση",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2425_86.pdf",
      "status": "systasi",
      "simeiosi": "Δεν φέρει εγκριτική απόφαση — ισχύει ως κανόνας τέχνης και επιστήμης, όχι ως υποχρεωτική διάταξη."
    },
    {
      "id": "2427",
      "kodikos": "ΤΟΤΕΕ 2427/1983",
      "titlos": "Κατανομή δαπανών κεντρικής θέρμανσης κτηρίων",
      "etos": "1983",
      "kategoria": "egk",
      "ekdosi": "",
      "fek": "ΦΕΚ 631/Δ/7-11-1985 (Π.Δ. 27)",
      "fekUrl": "https://search.et.gr/el/fek/?fekId=709009",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/202427-83fek_631d_1985.pdf",
      "status": "anatheorisi",
      "simeiosi": "Δημοσιεύθηκε αρχικά στο Ενημερωτικό Δελτίο ΤΕΕ αρ. 1294/23.01.1984. Η ομάδα εργασίας αναθεώρησης έχει παραδώσει τελικό κείμενο, το οποίο δεν έχει ακόμη θεσμοθετηθεί."
    },
    {
      "id": "2451",
      "kodikos": "ΤΟΤΕΕ 2451/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Μόνιμα πυροσβεστικά συστήματα με νερό",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Ε΄ έκδοση",
      "fek": "ΦΕΚ 632/Β/26-11-1987",
      "fekUrl": "https://search.et.gr/fek/?fekId=713801",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2451_86.pdf",
      "status": "anatheorisi",
      "simeiosi": "Εν ισχύι. Έχει συσταθεί ομάδα εργασίας ΤΕΕ για την αναθεώρησή της."
    },
    {
      "id": "2471",
      "kodikos": "ΤΟΤΕΕ 2471/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Διανομή καυσίμων αερίων",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Δ΄ έκδοση",
      "fek": "ΦΕΚ 366/Β/16-7-1987 · Π.Δ. 420/87 (ΦΕΚ 187/Α)",
      "fekUrl": "https://search.et.gr/fek/?fekId=713535",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2471_86.pdf",
      "status": "katargimeni",
      "simeiosi": "Έπαυσε να ισχύει με τον «Κανονισμό Εσωτερικών Εγκαταστάσεων Φυσικού Αερίου με πίεση λειτουργίας έως και 1 bar» — ΚΥΑ Δ3/Α/11346, ΦΕΚ 963/Β/15-7-2003. Συμπληρωματικά μέτρα: ΚΥΑ Δ3/Α/22560, ΦΕΚ 1730/Β/9-12-2005."
    },
    {
      "id": "2481",
      "kodikos": "ΤΟΤΕΕ 2481/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Διανομή ατμού μέχρι PN16-300°C",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Δ΄ έκδοση",
      "fek": "ΦΕΚ 334/Β/24-6-1987",
      "fekUrl": "https://search.et.gr/fek/?fekId=713503",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2481_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "2491",
      "kodikos": "ΤΟΤΕΕ 2491/1986",
      "titlos": "Εγκαταστάσεις σε κτίρια. Αποθήκευση και διανομή αερίων για ιατρική χρήση",
      "etos": "1986",
      "kategoria": "egk",
      "ekdosi": "Γ΄ έκδοση",
      "fek": "ΦΕΚ 665/Β/9-9-1988",
      "fekUrl": "https://search.et.gr/fek/?fekId=724384",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_2491_86.pdf",
      "status": "ypoxreotiki",
      "simeiosi": ""
    },
    {
      "id": "20701-1",
      "kodikos": "ΤΟΤΕΕ 20701-1/2017",
      "titlos": "Αναλυτικές εθνικές προδιαγραφές παραμέτρων για τον υπολογισμό της ενεργειακής απόδοσης κτιρίων και την έκδοση του πιστοποιητικού ενεργειακής απόδοσης",
      "etos": "2017",
      "kategoria": "en",
      "ekdosi": "Α΄ έκδοση",
      "fek": "ΦΕΚ 4003/Β/17-11-2017",
      "fekUrl": "https://search.et.gr/fek/?fekId=542227",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%95%CE%93%CE%9A%CE%A1%CE%99%CE%A3%CE%97-TOTEE-1.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Παράρτημα 1 της απόφασης ΔΕΠΕΑ/οικ. 182365/17.10.2017."
    },
    {
      "id": "20701-2",
      "kodikos": "ΤΟΤΕΕ 20701-2/2017",
      "titlos": "Θερμοφυσικές ιδιότητες δομικών υλικών και έλεγχος της θερμομονωτικής επάρκειας των κτηρίων",
      "etos": "2017",
      "kategoria": "en",
      "ekdosi": "Α΄ έκδοση",
      "fek": "ΦΕΚ 4003/Β/17-11-2017",
      "fekUrl": "https://search.et.gr/fek/?fekId=542227",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%95%CE%93%CE%9A%CE%A1%CE%99%CE%A3%CE%97-TOTEE-2.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Παράρτημα 2 της απόφασης ΔΕΠΕΑ/οικ. 182365/17.10.2017."
    },
    {
      "id": "20701-3",
      "kodikos": "ΤΟΤΕΕ 20701-3/2010",
      "titlos": "Κλιματικά δεδομένα ελληνικών περιοχών",
      "etos": "2014",
      "kategoria": "en",
      "ekdosi": "Γ΄ έκδοση",
      "fek": "ΦΕΚ 2945/Β/2014",
      "fekUrl": "https://search.et.gr/fek/?fekId=498690",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%95%CE%93%CE%9A%CE%A1%CE%99%CE%A3%CE%97-TOTEE-3.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Δεν αναθεωρήθηκε το 2017. Παραμένει σε ισχύ η Γ΄ έκδοση, Παράρτημα 3 της απόφασης οικ. 2618/2014."
    },
    {
      "id": "20701-4",
      "kodikos": "ΤΟΤΕΕ 20701-4/2017",
      "titlos": "Οδηγίες και έντυπα ενεργειακών επιθεωρήσεων κτηρίων, λεβήτων και εγκαταστάσεων θέρμανσης και εγκαταστάσεων κλιματισμού",
      "etos": "2017",
      "kategoria": "en",
      "ekdosi": "Α΄ έκδοση",
      "fek": "ΦΕΚ 4003/Β/17-11-2017",
      "fekUrl": "https://search.et.gr/fek/?fekId=542227",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%95%CE%93%CE%9A%CE%A1%CE%99%CE%A3%CE%97-TOTEE-4.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Παράρτημα 3 της απόφασης ΔΕΠΕΑ/οικ. 182365/17.10.2017."
    },
    {
      "id": "20701-5",
      "kodikos": "ΤΟΤΕΕ 20701-5/2017",
      "titlos": "Συμπαραγωγή ηλεκτρισμού, θερμότητας και ψύξης: εγκαταστάσεις σε κτήρια",
      "etos": "2017",
      "kategoria": "en",
      "ekdosi": "Α΄ έκδοση",
      "fek": "ΦΕΚ 4003/Β/17-11-2017",
      "fekUrl": "https://search.et.gr/fek/?fekId=542227",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%95%CE%93%CE%9A%CE%A1%CE%99%CE%A3%CE%97-TOTEE-5.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Παράρτημα 4 της απόφασης ΔΕΠΕΑ/οικ. 182365/17.10.2017."
    },
    {
      "id": "diorthosi-4108",
      "kodikos": "Διόρθωση σφαλμάτων",
      "titlos": "Διορθώσεις σφαλμάτων στην απόφαση ΔΕΠΕΑ/οικ. 182365/17.10.2017 «Έγκριση και εφαρμογή των Τεχνικών Οδηγιών ΤΕΕ για την Ενεργειακή Απόδοση Κτιρίων»",
      "etos": "2017",
      "kategoria": "en",
      "ekdosi": "",
      "fek": "ΦΕΚ 4108/Β/2017",
      "fekUrl": "https://search.et.gr/fek/?fekId=542200",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/4108.pdf",
      "status": "ypoxreotiki",
      "simeiosi": "Ελέγχεται υποχρεωτικά μαζί με το ΦΕΚ 4003/Β/2017."
    },
    {
      "id": "odofotismos",
      "kodikos": "ΤΟΤΕΕ (χωρίς αρίθμηση)",
      "titlos": "Σχεδιασμός και έλεγχος εγκαταστάσεων οδοφωτισμού",
      "etos": "2018",
      "kategoria": "auto",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/totee_odofotismou_Layout-1.pdf",
      "status": "systasi",
      "simeiosi": "Έκδοση ΤΕΕ χωρίς εγκριτική υπουργική απόφαση."
    },
    {
      "id": "yalopinakes",
      "kodikos": "ΤΟΤΕΕ (χωρίς αρίθμηση)",
      "titlos": "Υαλοπίνακες ασφαλείας",
      "etos": "2022",
      "kategoria": "auto",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/ISBN_2_11_2022__all_totee_yalopinakes_parartima_I_II.pdf",
      "status": "systasi",
      "simeiosi": "Εξαιρούνται εφαρμογές υαλοπινάκων με κύριο κριτήριο επιλογής τη θερμομόνωση ή/και την ηχομείωση. Ελεύθερη πρόσβαση μόνο για ανάγνωση."
    },
    {
      "id": "totee-0",
      "kodikos": "ΤΟΤΕΕ 0",
      "titlos": "Κατευθυντήριες οδηγίες για τη σύνταξη και αναθεώρηση των ΤΟΤΕΕ που θα αναπτυχθούν στο πλαίσιο της Εθνικής Συμμαχίας Αειφόρου Δόμησης",
      "etos": "2025",
      "kategoria": "auto",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/%CE%A4%CE%9F%CE%A4%CE%95%CE%95-2025-Nov.pdf",
      "status": "systasi",
      "simeiosi": "Μεθοδολογικό πλαίσιο της νέας γενιάς «ΤΟΤΕΕ Αειφόρου Δόμησης». Προδιαγράφει πάνω από 130 μελλοντικές οδηγίες."
    },
    {
      "id": "20701-6",
      "kodikos": "ΤΟΤΕΕ 20701-6",
      "titlos": "Βιοκλιματικός σχεδιασμός στον ελλαδικό χώρο",
      "etos": "—",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Ανακοινωμένη νέα ΤΟΤΕΕ της ενεργειακής σειράς. Δεν έχει εκδοθεί."
    },
    {
      "id": "20701-7",
      "kodikos": "ΤΟΤΕΕ 20701-7",
      "titlos": "Τεχνητός και φυσικός φωτισμός κτιρίων",
      "etos": "—",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Ανακοινωμένη νέα ΤΟΤΕΕ της ενεργειακής σειράς. Δεν έχει εκδοθεί."
    },
    {
      "id": "20701-8",
      "kodikos": "ΤΟΤΕΕ 20701-8",
      "titlos": "Εγκαταστάσεις αξιοποίησης ανανεώσιμων πηγών ενέργειας σε κτίρια",
      "etos": "—",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Ανακοινωμένη νέα ΤΟΤΕΕ της ενεργειακής σειράς. Δεν έχει εκδοθεί."
    },
    {
      "id": "20701-9",
      "kodikos": "ΤΟΤΕΕ 20701-9",
      "titlos": "Οικονομική αξιολόγηση ενεργειακών επενδύσεων",
      "etos": "—",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Ανακοινωμένη νέα ΤΟΤΕΕ της ενεργειακής σειράς. Δεν έχει εκδοθεί."
    },
    {
      "id": "20701-10",
      "kodikos": "ΤΟΤΕΕ 20701-10",
      "titlos": "Στοιχεία υπολογισμού εγκαταστάσεων θέρμανσης – ψύξης – αερισμού (κλιματισμού) και ζεστού νερού χρήσης κτιριακών χώρων",
      "etos": "—",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Ανακοινωμένη νέα ΤΟΤΕΕ της ενεργειακής σειράς. Δεν έχει εκδοθεί."
    },
    {
      "id": "lithostrota",
      "kodikos": "ΤΟΤΕΕ Αειφόρου Δόμησης",
      "titlos": "Αειφόρος κατασκευή, αποκατάσταση και συντήρηση λιθόστρωτων επιστρώσεων στην ορεινή και νησιωτική Ελλάδα",
      "etos": "2026",
      "kategoria": "ekp",
      "ekdosi": "",
      "fek": "",
      "fekUrl": "",
      "pdfUrl": "",
      "status": "ekponisi",
      "simeiosi": "Πρώτη εξειδικευμένη ΤΟΤΕΕ της σειράς Αειφόρου Δόμησης. Δημόσια διαβούλευση έως 20.09.2026."
    },
    {
      "id": "hist-2010",
      "kodikos": "ΤΟΤΕΕ 20701-1,2,3,4/2010",
      "titlos": "Αρχική έκδοση της ενεργειακής σειράς κατά τον πρώτο ΚΕΝΑΚ",
      "etos": "2010",
      "kategoria": "ist",
      "ekdosi": "Α΄ έκδοση",
      "fek": "ΦΕΚ 1387/Β/2010",
      "fekUrl": "",
      "pdfUrl": "https://web.tee.gr/wp-content/uploads/1387-b.pdf",
      "status": "istoriko",
      "simeiosi": "Αντικαταστάθηκε από τις εκδόσεις 2014 και 2017. Χρήσιμη για έλεγχο παλαιότερων ΠΕΑ και ενεργειακών μελετών."
    },
    {
      "id": "hist-2014",
      "kodikos": "ΤΟΤΕΕ 20701-1/-2/-4 (αναθ. 2014)",
      "titlos": "Ενδιάμεση αναθεώρηση: Γ΄ έκδοση 20701-1, Β΄ έκδοση 20701-2, Γ΄ έκδοση 20701-4",
      "etos": "2014",
      "kategoria": "ist",
      "ekdosi": "",
      "fek": "ΦΕΚ 2945/Β/2014 (οικ. 2618)",
      "fekUrl": "https://search.et.gr/fek/?fekId=498690",
      "pdfUrl": "",
      "status": "istoriko",
      "simeiosi": "Αντικαταστάθηκαν από τις Α΄ εκδόσεις 2017. Από την απόφαση αυτή παραμένει σε ισχύ μόνο η 20701-3/2010 (Γ΄ έκδοση)."
    }
  ]
};

  var COLORS = {
    ypoxreotiki: 'var(--gft-amber)', anatheorisi: 'var(--gft-amber)',
    systasi: 'var(--gft-teal)', katargimeni: 'var(--gft-rust)',
    ekponisi: 'var(--gft-slate)', istoriko: 'var(--gft-slate)'
  };
  var ORDER = ['ypoxreotiki', 'anatheorisi', 'systasi', 'katargimeni', 'ekponisi', 'istoriko'];

  var CSS = "\n.gft{--gft-panel:#171b24;--gft-line:#272e3b;--gft-fg:#dee4ee;--gft-dim:#8d97a8;\n  --gft-faint:#5d6676;--gft-amber:#e8a33d;--gft-teal:#45b3a6;--gft-rust:#b8635a;--gft-slate:#6d7a91;\n  font-family:\"IBM Plex Sans\",\"Segoe UI\",system-ui,sans-serif;color:var(--gft-fg);font-size:15px;line-height:1.55}\n.gft a{color:var(--gft-teal);text-decoration:none;border-bottom:1px solid rgba(69,179,166,.28)}\n.gft a:hover{border-bottom-color:var(--gft-teal)}\n.gft-bar{padding-bottom:14px;border-bottom:1px solid var(--gft-line);margin-bottom:8px}\n.gft-q{width:100%;background:var(--gft-panel);border:1px solid var(--gft-line);color:var(--gft-fg);\n  padding:9px 12px;border-radius:3px;font:inherit;font-size:14px}\n.gft-q::placeholder{color:var(--gft-faint)}\n.gft-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}\n.gft-chip{background:transparent;border:1px solid var(--gft-line);color:var(--gft-dim);\n  padding:5px 11px;border-radius:3px;font:inherit;font-size:12.5px;cursor:pointer}\n.gft-chip em{font-style:normal;font-family:\"IBM Plex Mono\",monospace;color:var(--gft-faint);margin-left:4px}\n.gft-chip:hover{border-color:var(--gft-slate);color:var(--gft-fg)}\n.gft-chip[aria-pressed=true]{background:#1d222d;border-color:var(--gft-amber);color:var(--gft-fg)}\n.gft-tally{font-family:\"IBM Plex Mono\",monospace;font-size:12.5px;color:var(--gft-faint);padding-top:10px}\n.gft-sect{margin-top:34px}\n.gft-h{font-size:16px;font-weight:600;margin:0 0 4px}\n.gft-sub{color:var(--gft-dim);font-size:13px;margin:0 0 16px;max-width:70ch}\n.gft-row{border-left:3px solid var(--gft-slate);background:var(--gft-panel);\n  padding:14px 16px;margin-bottom:7px;border-radius:0 3px 3px 0}\n.gft-s-ypoxreotiki{border-left-color:var(--gft-amber)}\n.gft-s-systasi{border-left-color:var(--gft-teal)}\n.gft-s-anatheorisi{border-left-color:var(--gft-amber);\n  background:linear-gradient(90deg,rgba(232,163,61,.055),transparent 40%),var(--gft-panel)}\n.gft-s-katargimeni{border-left-color:var(--gft-rust)}\n.gft-s-katargimeni .gft-code,.gft-s-katargimeni .gft-title{color:var(--gft-dim)}\n.gft-s-ekponisi,.gft-s-istoriko{border-left-color:var(--gft-slate);background:transparent;\n  border-top:1px solid var(--gft-line);border-right:1px solid var(--gft-line);border-bottom:1px solid var(--gft-line)}\n.gft-top{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;margin-bottom:5px}\n.gft-code{font-family:\"IBM Plex Mono\",monospace;font-size:13.5px;font-weight:500;color:var(--gft-amber)}\n.gft-s-systasi .gft-code,.gft-s-ekponisi .gft-code,.gft-s-istoriko .gft-code{color:var(--gft-dim)}\n.gft-badge{font-size:11.5px;font-family:\"IBM Plex Mono\",monospace;color:var(--gft-faint);\n  border:1px solid var(--gft-line);padding:1px 7px;border-radius:2px}\n.gft-title{font-size:14.5px;margin:0 0 8px;max-width:78ch}\n.gft-facts{display:flex;gap:8px 20px;flex-wrap:wrap;font-size:12.5px;\n  font-family:\"IBM Plex Mono\",monospace;color:var(--gft-dim)}\n.gft-note{font-size:12.5px;color:var(--gft-faint);margin:9px 0 0;max-width:80ch}\n.gft-empty{color:var(--gft-faint);font-size:14px;padding:24px 0}\n.gft-src{margin-top:34px;padding-top:18px;border-top:1px solid var(--gft-line);\n  font-size:12.5px;color:var(--gft-faint)}\n@media (max-width:640px){.gft-row{padding:12px 13px}}\n";

  function injectCSS() {
    if (document.getElementById('gft-style')) return;
    var s = document.createElement('style');
    s.id = 'gft-style';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function rowHTML(r, katastaseis) {
    var st = katastaseis[r.status] || { etiketa: r.status };
    var facts = [];
    if (r.etos && r.etos !== '\u2014') facts.push('\u0388\u03c4\u03bf\u03c2 ' + esc(r.etos));
    if (r.ekdosi) facts.push(esc(r.ekdosi));
    if (r.fek) {
      facts.push(r.fekUrl
        ? '<a href="' + esc(r.fekUrl) + '" target="_blank" rel="noopener">' + esc(r.fek) + '</a>'
        : esc(r.fek));
    } else {
      facts.push('\u03a7\u03c9\u03c1\u03af\u03c2 \u03b5\u03b3\u03ba\u03c1\u03b9\u03c4\u03b9\u03ba\u03cc \u03a6\u0395\u039a');
    }
    if (r.pdfUrl) {
      facts.push('<a href="' + esc(r.pdfUrl) + '" target="_blank" rel="noopener">PDF \u03a4\u0395\u0395</a>');
    }
    var hay = [r.kodikos, r.titlos, r.fek, r.simeiosi, r.etos, st.etiketa].join(' ').toLowerCase();
    return '<article class="gft-row gft-s-' + r.status + '" data-status="' + r.status +
      '" data-search="' + esc(hay) + '">' +
      '<div class="gft-top"><span class="gft-code">' + esc(r.kodikos) + '</span>' +
      '<span class="gft-badge">' + esc(st.etiketa) + '</span></div>' +
      '<p class="gft-title">' + esc(r.titlos) + '</p>' +
      '<div class="gft-facts">' + facts.map(function (f) { return '<span>' + f + '</span>'; }).join('') + '</div>' +
      (r.simeiosi ? '<p class="gft-note">' + esc(r.simeiosi) + '</p>' : '') +
      '</article>';
  }

  function render(container, opts) {
    if (!container) throw new Error('GFTotee.render: \u03bb\u03b5\u03af\u03c0\u03b5\u03b9 \u03c4\u03bf container');
    opts = opts || {};
    var d = opts.data || PAYLOAD;
    injectCSS();

    var counts = {};
    d.eggrafes.forEach(function (r) { counts[r.status] = (counts[r.status] || 0) + 1; });

    var chips = '<button class="gft-chip" data-status="all" aria-pressed="true">' +
      '\u038c\u03bb\u03b5\u03c2</button>' +
      ORDER.filter(function (k) { return counts[k]; }).map(function (k) {
        return '<button class="gft-chip" data-status="' + k + '" aria-pressed="false">' +
          esc(d.katastaseis[k].etiketa) + ' <em>' + counts[k] + '</em></button>';
      }).join('');

    var sections = d.kategories.map(function (kat) {
      var rows = d.eggrafes.filter(function (r) { return r.kategoria === kat.id; });
      if (!rows.length) return '';
      return '<section class="gft-sect">' +
        '<h3 class="gft-h">' + esc(kat.titlos) + '</h3>' +
        '<p class="gft-sub">' + esc(kat.perigrafi) + '</p>' +
        rows.map(function (r) { return rowHTML(r, d.katastaseis); }).join('') +
        '</section>';
    }).join('');

    container.innerHTML =
      '<div class="gft">' +
      '<div class="gft-bar">' +
      '<input type="search" class="gft-q" placeholder="\u0391\u03bd\u03b1\u03b6\u03ae\u03c4\u03b7\u03c3\u03b7 \u03c3\u03c4\u03bf \u03bc\u03b7\u03c4\u03c1\u03ce\u03bf" aria-label="Search">' +
      '<div class="gft-chips">' + chips + '</div>' +
      '<div class="gft-tally"></div></div>' +
      sections +
      '<p class="gft-empty" hidden>\u039a\u03b1\u03bc\u03af\u03b1 \u03b5\u03b3\u03b3\u03c1\u03b1\u03c6\u03ae.</p>' +
      '<p class="gft-src">\u03a0\u03b7\u03b3\u03ae: \u03a4\u0395\u0395 \u00b7 ' + esc(d.enimerosi) +
      ' \u00b7 <a href="' + esc(d.pigi) + '" target="_blank" rel="noopener">web.tee.gr</a></p>' +
      '</div>';

    var root = container.querySelector('.gft');
    var q = root.querySelector('.gft-q');
    var rows = [].slice.call(root.querySelectorAll('.gft-row'));
    var chipEls = [].slice.call(root.querySelectorAll('.gft-chip'));
    var tally = root.querySelector('.gft-tally');
    var empty = root.querySelector('.gft-empty');
    var active = 'all';

    function apply() {
      var t = (q.value || '').trim().toLowerCase(), n = 0;
      rows.forEach(function (r) {
        var ok = (active === 'all' || r.dataset.status === active) &&
                 (!t || r.dataset.search.indexOf(t) > -1);
        r.hidden = !ok; if (ok) n++;
      });
      [].forEach.call(root.querySelectorAll('.gft-sect'), function (s) {
        s.hidden = !s.querySelector('.gft-row:not([hidden])');
      });
      tally.textContent = n + ' \u03b1\u03c0\u03cc ' + rows.length + ' \u03b5\u03b3\u03b3\u03c1\u03b1\u03c6\u03ad\u03c2';
      empty.hidden = n > 0;
    }
    q.addEventListener('input', apply);
    chipEls.forEach(function (c) {
      c.addEventListener('click', function () {
        active = c.dataset.status;
        chipEls.forEach(function (x) { x.setAttribute('aria-pressed', String(x === c)); });
        apply();
      });
    });
    apply();
    return root;
  }

  global.GFTotee = { data: PAYLOAD, render: render, colors: COLORS };
})(window);
