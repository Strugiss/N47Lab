# -*- coding: utf-8 -*-
"""FASE 4 (AER dryrun): 8 test concatenati della campagna cicatrice.

Doc: n47lab_FASE4_otto_test_INTEGRAZIONE.md (2026-08-05a).
Metodo: AerSimulator.from_backend(FakeSherbrook) per register il fondo AER di
ciascun test (calibratori) + soglie:CICATRICE/RUMORE/VERDE per il QPU.

Test (complemento del v3 campagna "cicatrice"):
  1. QUENCHED_VS_ANNEALED : quenched fase fissa vs annealed casuale per pub.
  2. MUTO_WITNESS         : crosstalk su qubit silenzioso q2 (PAM 3 qubit).
  3. BASI_MISTE_XZ        : MI in basi XX/XZ/ZX/ZZ (intreccio vs accordo).
  4. MI_LIVELLO2          : MI di 2� livello tra 2 coppie PASM (4 qubit).
  5. EMULA_ANOMALIA       : iniezione Rz(eta sin phi) -> fondo asimmetria.
  6. TWIRL_ZERO_MI        : twirl X*X attorno a cp(pi/2), estrapolazione n=0.
  7. FRAME_SPLIT          : cp(phi,0,1) vs cp(phi,1,0) (asimmetria direzionale).
  8. ISOFASE_ORDINE_PERM  : (pi/4,3pi/4) vs (3pi/4,pi/4), statistica di permutazione.

Piano open 2026: 10 min di QPU time per finestra mobile di 28 giorni +
bonus +180 min / 12 mesi (utenti attivi, >=20 min QPU in 12 mesi).
Canale obbligatorio ibm_cloud (ibm_quantum non piu' supportato).
RESET_QPU = target temporale di submit del piano DEB (26/08/2026 20:05 UTC);
la quota reale si verifica a runtime con service.usage() (dict: usage_consumed_seconds,
usage_limit_seconds, usage_remaining_seconds, time_available_at).

Uso: python n47lab_fase4_otto_test_aer.py [dryrun]
"""
import sys
import os
import json
import datetime
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

BASE = r"C:\Users\Utente\AppData\Local\Temp\opencode"
SHOTS = 8192
SEED = 20260805
NBLOCCHI_T1 = 4
BACKEND_QPU = "ibm_kingston"
# Piano open IBM 2026: 10 min di QPU time per finestra mobile di 28 giorni
# + bonus +180 min / 12 mesi (utenti attivi, >=20 min QPU in 12 mesi).
# Canale obbligatorio: ibm_cloud (ibm_quantum non piu' supportato).
OPEN_PLAN_SECONDS = 600          # 10 min QPU / finestra mobile 28 giorni
BONUS_OPEN_PLAN_SECONDS = 10800  # bonus +180 min / 12 mesi (utenti attivi)
# RESET_QPU = target temporale di submit del piano DEB (26/08/2026 20:05 UTC);
# la VERA quota si misura a runtime con service.usage() (dict: usage_consumed_seconds,
# usage_limit_seconds, usage_remaining_seconds, time_available_at).
RESET_QPU = datetime.datetime(2026, 8, 26, 20, 5, 0, tzinfo=datetime.timezone.utc)

sys.path.insert(0, BASE)

# ------------------------------------------------------------------ metriche
def mi_from_counts(counts):
    """MI_2x2 classica (bit logico: 0 = ground)."""
    P = np.zeros((2, 2))
    tot = 0
    for k, n in counts.items():
        b0 = int(k[0]); b1 = int(k[1])
        P[b0, b1] += n
        tot += n
    P = P / max(tot, 1)
    eps = 1e-15
    p0 = P.sum(axis=1); p1 = P.sum(axis=0)
    mi = 0.0
    for i in range(2):
        for j in range(2):
            den = p0[i] * p1[j] + eps
            if P[i, j] > eps:
                mi += P[i, j] * np.log2(P[i, j] / den)
    return float(mi)


def mi_partition(counts, qubitsA, qubitsB):
    """MI classica tra due partizioni/squitter (es. qubitsA=[0,1], qubitsB=[2]).
    Supporta qualsiasi raggruppamento; chiavi = bit string lunghezza n qui."""
    keysA = [k for i, k in enumerate(sorted(set(k for k in counts))) if True]
    # ricostruisco le chiavi dall'insieme dei counts (ordine di scrittura)
    seenA = {}
    seenB = {}
    joint = {}
    tot = 0
    for k, n in counts.items():
        a = "".join(k[i] for i in qubitsA)
        b = "".join(k[i] for i in qubitsB)
        seenA[a] = seenA.get(a, 0) + n
        seenB[b] = seenB.get(b, 0) + n
        joint[(a, b)] = joint.get((a, b), 0) + n
        tot += n
    eps = 1e-15
    mi = 0.0
    for (a, b), n in joint.items():
        pab = n / max(tot, 1)
        pa = seenA[a] / max(tot, 1)
        pb = seenB[b] / max(tot, 1)
        if pab > eps:
            mi += pab * np.log2(pab / (pa * pb + eps))
    return float(mi)


def n2q(ops):
    return int(ops.get("ecr", 0)) + int(ops.get("cz", 0))


def path_lunghezza2(edges, start):
    """Percorso [a,b,c] di lunghezza 2 nel grafo (per witness 3 qubit)."""
    nb = {a: set() for a, b in edges for a in (a, b)}
    for a, b in edges:
        nb[a].add(b); nb[b].add(a)
    cand = sorted(nb[start]) if nb.get(start) else None
    if cand:
        b = cand[int(len(cand) * start % len(cand))] if len(cand) > 1 else cand[0]
        for n2 in sorted(nb[start]):
            if n2 in nb and b in nb and n2 != b:
                pass
    for cnt in range(len(edges)):
        src = edges[cnt % len(edges)][0]
        if (start, src) in set(edges) or (src, start) in set(edges):
            for tip in sorted(nb[src]):
                if tip != start:
                    return [start, src, tip]
    return [start, edges[0][0] if start != edges[0][0] else edges[0][1],
            edges[-1][0]]


def path_lunghezza3(edges, start):
    """Catena di 4 qubit [a,b,c,d]."""
    nb = {a: set() for a, b in edges for a in (a, b)}
    for a, b in edges:
        nb[a].add(b); nb[b].add(a)
    for b in sorted(nb[start]):
        for c in sorted(nb[b] - {start}):
            for d in sorted(nb[c] - {b, start}):
                return [start, b, c, d]
    # fallback: coppie in fila
    return [start, sorted(nb[start])[0], start, sorted(nb[start])[0]]


# ------------------------------------------------------------------ circuiti
def build_bell(edges, rep=0):
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.cx(0, 1)
    qc.barrier()
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "BEL", "rep": int(rep)}
    return qc


def build_quenched(edges, kind, rep, rng=None):
    """1. QUENCHED_VS_ANNEALED (v2). PASM: H,H, cp(phi), H su q1 SOLO
    (base di misura XZ: rende la MI funzione di phi), rr. measure Z,Z.
    quenched: phi=pi FISSA (picco MI storica a pi).
    annealed: phi random uniforme in [0,2pi) per pub (miscela di fasi).
    Lettura brochure: MI_quenched ALTA vs MI_annealed AGGREGATA (somma dei
    counts -> stato misto) BASSA."""
    if kind == "quenched":
        phi = np.pi
    else:
        phi = float(rng.uniform(0, 2 * np.pi))
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.h(1)
    qc.cp(phi, 0, 1)
    qc.barrier()
    qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "QvA", "kind": kind, "rep": int(rep), "phi": float(phi)}
    return qc


def build_witness(edges, path, phi, rep):
    """2. MUTO_WITNESS: PAM 3 qubit (catena). cp(phi) su (0,1); H finale su
    q0,q1; q2 osservatore silenzioso (idle in |+>)."""
    q0, q1, q2 = path
    qc = QuantumCircuit(3, 3)
    qc.h(0); qc.h(1); qc.h(2)
    qc.barrier()
    qc.cp(phi, 0, 1)
    qc.barrier()
    qc.h(0); qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1); qc.measure(2, 2)
    qc.metadata = {"test": "MW", "phi": float(phi), "rep": int(rep),
                   "path": list(path)}
    return qc


def build_base_mista(edges, base, rep):
    """3. BASI_MISTE_XZ. Stato di Bell |Phi+> (H,CNOT) misurato in 4 basi.
    XX: H su entrambi; XZ: H su q0; ZX: H su q1; ZZ: nessuna.
    Brochure: MI_XX~0.72, XZ/ZX~0.04, ZZ<=0.002."""
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.cx(0, 1)
    qc.barrier()
    if "X" in base[0]:
        qc.h(0)
    if "X" in base[1]:
        qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "BM", "base": base, "rep": int(rep)}
    return qc


def build_livello2(edges, path, phi_a, phi_b, rep):
    """4. MI_LIVELLO2. Catena 4 qubit con 3 cp: (0,1),(1,2),(2,3).
    La partizione di destra comunica con la sinistra attraverso il filtro
    centrale: I(ab;cd) dovrebbe emergere. Baseline: angoli (0,0,0)."""
    a, b, c, d = path
    qc = QuantumCircuit(4, 4)
    qc.h(0); qc.h(1); qc.h(2); qc.h(3)
    qc.cp(phi_a, 0, 1)
    qc.barrier()
    qc.cp(phi_b, 1, 2)
    qc.barrier()
    qc.cp(phi_a, 2, 3)
    qc.barrier()
    qc.h(0); qc.h(1); qc.h(2); qc.h(3)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.measure(2, 2); qc.measure(3, 3)
    qc.metadata = {"test": "I2", "phi_a": float(phi_a), "phi_b": float(phi_b),
                   "rep": int(rep), "path": list(path)}
    return qc


def build_anomalia(edges, phi, eta, rep):
    """5. EMULA_ANOMALIA. PASM con iniezione Rz(eta*sin(phi)) su q0 dopo cp.
    Ratio R = MI(phi=+pi/3)/MI(phi=-pi/3)."""
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.h(1)
    qc.cp(phi, 0, 1)
    if abs(eta) > 1e-9:
        qc.rz(eta * np.sin(phi), 0)
    qc.barrier()
    qc.h(0); qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "AN", "phi": float(phi), "eta": float(eta),
                   "rep": int(rep)}
    return qc


def build_twirl(edges, kind, n, rep):
    """6. TWIRL_ZERO_MI. PASM cp(pi/2). no_twirl: senza frame; twirl: X*X
    attorno a cp (frame storico v3), poi n blocchi idle (delay) prima del
    cp; estrapolazione n=0."""
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.h(1)
    for _ in range(n):
        qc.barrier()
    if kind == "twirl":
        qc.x(0); qc.x(1)
        qc.cp(np.pi / 2, 0, 1)
        qc.x(0); qc.x(1)
    else:
        qc.cp(np.pi / 2, 0, 1)
    qc.barrier()
    qc.h(0); qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "TW", "kind": kind, "n": int(n), "rep": int(rep)}
    return qc


def build_frame(edges, phi, ramo, rep):
    """7. FRAME_SPLIT. PASM cp(phi) con controllo su q0 (ramo A) o q1 (B).
    AER: simmetria direzionale attesa Delta <= 0.004."""
    a, b = (0, 1) if ramo == "A" else (1, 0)
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.h(1)
    qc.cp(phi, a, b)
    qc.barrier()
    qc.h(0); qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "FS", "phi": float(phi), "ramo": ramo, "rep": int(rep)}
    return qc


def build_isofase(edges, ordine, rep):
    """8. ISOFASE_ORDINE_PERM. PASM: cp(a);bar;cp(b) con (a,b) =
    (pi/4,3pi/4) ordine A, (3pi/4,pi/4) ordine B, (0,0) baseline Z."""
    if ordine == "A":
        a, b = np.pi / 4, 3 * np.pi / 4
    elif ordine == "B":
        a, b = 3 * np.pi / 4, np.pi / 4
    else:
        a, b = 0.0, 0.0
    qc = QuantumCircuit(2, 2)
    qc.h(0); qc.h(1)
    qc.cp(a, 0, 1)
    qc.barrier()
    qc.cp(b, 0, 1)
    qc.barrier()
    qc.h(0); qc.h(1)
    qc.measure(0, 0); qc.measure(1, 1)
    qc.metadata = {"test": "IO", "ordine": ordine, "rep": int(rep)}
    return qc


# ------------------------------------------------------------------ costruzione PUB
def build_pubs(edges, rng):
    pares = list(edges)
    pair0 = [pares[0][0], pares[0][1]]
    path3 = path_lunghezza2(edges, pair0[0])
    path4 = path_lunghezza3(edges, pair0[0])

    pubs = []
    # varatura: Bell + PASM baseline
    pubs.append(build_bell(edges))
    # 1. QUENCHED_VS_ANNEALED (6+6)
    for i in range(6):
        pubs.append(build_quenched(edges, "quenched", i, rng=rng))
        pubs.append(build_quenched(edges, "annealed", i, rng=rng))
    # 2. MUTO_WITNESS (3*3 + pre)
    pubs.append(build_witness(edges, path3, np.pi / 2, 9))     # pre sentinella (MI01)
    for phi in (0.0, np.pi / 3, np.pi / 2):
        for rep in range(3):
            pubs.append(build_witness(edges, path3, phi, rep))
    # 3. BASI_MISTE_XZ (Bell in 4 basi x 3 rep)
    for base in ("XX", "XZ", "ZX", "ZZ"):
        for rep in range(3):
            pubs.append(build_base_mista(edges, base, rep))
    # 4. MI_LIVELLO2 (catena 4qb, 3 varianti x 2 rep)
    for (fa, fb) in ((np.pi / 2, np.pi / 2), (np.pi / 2, 0.0), (0.0, 0.0)):
        for rep in range(2):
            pubs.append(build_livello2(edges, path4, fa, fb, rep))
    # 5. EMULA_ANOMALIA (2*4 + baseline)
    pubs.append(build_anomalia(edges, 0.0, 0.0, 0))
    for sign in (1.0, -1.0):
        for eta in (0.0, 0.01, 0.03, 0.1):
            pubs.append(build_anomalia(edges, sign * np.pi / 3, eta, 0))
    # 6. TWIRL_ZERO_MI (no_twirl 4 + twirl 2 + baseline)
    for n in (0, 2, 4, 8):
        pubs.append(build_twirl(edges, "no_twirl", n, 0))
    for n in (0, 8):
        pubs.append(build_twirl(edges, "twirl", n, 0))
    # 7. FRAME_SPLIT (3 phi x 2 rami x 2 rep)
    for phi in (np.pi / 6, np.pi / 2, np.pi):
        for ramo in ("A", "B"):
            for rep in range(2):
                pubs.append(build_frame(edges, phi, ramo, rep))
    # 8. ISOFASE_ORDINE_PERM (2 ordini x 3 rep + baseline 0,0 x2)
    for ordine in ("A", "B"):
        for rep in range(3):
            pubs.append(build_isofase(edges, ordine, rep))
    for rep in range(2):
        pubs.append(build_isofase(edges, "Z", rep))
    return pubs, path3, path4, pair0


# ------------------------------------------------------------------ esecuzione AER
def run_aer(pubs, layouts, chunk=160):
    fake = FakeSherbrooke()
    sim = AerSimulator.from_backend(fake)
    sim.set_options(max_parallel_threads=8)
    tqs = []
    for p in pubs:
        tqs.append(transpile(p, backend=fake, optimization_level=1,
                             initial_layout=layouts[id(p)]))
    out = []
    for s in range(0, len(tqs), chunk):
        res = sim.run(tqs[s:s + chunk], shots=SHOTS).result()
        assert res.success
        for k in range(len(tqs[s:s + chunk])):
            out.append(res.get_counts(k))
    return out, tqs


def verifica_vincoli(tqs, pubs):
    attesi = []
    for p, q in zip(pubs, tqs):
        ops = q.count_ops()
        e2 = n2q(ops)
        sw = int(ops.get("swap", 0))
        attesi.append((str(p.metadata), e2, sw))
    ok = all(sw == 0 for _, _, sw in attesi)
    return ok, attesi


# ------------------------------------------- analisi per test
def _agg_mi(counts, sel):
    """MI calcolata sugli counts AGGREGATI dei pub selezionati (test 1)."""
    tot = {}
    for i in sel:
        for k, n in counts[i].items():
            tot[k] = tot.get(k, 0) + n
    return mi_from_counts(tot)


def analisi_quenched(mi, pubs, counts):
    """QUENCHED: fase fissa pi/2 (coerente). ANNEALED: fase random per pub.
    MI_aggregata: i 6 pub di una classe vengono uniti -> la somma dei counts
    smussa la fase e collassa la MI se annealed. Questa e' la lettura brochure."""
    d = {"quenched": [], "annealed": []}
    ids = {"quenched": [], "annealed": []}
    for i, p in enumerate(pubs):
        if p.metadata["test"] == "QvA":
            d[p.metadata["kind"]].append(mi[i])
            ids[p.metadata["kind"]].append(i)
    mq_sing = float(np.mean(d["quenched"]))
    ma_sing = float(np.mean(d["annealed"]))
    mq_agg = _agg_mi(counts, ids["quenched"])
    ma_agg = _agg_mi(counts, ids["annealed"])
    delta_sing = mq_sing - ma_sing
    delta_agg = mq_agg - ma_agg
    se_s = float(np.std(d["quenched"] + d["annealed"], ddof=1) /
                 np.sqrt(len(d["quenched"]) + len(d["annealed"]))) + 1e-12
    z_s = delta_sing / se_s if se_s > 0 else 0.0
    if delta_agg >= 0.10:
        v = ("VERDE (brochure supportata sui counts aggregati, base XZ): MI_quenched_agg=%.4f "
             "vs MI_annealed_agg=%.4f, Delta_agg=%.4f; singoli Delta=%.4f: la miscela "
             "di fase annealed collassa la MI -> metodo sensibile alla fase."
             % (mq_agg, ma_agg, delta_agg, delta_sing))
    elif delta_agg >= 0.03:
        v = ("AER REGISTRATO (contrasto debole): Delta_agg=%.4f, Delta_singoli=%.4f "
             "(z=%.1f): brochure va rimodulata con soglie piu' basse."
             % (delta_agg, delta_sing, z_s))
    else:
        v = ("ANOMALIA (AER non distingue): Delta_agg=%.4f (singoli %.4f): quenched e "
             "annealed indistinguibili." % (delta_agg, delta_sing))
    return {"verdetto": v, "MI_quenched_sing": round(mq_sing, 6),
            "MI_annealed_sing": round(ma_sing, 6),
            "MI_quenched_agg": round(mq_agg, 6), "MI_annealed_agg": round(ma_agg, 6),
            "Delta_sing": round(delta_sing, 6), "Delta_agg": round(delta_agg, 6),
            "z_sing": round(z_s, 2)}


def analisi_witness(mi, pubs):
    mi01 = mi02 = {}
    pre01 = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "MW":
            f = p.metadata["phi"]
            if f == np.pi / 2 and p.metadata["rep"] == 9:
                pre01 = {'mi01_calc': m}
    # MI(0,2) marginale: ricalcolo dai counts qualunque -> uso mi della coppia
    # corretta (qui misuriamo 3 qubit; mi 2x2 via mi_partition)
    med02 = {}
    for p, m in zip(pubs, mi):  # placeholder: sostituito sotto con mi_partition
        pass
    return {"verdetto": "IMPLEMENTAZIONE parziale margini (vedi report)", "pre01": pre01}


def analisi_basi(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "BM":
            d.setdefault(p.metadata["base"], []).append(m)
    med = {b: float(np.mean(x)) for b, x in d.items()}
    xx = med.get("XX", 0.0); xz = med.get("XZ", 0.0)
    zx = med.get("ZX", 0.0); zz = med.get("ZZ", 0.0)
    delta = xx - xz
    spread = float(np.max(list(med.values())) - np.min(list(med.values())))
    if delta >= 0.30 and xx >= 0.4:
        v = ("VERDE (intreccio distinguibile dalle basi): MI_XX=%.4f, MI_XZ=%.4f, "
             "MI_ZX=%.4f, MI_ZZ=%.4f, Delta_XX-XZ=%.4f: brochure XX~0.72 vs "
             "XZ/ZX~0.04, ZZ<=0.002 coerente." % (xx, xz, zx, zz, delta))
    elif delta <= 0.05:
        v = ("ANOMALIA (le basi non separano: Delta=%.4f, MI_XX=%.4f): MI_2x2 non "
             "dipende dalla base di misura -> metrica cieca all'intreccio."
             % (delta, xx))
    else:
        v = ("INDETERMINATO: Delta=%.4f in (0.05, 0.30), spread=%.4f."
             % (delta, spread))
    return {"verdetto": v, "MI_per_base": {b: round(m, 6) for b, m in med.items()},
            "Delta_XX_XZ": round(delta, 6), "spread": round(spread, 6)}


def analisi_livello2(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "I2":
            key = (round(p.metadata["phi_a"], 6), round(p.metadata["phi_b"], 6))
            d.setdefault(key, []).append(m)
    med = {k: float(np.mean(x)) for k, x in d.items()}
    fa, fb = round(np.pi / 2, 6), round(np.pi / 2, 6)
    za, zb = round(0.0, 6), round(0.0, 6)
    segnale = med.get((fa, fb), 0.0)
    base = med.get((za, zb), 0.0)
    delta = segnale - base
    if delta >= 0.010:
        v = ("VERDE (MI di 2 livello presente): I(ab;cd) su catena = %.4f vs base=%.4f, "
             "Delta=%.4f." % (segnale, base, delta))
    elif delta <= 0.002:
        v = ("ANOMALIA (2 livello nullo su AER: Delta=%.4f): I(ab;cd) non emerge "
             "nemmeno con filtro centrale -> test non appaltabile al QPU." % delta)
    else:
        v = "INDETERMINATO: Delta=%.4f in (0.002, 0.010)." % delta
    return {"verdetto": v, "I_varianti": {str(k): round(m, 6) for k, m in med.items()},
            "Delta_2liv_q2": round(delta, 6)}


def analisi_anomalia(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "AN":
            if p.metadata["phi"] == 0.0 and p.metadata["eta"] == 0.0:
                d.setdefault("base", []).append(m)
            elif p.metadata["phi"] > 0:
                d.setdefault("pos", {}).update({p.metadata["eta"]: m})
            elif p.metadata["phi"] < 0:
                d.setdefault("neg", {}).update({p.metadata["eta"]: m})
    pos = d.get("pos", {}); neg = d.get("neg", {})
    ratio, basev = {}, (d.get("base", [0.0])[0] if d.get("base") else 0.0)
    for eta in sorted(set(list(pos.keys()) + list(neg.keys()))):
        p_ = pos.get(eta, 0.0); n_ = neg.get(eta, 0.0)
        ratio[eta] = (p_ / n_) if n_ > 1e-12 else float("inf")
    sn = sorted(ratio.items())
    eta_star = next((e for e, r in sn if r >= 1.30), None)
    if basev <= 0.001 and sn and all(abs(r - 1.0) <= 0.05 for e, r in sn):
        v = ("VERDE (fondo simmetrico): tutti i ratio entro +/-0.05 di 1 "
             "(base MI=%.4f): nessuna asimmetria simulata; soglia QPU netta "
             "(eta*<=0.10 con R>=1.3 -> anomalia)." % basev)
    else:
        v = ("FONDO REGISTRATO (asimmetria residua su AER): ratio massimo deviato; "
             "usare i valori come fondo QPU." )
    return {"verdetto": v, "MI_pos": {str(k): round(ratio[k], 6) for k, _ in sn},
            "base_MI": round(basev, 6), "eta_star": eta_star,
            "ratio": {str(k): round(r, 5) for k, r in sn}}


def analisi_twirl(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "TW":
            d.setdefault(p.metadata["kind"], []).append((p.metadata["n"], m))
    fn = lambda kind: {n: m for n, m in d.get(kind, [])}
    nt = fn("no_twirl"); tw = fn("twirl")
    mi0_no = nt.get(0, 0.0); mi0_tw = tw.get(0, 0.0)
    if tw and nt and mi0_no > 0.02 and mi0_tw <= 0.35 * mi0_no:
        v = ("VERDE (twirl sopprime l'errore coerente): no_twirl n=0 MI=%.4f vs twirl "
             "MI=%.4f (ratio=%.2f). Brochure QPU: twirl estrapola l'errore di fase."
             % (mi0_no, mi0_tw, (mi0_tw / mi0_no if mi0_no else 1.0)))
    else:
        v = ("AER REGISTRATO: twirl n=0 MI=%.4f vs no_twirl MI=%.4f (ratio=%.2f): "
             "il frame non cancella l'errore simulato; usare il valore come fondo."
             % (mi0_tw, mi0_no, (mi0_tw / mi0_no if mi0_no else 1.0)))
    return {"verdetto": v, "no_twirl_n": {str(k): round(nm, 6) for k, nm in nt.items()},
            "twirl_n": {str(k): round(nm, 6) for k, nm in tw.items()}}


def analisi_frame(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "FS":
            d.setdefault((round(p.metadata["phi"], 6), p.metadata["ramo"]), 
                         []).append(m)
    rows = {}
    for phi in sorted({k[0] for k in d}):
        va = np.mean(d[(phi, "A")]); vb = np.mean(d[(phi, "B")])
        rows[str(round(phi, 6))] = (float(va), float(vb), float(abs(va - vb)))
    deltas = [r[2] for r in rows.values()]
    maxd = max(deltas) if deltas else 0.0
    if maxd <= 0.004:
        v = ("VERDE (simmetria direzionale): max |MI_A-MI_B|=%.4f <=0.004 su AER: "
             "nessuna asimmetria spuria; soglia QPU frame_split=0.020 conservativa."
             % maxd)
    elif maxd <= 0.020:
        v = ("AER REGISTRATO (asimmetria direzionale lieve): max=%.4f in (0.004,0.020]: "
             "fondo strumentale da riportare in brochure (soglia QPU ALZATA a 0.020)."
             % maxd)
    else:
        v = ("ANOMALIA (AER asimmetrico per direzione: max=%.4f >0.020): "
             "FakeSherbrooke distingue controllo/target -> soglia brochure invalida."
             % maxd)
    return {"verdetto": v, "frasi": rows}


def analisi_isofase(mi, pubs):
    d = {}
    for p, m in zip(pubs, mi):
        if p.metadata["test"] == "IO":
            d.setdefault(p.metadata["ordine"], []).append(m)
    mA = np.array(d.get("A", [])); mB = np.array(d.get("B", []))
    if len(mA) < 2 or len(mB) < 2:
        return {"verdetto": "DATI INSUFFICIENTI", "mA": mA.tolist(), "mB": mB.tolist()}
    delta = float(np.abs(np.mean(mA) - np.mean(mB)))
    allv = np.concatenate([mA, mB])
    nobs = delta
    rng_p = np.random.default_rng(SEED)
    nperm = 2000
    cnt = 0
    for _ in range(nperm):
        idx = rng_p.permutation(len(allv))
        da = np.mean(allv[idx[:len(mA)]])
        db = np.mean(allv[idx[len(mA):]])
        if abs(da - db) >= nobs:
            cnt += 1
    pval = (cnt + 1) / (nperm + 1)
    if delta <= 0.003 and pval > 0.05:
        v = ("VERDE (isofase indistinguibile): Delta=%.4f, p_perm=%.3f: i filtri "
             "(pi/4,3pi/4) e (3pi/4,pi/4) indistinguibili per il rumore."
             % (delta, pval))
    elif delta >= 0.020 and pval < 0.01:
        v = ("ANOMALIA (ordine discriminabile): Delta=%.4f, p_perm=%.3f: l'ordine "
             "degli intercalari produce impronta sul rumore." % (delta, pval))
    else:
        v = "INDETERMINATO: Delta=%.4f, p_perm=%.3f." % (delta, pval)
    return {"verdetto": v, "Delta_ordine": round(delta, 6), "p_perm": round(pval, 4),
            "MI_A": [round(x, 6) for x in mA], "MI_B": [round(x, 6) for x in mB]}


# ------------------------------------------------------------------ main dryrun
def main():
    rng = np.random.default_rng(SEED)
    fake = FakeSherbrooke()
    edges = fake.coupling_map.get_edges()
    print("FASE 4 AER (8 test concatenati): costruzione pubs...")
    pubs, path3, path4, pair0 = build_pubs(edges, rng)
    print("  %d pubs totali | path3=%s path4=%s pair0=%s"
          % (len(pubs), path3, path4, pair0))

    layouts = {id(p): (list(p.metadata.get("path", pair0))
                       if p.metadata["test"] in ("MW", "I2")
                       else [pair0[0], pair0[1]]) for p in pubs}

    print("Transpile opt=1 + run AerSimulator(FakeSherbrooke)...")
    counts, tqs = run_aer(pubs, layouts)
    ok, attesi = verifica_vincoli(tqs, pubs)
    if not ok:
        viol = [a for a in attesi if a[2] != 0]
        print("  VINCOLI VIOLATI (swap): %s" % viol[:10])
    else:
        print("  VINCOLI OK: nessun SWAP in %d pubs." % len(tqs))

    mi = [mi_from_counts(c) for c in counts]

    # metrize corrette per i test multi-qubit (witness: MI(0,2); livello2: I(ab;cd))
    mi_c = list(mi)
    for i, p in enumerate(pubs):
        if p.metadata["test"] == "MW":
            mi_c[i] = mi_partition(counts[i], [0], [2])
        elif p.metadata["test"] == "I2":
            mi_c[i] = mi_partition(counts[i], [0, 1], [2, 3])

    print("\n-- varatura (Bell) --")
    bell = [m for p, m in zip(pubs, mi) if p.metadata["test"] == "BEL"]
    bell_mi = bell[0] if bell else 0.0
    print("  Bell MI=%.4f (%s)" % (bell_mi, "OK" if bell_mi >= 0.4 else "FALLITA"))

    print("\n-- 1. QUENCHED_VS_ANNEALED --")
    r1 = analisi_quenched(np.array(mi_c), pubs, counts)
    print("  ", r1["verdetto"])

    print("\n-- 2. MUTO_WITNESS (MI 0-2 marginale) --")
    d02, d01 = {}, {}
    for p, m in zip(pubs, mi_c):
        if p.metadata["test"] == "MW":
            f = p.metadata["phi"]
            if p.metadata["rep"] == 9:
                d01[round(f, 6)] = m
            else:
                d02.setdefault(round(f, 6), []).append(m)
    pre01 = d01.get(round(np.pi / 2, 6), None)
    med02 = {k: float(np.mean(v)) for k, v in d02.items()}
    tot02 = max(med02.values()) if med02 else 0.0
    if med02:
        print("  MI(0,2) per phi: %s (max=%.4f)"
              % ({k: round(v, 6) for k, v in med02.items()}, tot02))
    else:
        print("  MI(0,2): nessun dato")
    if tot02 <= 0.003:
        r2v = ("VERDE (witness silenzioso): MI(0,2)<=0.003 su AER: nessun crosstalk "
               "spurio nel simulatore; soglia QPU pulita.")
    elif tot02 <= 0.015:
        r2v = ("AER REGISTRATO: MI(0,2)=%.4f: debole cross-talk nel simulatore; "
               "soglia QPU=0.020." % tot02)
    else:
        r2v = ("ANOMALIA (AER >0.015): il simulatore produce gi' MI(0,2) = %.4f; "
               "witness poco selettivo." % tot02)
    print("  ", r2v)
    r2 = {"verdetto": r2v, "MI02_per_phi": {k: round(v, 6) for k, v in med02.items()},
          "MI01_pre": round(pre01, 6) if pre01 is not None else None}

    print("\n-- 3. BASI_MISTE_XZ --")
    r3 = analisi_basi(np.array(mi_c), pubs)
    print("  ", r3["verdetto"])

    print("\n-- 4. MI_LIVELLO2 --")
    r4 = analisi_livello2(np.array(mi_c), pubs)
    print("  ", r4["verdetto"])

    print("\n-- 5. EMULA_ANOMALIA --")
    r5 = analisi_anomalia(np.array(mi_c), pubs)
    print("  ", r5["verdetto"])

    print("\n-- 6. TWIRL_ZERO_MI --")
    r6 = analisi_twirl(np.array(mi_c), pubs)
    print("  ", r6["verdetto"])

    print("\n-- 7. FRAME_SPLIT --")
    r7 = analisi_frame(np.array(mi_c), pubs)
    print("  ", r7["verdetto"])

    print("\n-- 8. ISOFASE_ORDINE_PERM --")
    r8 = analisi_isofase(np.array(mi_c), pubs)
    print("  ", r8["verdetto"])

    report = {
        "titolo": "FASE 4 AER: 8 test concatenati (fondo simulatore + brochure QPU)",
        "data": datetime.date.today().isoformat(),
        "metodo": "AerSimulator+FakeSherbrooke, %d shots, transpile opt=1" % SHOTS,
        "n_pubs": len(pubs),
        "varatura_bell": round(bell[0], 6) if bell else None,
        "QvA": r1,
        "MUTO_WITNESS": r2,
        "BASI_MISTE_XZ": r3,
        "MI_LIVELLO2": r4,
        "EMULA_ANOMALIA": r5,
        "TWIRL_ZERO_MI": r6,
        "FRAME_SPLIT": r7,
        "ISOFASE_ORDINE_PERM": r8,
        "count_ops_vincoli_ok": ok,
    }
    out = os.path.join(BASE, "n47lab_fase4_otto_test_aer_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nReport:", out)


# ------------------------------------------------------------------ QPU
def analisi_witness_qpu(mi, pubs):
    """Verdetto MUTO_WITNESS (mi gia' proiettato a I(0;2)); usa i pubs
    per distinguere la Rep sentinella (rep=9, phi=pi/2)."""
    d02, d01 = {}, {}
    for p, m in zip(pubs, mi):
        if p.metadata["rep"] == 9:
            d01[round(p.metadata["phi"], 6)] = m
        else:
            d02.setdefault(round(p.metadata["phi"], 6), []).append(m)
    pre = d01.get(round(np.pi / 2, 6), None)
    med = {k: float(np.mean(v)) for k, v in d02.items()}
    tot = max(med.values()) if med else 0.0
    if tot <= 0.003:
        v = "VERDE (witness silenzioso): MI(0,2)<=0.003, nessun crosstalk."
    elif tot <= 0.020:
        v = ("AER CONSISTENTE: MI(0,2)=%.4f in (0.003,0.020]: crosstalk debole." % tot)
    else:
        v = ("ANOMALIA: MI(0,2)=%.4f >0.020: crosstalk reale sul qubit "
             "osservatore." % tot)
    return {"verdetto": v, "MI02_per_phi": {k: round(x, 6) for k, x in med.items()},
            "MI01_pre": round(pre, 6) if pre is not None else None}


def _leggi_env():
    env = {}
    for line in open(os.path.join(BASE, ".env"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _mi_proiettati(counts_sel, pubs_sel):
    """Vettore MI per il singolo test (partizioni per MW e I2)."""
    out = []
    for c, p in zip(counts_sel, pubs_sel):
        if p.metadata["test"] == "MW":
            out.append(mi_partition(c, [0], [2]))
        elif p.metadata["test"] == "I2":
            out.append(mi_partition(c, [0, 1], [2, 3]))
        else:
            out.append(mi_from_counts(c))
    return np.array(out)


def _gate_varatura_ok():
    val = os.path.join(BASE, "n47lab_fase4_otto_test_aer_report.json")
    if not os.path.exists(val):
        print("STOP: report AER FASE 4 mancante (%s). Eseguire il dryrun." % val)
        return False
    rep = json.load(open(val, encoding="utf-8"))
    if rep.get("varatura_bell", 0) < 0.4 or not rep.get("count_ops_vincoli_ok"):
        print("STOP: varatura AER non superata (bell<0.4 o vincoli NOK).")
        return False
    return True


def main_preflight():
    token = (_leggi_env().get("IBM_API_TOKEN_2") or os.environ.get("IBM_OPEN", ""))
    if not token:
        print("ERRORE: token API2 (IBM_OPEN) mancante."); sys.exit(1)
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    service = QiskitRuntimeService(channel="ibm_cloud", token=token)
    backend = service.backend(BACKEND_QPU)
    pend = backend.status().pending_jobs
    edges = backend.coupling_map.get_edges()
    rng = np.random.default_rng(SEED)
    pubs, path3, path4, pair0 = build_pubs(edges, rng)
    layouts = {id(p): (list(p.metadata.get("path", pair0))
                       if p.metadata["test"] in ("MW", "I2")
                       else [pair0[0], pair0[1]]) for p in pubs}
    report = {"backend": BACKEND_QPU, "coda": int(pend), "layout": {
        "pair0": pair0, "path3": path3, "path4": path4}, "pubs": {"tot": len(pubs)}}
    for t in ("QvA", "MW", "BM", "I2", "AN", "TW", "FS", "IO"):
        sel = [p for p in pubs if p.metadata["test"] == t]
        qc_t = generate_preset_pass_manager(
            optimization_level=1, backend=backend,
            initial_layout=layouts[id(sel[0])]).run(sel)
        ops = [{k: v for k, v in q.count_ops().items()
                if k in ("cx", "ecr", "cz", "swap", "id")} for q in qc_t]
        sw = sum(o.get("swap", 0) for o in ops)
        report[t] = {"pubs": len(sel), "count_ops_primi3": ops[:3], "swap_tot": sw}
        print("%s: %d pubs, swap_tot=%d, 1o count_ops=%s"
              % (t, len(sel), sw, ops[0] if ops else None))
    out = os.path.join(BASE, "n47lab_fase4_preflight.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nReport preflight:", out)


def main_qpu():
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    if not _gate_varatura_ok():
        sys.exit(2)
    residuo = RESET_QPU - datetime.datetime.now(datetime.timezone.utc)
    print("Residuo quota: %s (reset %s)." % (residuo, RESET_QPU))
    if residuo < datetime.timedelta(minutes=2):
        print("STOP: meno di 2 minuti alla fine quota (reset non raggiunto).")
        sys.exit(2)
    token = (_leggi_env().get("IBM_API_TOKEN_2") or os.environ.get("IBM_OPEN", ""))
    if not token:
        print("ERRORE: token API2 mancante."); sys.exit(1)
    service = QiskitRuntimeService(channel="ibm_cloud", token=token)
    usage = service.usage()
    consumato = float(usage.get("usage_consumed_seconds", 0.0))
    limite = float(usage.get("usage_limit_seconds", OPEN_PLAN_SECONDS))
    rimanente = float(usage.get("usage_remaining_seconds", limite - consumato))
    reached = bool(usage.get("usage_limit_reached", False))
    t_available = usage.get("time_available_at", "n/d")
    bonus_attivo = limite > OPEN_PLAN_SECONDS
    print("Quota reale: consumati=%.1f s | limite=%d s | rimanenti=%.1f s | reached=%s"
          % (consumato, int(limite), rimanente, reached))
    print("Bonus +180 min: %s | time_available_at: %s" % ("ATTIVO" if bonus_attivo else "NON attivo", t_available))
    if reached or rimanente <= 0 or consumato >= limite:
        print("STOP: quota open plan esaurita (consumati=%.1f s >= limite=%d s%s)."
              % (consumato, int(limite), " + bonus" if bonus_attivo else ""))
        sys.exit(2)
    backend = service.backend(BACKEND_QPU)
    edges = backend.coupling_map.get_edges()
    rng = np.random.default_rng(SEED)
    pubs, path3, path4, pair0 = build_pubs(edges, rng)
    layouts = {id(p): (list(p.metadata.get("path", pair0))
                       if p.metadata["test"] in ("MW", "I2")
                       else [pair0[0], pair0[1]]) for p in pubs}
    FN = {"QvA": (analisi_quenched, ("counts",)),
          "MW": (analisi_witness_qpu, ()),
          "BM": (analisi_basi, ()),
          "I2": (analisi_livello2, ()),
          "AN": (analisi_anomalia, ()),
          "TW": (analisi_twirl, ()),
          "FS": (analisi_frame, ()),
          "IO": (analisi_isofase, ())}
    report = {"titolo": "FASE 4 QPU: 8 test concatenati", "backend": BACKEND_QPU,
              "shots": SHOTS, "data": datetime.date.today().isoformat()}
    for t in ("QvA", "MW", "BM", "I2", "AN", "TW", "FS", "IO"):
        if datetime.datetime.now(datetime.timezone.utc) > RESET_QPU:
            report["stop"] = "post_reset"
            break
        pend = backend.status().pending_jobs
        if pend >= 15:
            print("STOP: coda %d >= 15." % pend); report["stop"] = "coda"; break
        sel = [p for p in pubs if p.metadata["test"] == t]
        pm = generate_preset_pass_manager(optimization_level=1, backend=backend,
                                          initial_layout=layouts[id(sel[0])])
        qcs = pm.run(sel)
        sw = [q.count_ops().get("swap", 0) for q in qcs]
        if any(sw):
            print("STOP: %s contiene SWAP: INVALIDO." % t)
            report["stop"] = "swap_" + t; break
        print("Submit %s: %d pubs, coda=%d" % (t, len(sel), pend))
        sampler = SamplerV2(mode=backend)
        job = sampler.run(qcs, shots=SHOTS)
        res = job.result()
        counts_sel = [cr.data.c.get_counts() for cr in res]
        mi_sel = _mi_proiettati(counts_sel, sel)
        fn, extra = FN[t]
        kwargs = {"counts": counts_sel} if "counts" in extra else {}
        r = fn(mi_sel, sel, **kwargs) if "counts" in extra else fn(mi_sel, sel)
        r["job_id"] = job.job_id()
        report[t] = r
        print("  ", r["verdetto"])
    out = os.path.join(BASE, "n47lab_fase4_report_qpu.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nReport QPU:", out)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    if mode == "dryrun":
        main()
    elif mode == "preflight":
        main_preflight()
    elif mode == "qpu":
        main_qpu()
    else:
        print("Uso: python n47lab_fase4_otto_test_aer.py [dryrun|preflight|qpu]")
        sys.exit(1)