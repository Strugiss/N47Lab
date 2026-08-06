"""
entanglement_witness_pasm.py  —  Witness di Entanglement su PASM φ=π/2
====================================================================
Esperimento: 3 qubit (A, B, M). PASM φ=π/2 crea memoria condivisa.
            Witness: W = ⟨XX⟩ + ⟨YY⟩ + ⟨ZZ⟩ su A,B.
Predizione:  W ≈ 0  (correlazione classica, nessun entanglement).
Soglia:      W < -1 → entanglement certificato.

Backend:     ibm_marrakesh (Heron r2, 156 qubit)
Shot:        8192

N47Lab — Fisica della Memoria Sub-Planckiana
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp
import argparse, time, json

# ===========================================================================
# CONFIG
# ===========================================================================
PHI = np.pi / 2
N_SHOTS = 8192
BACKEND_NAME = "ibm_marrakesh"

# Layout logico: q[0]=A, q[1]=M, q[2]=B
A, M, B = 0, 1, 2


# ===========================================================================
# PASM CIRCUIT  (φ = π/2, τ = 0)
# ===========================================================================
def pasm_circuit(phi=PHI):
    """
    Circuito PASM: shared memory tra A e B via M.
    Fasi:
      1. H su A, M, B
      2. CP(phi, A, M)   — forward imprint
      3. X(M)            — echo refocusing
      4. CP(phi, B, M)   — backward imprint
    Nessuna misura (l'Estimator calcola i valori d'aspettazione).
    """
    qc = QuantumCircuit(3)
    qc.h(A); qc.h(M); qc.h(B)
    qc.cp(phi, A, M)
    qc.x(M)
    qc.cp(phi, B, M)
    qc.name = "PASM_phi_pi2"
    qc.metadata = {"phi": phi, "type": "pasm_shared"}
    return qc


# ===========================================================================
# WITNESS OPERATOR
# ===========================================================================
def build_witness():
    """
    Operatore witness W = X_A X_B + Y_A Y_B + Z_A Z_B
    Su 3 qubit (A, M, B) con l'identità su M.
    Ordine dei qubit: q[0]=A, q[1]=M, q[2]=B
    → Pauli string:  "XIX", "YIY", "ZIZ"
    """
    return SparsePauliOp.from_list([
        ("XIX", 1.0),
        ("YIY", 1.0),
        ("ZIZ", 1.0),
    ])


def build_individual_observables():
    """Restituisce i tre operatori XX, YY, ZZ separati (per diagnostica)."""
    return {
        "XX": SparsePauliOp("XIX"),
        "YY": SparsePauliOp("YIY"),
        "ZZ": SparsePauliOp("ZIZ"),
    }


# ===========================================================================
# ANALISI
# ===========================================================================
def analyze(w_val, xx_val, yy_val, zz_val, std_err=None):
    """
    Analizza il risultato del witness.
    W < -1 → entanglement.
    """
    sep_threshold = -1.0

    report = {
        "W": float(w_val),
        "XX": float(xx_val),
        "YY": float(yy_val),
        "ZZ": float(zz_val),
        "std_err": float(std_err) if std_err is not None else None,
        "W < -1?": w_val < sep_threshold,
        "entanglement_detected": w_val < sep_threshold,
        "threshold": sep_threshold,
        "prediction": "W ~ 0 (classical correlations, no entanglement)",
        "verdict": "",
    }

    if w_val < sep_threshold:
        report["verdict"] = (
            f"ENTANGLEMENT RILEVATO: W = {w_val:.4f} < {sep_threshold}. "
            "La memoria condivisa PASM genera correlazioni quantistiche."
        )
    else:
        report["verdict"] = (
            f"NESSUN ENTANGLEMENT: W = {w_val:.4f} >= {sep_threshold}. "
            f"Correlazioni classiche dominate dal rumore. W ~ {w_val:.4f}"
        )

    return report


# ===========================================================================
# ESECUZIONE — SIMULATORE
# ===========================================================================
def run_simulation():
    """Esecuzione locale con StatevectorEstimator (senza rumore)."""
    from qiskit.primitives import StatevectorEstimator as Estimator

    print("\n[STATO] Simulazione statevector (ideale, 0 rumore)")
    qc = pasm_circuit()
    obs = build_witness()

    estimator = Estimator()
    job = estimator.run([(qc, obs)])
    result = job.result()[0]
    evs = result.data.evs
    w_val = float(evs.flatten()[0]) if hasattr(evs, 'flatten') else float(evs)
    std_err = None

    # Componenti singole
    comps = build_individual_observables()
    vals = {}
    for name, op in comps.items():
        j = estimator.run([(qc, op)]).result()[0]
        v = j.data.evs
        vals[name] = float(v.flatten()[0]) if hasattr(v, 'flatten') else float(v)

    report = analyze(w_val, vals["XX"], vals["YY"], vals["ZZ"], std_err)
    report["stds"] = {
        "W": float(std_err) if std_err is not None else 0.0,
    }

    _stampa_report(report)
    return report


# ===========================================================================
# ESECUZIONE — QPU
# ===========================================================================
def run_qpu(instance=None):
    """Esecuzione su ibm_marrakesh via EstimatorV2."""
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator

    print(f"\n[STATO] Connessione a {BACKEND_NAME}...")
    service = QiskitRuntimeService(channel="ibm_cloud", instance=instance)
    backend = service.backend(BACKEND_NAME)

    # Costruisci e transpila
    qc = pasm_circuit()
    obs = build_witness()

    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    isa_qc = pm.run(qc)
    isa_obs = obs.apply_layout(isa_qc.layout)

    print(f"[STATO] Circuit transpilato: {isa_qc.num_qubits} qubit fisici, "
          f"profondità={isa_qc.depth()}")

    # Esegui
    estimator = Estimator(mode=backend, options={"default_shots": N_SHOTS})
    pub = (isa_qc, isa_obs)
    job = estimator.run([pub])
    print(f"[JOB] Inviato: {job.job_id()}")
    print(f"[JOB] Attesa risultati...")

    result = job.result()[0]
    evs = result.data.evs
    w_val = float(evs.flatten()[0]) if hasattr(evs, 'flatten') else float(evs)
    std_err = None

    # Componenti
    comps = build_individual_observables()
    vals = {}
    for name, op in comps.items():
        isa_comp = op.apply_layout(isa_qc.layout)
        j = estimator.run([(isa_qc, isa_comp)]).result()[0]
        v = j.data.evs
        vals[name] = float(v.flatten()[0]) if hasattr(v, 'flatten') else float(v)

    report = analyze(w_val, vals["XX"], vals["YY"], vals["ZZ"], std_err)
    report["job_id"] = job.job_id()
    report["backend"] = BACKEND_NAME
    report["shots"] = N_SHOTS
    report["transpiled_depth"] = isa_qc.depth()
    report["transpiled_qubits"] = isa_qc.num_qubits

    _stampa_report(report)
    return report


# ===========================================================================
# OUTPUT
# ===========================================================================
def _stampa_report(report):
    print("\n" + "=" * 60)
    print("  REPORT - ENTANGLEMENT WITNESS PASM phi=pi/2")
    print("=" * 60)
    print(f"  W  = <XX> + <YY> + <ZZ>  =  {report['W']:.6f}")
    print(f"  <XX> = {report['XX']:.6f}")
    print(f"  <YY> = {report['YY']:.6f}")
    print(f"  <ZZ> = {report['ZZ']:.6f}")
    if report.get("std_err"):
        print(f"  sigma(W) = {report['std_err']:.6f}")
    print(f"  Soglia entanglement: W < {report['threshold']}")
    print(f"  W < -1 ? {report['W < -1?']}")
    print(f"  Predizione: {report['prediction']}")
    print(f"  Verdetto: {report['verdict']}")
    print("=" * 60)


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Entanglement Witness su PASM φ=π/2 (ibm_marrakesh)"
    )
    parser.add_argument(
        "mode", nargs="?", default="sim",
        choices=["sim", "qpu"],
        help="'sim' = simulatore (default) | 'qpu' = ibm_marrakesh"
    )
    parser.add_argument("--instance", default=None,
                        help="IBM Cloud CRN instance (opzionale)")
    args = parser.parse_args()

    print("=" * 55)
    print("  ENTANGLEMENT WITNESS  —  PASM phi = pi/2")
    print("  N47Lab  |  Fisica della Memoria Sub-Planck")
    print("=" * 55)

    print(f"  Qubit:  A (q{A}) - M (q{M}) - B (q{B})")
    print(f"  phi = pi/2   Shot = {N_SHOTS}")
    print(f"  Witness: W = <XX> + <YY> + <ZZ>")
    print(f"  Soglia:  W < -1 -> entanglement")
    print(f"  Predizione: W ~ 0 (solo correlazione classica)")

    t0 = time.time()

    if args.mode == "qpu":
        report = run_qpu(instance=args.instance)
    else:
        report = run_simulation()

    elapsed = time.time() - t0
    print(f"\n  Tempo totale: {elapsed:.1f} s")

    # Salva report
    fname = f"witness_report_{args.mode}_{int(t0)}.json"
    with open(fname, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report salvato: {fname}")

    return report


if __name__ == "__main__":
    main()
