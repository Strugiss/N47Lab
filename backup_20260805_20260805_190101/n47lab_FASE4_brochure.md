# BROCHURE FASE 4 — 8 test concatenati (esecuzione AER registrata)

Data: 2026-08-05 | Metodo: AerSimulator + FakeSherbrooke, 8192 shots/pub,
transpile optimization_level=1, layout fisso per coppia. 76 pubs totali,
nessun SWAP, varatura Bell MI=0.741 OK.

Ogni test riporta: METRICA | soglia CICATRICE (PRED_ALTA) | fondo come
DA REGISTRATO/BROCHURE | note per il QPU.

---

## 1. QUENCHED_VS_ANNEALED (QvA)

- CIRUITO: 2 qubit PASM `H,H,cp(phi),H(q1),measure` — base di misura XZ
  (solo H su q1): rende la MI funzione esplicita di phi.
- QUENCHED: phi = pi fisso per tutti i pubs (picco storico).
- ANNEALED: phi random uniforme per pub; si aggregano i counts (stato misto).
- METRICA: MI_2x2 mediata; lettura su MI AGGREGATA (somma counts per tipo).
- **AER registrato**: MI_quenched_agg = 0.7367 | MI_annealed_agg = 0.2321 |
  Delta_agg = 0.5047 | singoli Delta = 0.4640.
- VERDETTO AER: **VERDE** (brochure supportata; la miscela di fase collassa la MI).
- SOGLIA QPU CICATRICE: Delta_agg >= 0.30 | RUMORE: Delta_agg <= 0.10.

## 2. MUTO_WITNESS (MW)

- CIRUITO: 3 qubit catena (a,b,c): H su tutti, cp(phi) su (a,b), H su (a,b)
  SOLO; c osservatore silenzioso in |+>.
- METRICA: MI marginale I(0;2) (qubit c è indipendente in ideale).
- **AER registrato**: MI(0,2) max = 0.00017 (phi=pi/3), 0.00005-0.0002 per
  tutte le phi. Crosstalk ASSENTE nel simulatore.
- VERDETTO AER: **VERDE** — soglia QPU pulita.
- SOGLIA QPU CICATRICE: MI(0,2) <= 0.003 | RUMORE: >= 0.020.

## 3. BASI_MISTE_XZ (BM)

- CIRUITO: stato di Bell |Phi+> (H,CNOT) come ISOLATO, misurato in 4 basi:
  XX (H su entrambi), XZ (H su q0), ZX (H su q1), ZZ (nessuna).
- METRICA: MI_2x2 per base; Delta_XX-XZ = MI_XX - MI_XZ.
- **AER registrato**: MI_XX=0.7509 | MI_XZ=0.0001 | MI_ZX=0.0000 |
  MI_ZZ=0.7691 | Delta_XX-XZ=0.7508.
- Nota: per Bell anche ZZ e' ALTA (correlazione del Bell): la brocia
  brochure "ZZ<=0.002" vale per il PASM con fase, NON per Bell. In QPU
  usare XZ/ZX come basi "CONTROLLO" (MI~0), XXI come base SEGNALE.
- VERDETTO AER: **VERDE**.
- SOGLIA QPU CICATRICE: Delta_XX-XZ >= 0.30 | RUMORE: <= 0.05.

## 4. MI_LIVELLO2 (I2)

- CIRUITO: catena 4 qubit (a,b,c,d) con 3 cp: (a,b),(b,c),(c,d); angoli
  phi_a su (a,b),(c,d) e phi_b centrale su (b,c). Baseline: (0,0).
- METRICA: I(ab;cd) = MI classica tra partizioni {0,1} e {2,3}.
- **AER registrato**: I(pi/2,pi/2)=0.0903 vs base(0,0)=0.0022, Delta=0.0881.
- VERDETTO AER: **VERDE** (coerenza mediata da filtro centrale emerge).
- SOGLIA QPU CICATRICE: Delta >= 0.01 | RUMORE: <= 0.002.

## 5. EMULA_ANOMALIA (AN)

- CIRUITO: PASM con iniezione Pz a q0 dopo cp(phi): Rz(eta*sin(phi)).
  phi in {+pi/3, -pi/3}, eta in {0, 0.01, 0.03, 0.1}; baseline phi=0.
- METRICA: R = MI(+pi/3) / MI(-pi/3); eta* = minima eta con R>=1.30.
- **AER registrato** (fondo di asimmetria simulato):
  eta=0.0 -> 0.902 | 0.01 -> 1.112 | 0.03 -> 1.092 | 0.1 -> 1.018;
  base_MI = 0.0109; eta* = nessuno.
- VERDETTO AER: **FONDO REGISTRATO** (il rumore simulato ha una lieve
  asimmetria direzionale su +pi/3 rispetto a -pi/3, NON oltre 1.30: il
  pericoloso eta*=non emerge).
- SOGLIA QPU CICATRICE (anomalia reale): eta* <= 0.10 con R >= 1.30
  (quindi R >= 1.30 regione => NON è solo fondo AER).
- NOTA: confrontare sempre con la R di fondo qui registrata; se al QPU
  R(eta=0.03) >= 1.3 -> anomalia reale oltre il fondo.

## 6. TWIRL_ZERO_MI (TW)

- CIRUITO: PASM cp(pi/2) no_twirl vs twirl frame X*X attorno al cp; n
  idle-blocks prima (n in {0,2,4,8}); estrapolazione a n=0.
- METRICA: MI_2x2; confronto no_twirl n=0 vs twirl n=0.
- **AER registrato**: no_twirl n=0 MI=0.0654 | twirl n=0 MI=0.0650
  (ratio=1.00). Il frame NON cancella nulla in AER: non c'è errore
  coerente da cancellare.
- VERDETTO AER: **FONDO REGISTRATO** — il twirl è EFFICACE solo sul
  QPU reale (errore coerente); usando l'AER come riferimento, sul QPU
  atteso crollo se errore coerente dominante.
- SOGLIA QPU CICATRICE: twirl n=0 MI <= 0.010 | RUMORE: twirl >= 0.030.

## 7. FRAME_SPLIT (FS)

- CIRUITO: PASM cp(phi,0,1) ramo A vs cp(phi,1,0) ramo B (controllo
  invertito), phi in {pi/6, pi/2, pi}.
- METRICA: Delta_AB = |MI(A) - MI(B)| per phi.
- **AER registrato** (fondo di asimmetria direzionale):
  pi/6: 0.0032 | pi/2: 0.0172 | pi: 0.0000; max = 0.0172.
- VERDETTO AER: **FONDO REGISTRATO** — asimmetria direzionale LIEVE nel
  simulatore (FakeSherbrooke distingue parzialmente controllo/target).
- SOGLIA QPU CICATRICE: Delta_AB <= 0.004 (simmetria) |
  RUMORE: Delta_AB >= 0.020 (soglia ALZATA rispetto a 0.012 della
  brochure per il fondo registrato).

## 8. ISOFASE_ORDINE_PERM (IO)

- CIRUITO: PASM a doppio filtro: cp(pi/4); bar; cp(3pi/4) ordine A vs
  cp(3pi/4); bar; cp(pi/4) ordine B; baseline (0,0).
- METRICA: Delta_ordine = |MI_A - MI_B|; p-value di permutazione (2000
  shuffle sulle etichette A/B).
- **AER registrato**: Delta=0.0004, p_perm=0.089 (indistinguibile).
- VERDETTO AER: **VERDE** (l'ordine non lascia impronta misurabile).
- SOGLIA QPU CICATRICE: Delta_ordine <= 0.003 e p_perm > 0.05 |
  RUMORE: Delta_ordine >= 0.020 e p_perm < 0.01.

---

## Riepilogo QPU (reset 26-08-2026 20:05 UTC)

| Test | Esito AER | Soglia CICATRICE | Soglia RUMORE |
|------|-----------|------------------|---------------|
| 1 QvA | VERDE | Delta_agg>=0.30 | Delta<=0.10 |
| 2 MUTO_WITNESS | VERDE | MI(0,2)<=0.003 | >=0.020 |
| 3 BASI_MISTE_XZ | VERDE | Delta_XX-XZ>=0.30 | <=0.05 |
| 4 MI_LIVELLO2 | VERDE | Delta>=0.01 | <=0.002 |
| 5 EMULA_ANOMALIA | FONDO | eta*<=0.10 (R>=1.3) | — |
| 6 TWIRL_ZERO_MI | FONDO | twirl_n0<=0.010 | >=0.030 |
| 7 FRAME_SPLIT | FONDO | Delta_AB<=0.004 | >=0.020 |
| 8 ISOFASE_ORDINE_PERM | VERDE | Delta<=0.003, p>0.05 | Delta>=0.020, p<0.01 |

Nota relatore: 5 VERDE + 3 FONDO REGISTRATO. Nessuna ANOMALIA bloccante.
I test 1 e 3 sono i più sensibili (Delta>0.5): prioritari al QPU.

---

## Piano QPU aggiornato (open plan 2026)

- **Quota**: 10 minuti di QPU time per finestra mobile di 28 giorni +
  bonus di +180 minuti su 12 mesi (attivabile dagli utenti attivi,
  >=20 min di QPU negli ultimi 12 mesi).
- **Canale**: ibm_cloud obbligatorio (il canale ibm_quantum non è più
  supportato; in alternativa ibm_quantum_platform).
- **Backend Heron r2 disponibili**: ibm_pittsburgh, ibm_boston, ibm_fez,
  ibm_miami, ibm_marrakesh, ibm_kingston (preferito: ibm_kingston).
- **Ordine di submit**: prima il piano DEB (target 26/08/2026 20:05 UTC),
  poi la FASE 4 (8 test concatenati).
- **Verifica quota**: prima di ogni test interrogare service.usage() e
  leggere ist_seconds; procedere solo se ist_seconds < 600 s (senza
  bonus) o < 600+10800 s (bonus attivo, quota mostrata > 600 s).