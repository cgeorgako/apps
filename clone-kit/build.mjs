#!/usr/bin/env node
/*
 * Δημιουργία «κλώνου» της εφαρμογής ΚΑΕΚ χωρίς καμία σύνδεση με το SYNOLIKO-12.
 *
 *   node build.mjs <πηγή.html> <έξοδος.html>
 *
 * 1. Αφαιρεί όλα τα τμήματα που περικλείονται σε σήμανση  /*@SYN*\/ … /*@/SYN*\/  ή  <!--@SYN--> … <!--@/SYN-->
 *    (Καταχώριση, έλεγχος επικάλυψης, ανανέωση από repo, GitHub token κ.λπ.).
 * 2. Αλλάζει το footer.
 * 3. ΕΛΕΓΧΕΙ ότι δεν έμεινε κανένα ίχνος SYNOLIKO/GitHub-write και ότι το script είναι συντακτικά έγκυρο.
 *    Αν κάτι δεν ισχύει, το build ΑΠΟΤΥΓΧΑΝΕΙ (δεν παράγεται αρχείο).
 */
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';

const [,, src, out] = process.argv;
if (!src || !out) { console.error('Χρήση: node build.mjs <πηγή.html> <έξοδος.html>'); process.exit(2); }

const FOOTER_OLD = '<footer>Σχεδιασμός-Υλοποίηση Χρήστος Γεωργακόπουλος - 2026</footer>';
const FOOTER_NEW = '<footer>Σχεδιασμός - Υλοποίηση : Χρήστος Γεωργακόπουλος/2026 - Προσφορά προς τα μέλη ΤΕΕ Ηλείας</footer>';

const fail = m => { console.error('✗ ΑΠΟΤΥΧΙΑ BUILD: ' + m); process.exit(1); };

let html = fs.readFileSync(src, 'utf8');

// --- 1. αφαίρεση σημασμένων τμημάτων (έλεγχος ζευγαρώματος) ---
const open  = (html.match(/(<!--@SYN-->|\/\*@SYN\*\/)/g) || []).length;
const close = (html.match(/(<!--@\/SYN-->|\/\*@\/SYN\*\/)/g) || []).length;
if (open === 0) fail('δεν βρέθηκαν σημάνσεις @SYN στην πηγή (λάθος αρχείο/έκδοση;)');
if (open !== close) fail(`ασύμμετρες σημάνσεις @SYN (${open} έναρξης / ${close} λήξης)`);
const re = /(?:<!--@SYN-->|\/\*@SYN\*\/)[\s\S]*?(?:<!--@\/SYN-->|\/\*@\/SYN\*\/)/g;
html = html.replace(re, '');

// --- 2. footer ---
if (!html.includes(FOOTER_OLD)) fail('δεν βρέθηκε το αναμενόμενο footer στην πηγή');
html = html.replace(FOOTER_OLD, FOOTER_NEW);

// --- 3. έλεγχοι ασφαλείας ---
const forbidden = [
  /synoliko/i, /synUpdate/i, /synSig/i, /SynBanner/i,
  /lista_topo_arxeio/i, /api\.github\.com/i, /gh_token/i, /ghToken/i, /ghCommitFiles/i,
  /@\/?SYN/,
];
for (const rx of forbidden) {
  const m = html.match(rx);
  if (m) {
    const i = html.search(rx);
    fail(`έμεινε ίχνος «${m[0]}» στο αποτέλεσμα: …${html.slice(Math.max(0, i - 50), i + 80).replace(/\n/g, ' ')}…`);
  }
}
if (!html.includes(FOOTER_NEW)) fail('το νέο footer δεν εισήχθη');

// syntax check κάθε inline <script>
const scripts = [...html.matchAll(/<script\b(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]);
if (!scripts.length) fail('δεν βρέθηκε inline script');
scripts.forEach((code, i) => {
  try { new vm.Script(code, { filename: `inline-script-${i}` }); }
  catch (e) { fail(`συντακτικό σφάλμα στο inline script #${i}: ${e.message}`); }
});

// κάθε $('id') του script πρέπει να υπάρχει στο HTML (αλλιώς σπάει ο κώδικας στην εκκίνηση)
const bodyHtml = html.replace(/<script\b[\s\S]*?<\/script>/gi, '');
const ids = new Set([...bodyHtml.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
const code = scripts.join('\n');
const used = [...new Set([...code.matchAll(/\$\('([A-Za-z0-9_-]+)'\)/g)].map(m => m[1]))];
// ids που δημιουργούνται δυναμικά από JS (δεν υπάρχουν στο στατικό HTML)
const dynamic = new Set((code.match(/id="([A-Za-z0-9_-]+)"/g) || []).map(s => s.slice(4, -1)));
const missing = used.filter(id => !ids.has(id) && !dynamic.has(id));
if (missing.length) fail('το script αναφέρεται σε στοιχεία που δεν υπάρχουν πια στη σελίδα: ' + missing.join(', '));

fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
fs.writeFileSync(out, html, 'utf8');
console.log(`✓ OK — αφαιρέθηκαν ${open} τμήματα, ${scripts.length} script ελέγχθηκαν, ${(html.length/1024).toFixed(0)} KB → ${out}`);
