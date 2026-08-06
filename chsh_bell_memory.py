"""
chsh_bell_memory.py  —  CHSH Bell Test con Memoria Condivisa (PASM)
===================================================================
Esperimento: CHSH tra due sistemi (A, B) dopo interazione PASM con
memoria condivisa M.  3 qubit (A, M, B) + 1 ancilla.

Backend : ibm_marrakesh
Shots   : 16384

Angoli CHSH (4 combinazioni standard):
  E(a,b)   = E(θ_A=0,    θ_B=π/4)
  E(a,b')  = E(θ_A=0,    θ_B=3π/4)
  E(a',b)  = E(θ_A=π/2,  θ_B=π/4)
  E(a',b') = E(θ_A=π/2,  θ_B=3π/4)
  S = E(a,b) - E(a,b') + E(a',b) + E(a',b')

Predizioni:
  φ = π/2   →  S < 2.0      (correlazione classica — CHSH non violato)
  φ = π     →  S ≈ 2.828    (violazione quantistica massima CHSH)

Autore: N47Lab — Fisica della Memoria Sub-Planckiana
"""

import os
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler


# ===========================================================================
# CONFIGURAZIONE
# ===========================================================================
def _leggi_env():
    """Legge il .env N47Lab (temp opencode) senza esporre segreti."""
    env = {}
    for base in (
        r"C:\Users\Utente\AppData\Local\Temp\opencode",
        os.path.dirname(os.path.abspath(__file__)),
    ):
        p = os.path.join(base, ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    return env

_env = _leggi_env()
API_TOKEN = _env.get("IBM_API_TOKEN_1") or _env.get("IBM_API_TOKEN") or ""
CRN = _env.get("IBM_CRN_1") or _env.get("IBM_CRN") or ""
BACKEND = "ibm_marrakesh"
N_SHOTS = 16384

# Angoli CHSH: coppie (theta_A, theta_B) per le 4 correlazioni
ANGLES = [
    (0.0, np.pi / 4),       # (a, b)
    (0.0, 3 * np.pi / 4),   # (a, b')
    (np.pi / 2, np.pi / 4), # (a', b)
    (np.pi / 2, 3 * np.pi / 4), # (a', b')
]
LABELS = ["E(a,b)", "E(a,b')", "E(a',b)", "E(a',b')"]

PHI_VALS = [np.pi / 2, np.pi]  # φ da testare


# ===========================================================================
# CIRCUITO PASM + CHSH
# ===========================================================================
def pasm_chsh_circuit(phi, theta_A, theta_B):
    """
    Circuito a 4 qubit + 2 classical bit.

    Layout qubit:
      q0 = Alice (A)
      q1 = Memoria condivisa (M)
      q2 = Bob (B)
      q3 = Ancilla

    Misura: cr[0] = A, cr[1] = B

    Sequenza:
      1. H su tutti
      2. forward CP(phi)  A->M, ancilla->M
      3. echo X su M
      4. backward CP(phi) B->M, ancilla->M
      5. rotazione basi CHSH su A e B
      6. misura A, B
    """
    qc = QuantumCircuit(4, 2)

    # === PASM: preparazione stato con memoria condivisa ===
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.h(3)

    # forward imprint: A ed ancilla scrivono su M
    qc.cp(phi, 0, 1)
    qc.cp(phi, 3, 1)

    # echo pulse su M (protezione da rumore)
    qc.x(1)

    # backward imprint: B ed ancilla rileggono da M
    qc.cp(phi, 2, 1)
    qc.cp(phi, 3, 1)

    # === CHSH: rotazione basi di misura ===
    qc.rz(theta_A, 0)
    qc.h(0)
    qc.rz(theta_B, 2)
    qc.h(2)

    qc.measure(0, 0)
    qc.measure(2, 1)

    qc.name = f"pasm_{phi:.3f}_chsh_{theta_A:.3f}_{theta_B:.3f}"
    qc.metadata = {
        "phi": float(phi),
        "theta_A": float(theta_A),
        "theta_B": float(theta_B),
        "type": "pasm_chsh",
    }
    return qc


# ===========================================================================
# ANALISI DATI
# ===========================================================================
def compute_E(counts):
    """
    Correlazione E = P(00) + P(11) - P(01) - P(10)
    counts keys: little-endian, e.g. '01' = cr[0]=1, cr[1]=0
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p00 = counts.get("00", 0) / total
    p01 = counts.get("01", 0) / total
    p10 = counts.get("10", 0) / total
    p11 = counts.get("11", 0) / total
    return p00 + p11 - p01 - p10


def compute_E_error(counts):
    """Errore statistico su E per propagazione binomiale."""
    total = sum(counts.values())
    if total == 0:
        return 1.0
    p00 = counts.get("00", 0) / total
    p01 = counts.get("01", 0) / total
    p10 = counts.get("10", 0) / total
    p11 = counts.get("11", 0) / total
    var = (p00 * (1 - p00) + p01 * (1 - p01)
           + p10 * (1 - p10) + p11 * (1 - p11)) / total
    return np.sqrt(var)


def compute_S_from_counts(counts_list):
    """Calcola S = E0 - E1 + E2 + E3 da lista di 4 distribuzioni."""
    E_vals = []
    E_errs = []
    for counts in counts_list:
        E_vals.append(compute_E(counts))
        E_errs.append(compute_E_error(counts))

    S = E_vals[0] - E_vals[1] + E_vals[2] + E_vals[3]
    # errore: var(S) = sum(var(E_i)) (indipendenti)
    S_err = np.sqrt(sum(e ** 2 for e in E_errs))

    return E_vals, E_errs, S, S_err


# ===========================================================================
# ESECUZIONE SU QPU
# ===========================================================================
def run_chsh_qpu(phi):
    """Esegue CHSH per un dato φ su ibm_marrakesh."""
    service = QiskitRuntimeService(
        channel="ibm_cloud",
        token=API_TOKEN,
        instance=CRN,
    )
    backend = service.backend(BACKEND)

    circuits = []
    for theta_A, theta_B in ANGLES:
        qc = pasm_chsh_circuit(phi, theta_A, theta_B)
        circuits.append(qc)

    circuits_t = transpile(circuits, backend)

    print(f"\n  Invio {len(circuits)} circuiti per φ={phi:.4f} ...")
    sampler = Sampler(mode=backend)
    job = sampler.run(circuits_t, shots=N_SHOTS)
    print(f"  Job ID: {job.job_id()}")

    results = job.result()

    counts_list = []
    for i in range(4):
        dist = results[i].data.meas.get_counts()
        counts_list.append(dist)

    E_vals, E_errs, S, S_err = compute_S_from_counts(counts_list)
    return E_vals, E_errs, S, S_err


# ===========================================================================
# ESECUZIONE LOCALE (simulatore rumoroso, per test)
# ===========================================================================
def run_chsh_sim(phi):
    """Esegue CHSH in simulazione locale con rumore realistico."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error

    nm = NoiseModel()
    for q in range(4):
        nm.add_quantum_error(
            thermal_relaxation_error(200e-3, 150e-3, 0.01),
            ["delay"], [q],
        )
    nm.add_all_qubit_quantum_error(depolarizing_error(8e-3, 2), ["cp"])
    nm.add_all_qubit_quantum_error(depolarizing_error(3e-4, 1), ["h", "x", "rz"])

    sim = AerSimulator(noise_model=nm)

    circuits = []
    for theta_A, theta_B in ANGLES:
        qc = pasm_chsh_circuit(phi, theta_A, theta_B)
        circuits.append(qc)

    circuits_t = transpile(circuits, sim)

    counts_list = []
    for qc_t in circuits_t:
        result = sim.run(qc_t, shots=N_SHOTS).result()
        counts_list.append(result.get_counts(0))

    E_vals, E_errs, S, S_err = compute_S_from_counts(counts_list)
    return E_vals, E_errs, S, S_err


# ===========================================================================
# REPORT
# ===========================================================================
def print_report(phi, E_vals, E_errs, S, S_err):
    """Stampa risultati CHSH per un dato φ."""
    print(f"\n  {'=' * 55}")
    print(f"  RISULTATI CHSH — φ = {phi:.4f}")
    print(f"  {'=' * 55}")
    for i, label in enumerate(LABELS):
        print(f"    {label:>8s} = {E_vals[i]:+8.5f} ± {E_errs[i]:.5f}")
    print(f"  {'─' * 40}")
    print(f"    S          = {S:+8.5f} ± {S_err:.5f}")

    # Test ipotesi nulla: H0: S = 2 (classico)
    if S > 2.0:
        sigma = (S - 2.0) / S_err if S_err > 0 else 0
        print(f"    S - 2      = {S - 2.0:+8.5f}  ({sigma:.1f}σ)")
        if sigma >= 3:
            print(f"    >>> VIOLAZIONE CHSH a {sigma:.1f}σ <<<")
        else:
            print(f"    >>> Indizio di violazione, ma < 3σ <<<")
    else:
        print(f"    S - 2      = {S - 2.0:+8.5f}")
        print(f"    >>> NESSUNA violazione CHSH (S < 2) <<<")

    # Predizione
    if abs(phi - np.pi / 2) < 1e-6:
        pred_str = "S < 2 (classico)"
        if S < 2.0:
            print(f"    ✅ PREDIZIONE CONFERMATA: {pred_str}")
        else:
            print(f"    ⚠️  PREDIZIONE NON CONFERMATA: atteso {pred_str}")
    elif abs(phi - np.pi) < 1e-6:
        target = 2 * np.sqrt(2)
        pred_str = f"S ≈ {target:.3f} (massima violazione quantistica)"
        if abs(S - target) < 3 * S_err:
            print(f"    ✅ COMPATIBILE con {pred_str}")
        else:
            print(f"    ⚠️  ATTESO {pred_str}, osservato S = {S:.4f}")

    print()


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "qpu"
    runner = {"qpu": run_chsh_qpu, "sim": run_chsh_sim}
    run_fn = runner.get(mode, run_chsh_qpu)

    print("=" * 60)
    print("  CHSH BELL TEST con Memoria Condivisa (PASM)")
    print(f"  Backend: {BACKEND if mode == 'qpu' else 'AerSimulator'}")
    print(f"  Shots:   {N_SHOTS}")
    print(f"  Modalità: {mode}")
    print("=" * 60)

    for phi in PHI_VALS:
        phi_label = f"φ = π/2" if abs(phi - np.pi / 2) < 1e-6 else f"φ = π"
        print(f"\n  >>> {phi_label}")
        E_vals, E_errs, S, S_err = run_fn(phi)
        print_report(phi, E_vals, E_errs, S, S_err)


if __name__ == "__main__":
    main()
