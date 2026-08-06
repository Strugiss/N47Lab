"""
echo_protocol_c8.py  —  Protocollo Echo Quantistico N4.1.6 (C8)
================================================================
Esperimento: CPhase(phi) forward -> tau/2 -> pi(M) -> tau/2 -> CPhase(phi) backward
Predizione:  I(tau) = I_imprint + I_noise * exp(-tau/T2*)

Basato su PASM validato su ibm_marrakesh (E16, 29/07/2026, MI=0.074936)
Autore: N47Lab — Fisica della Memoria Sub-Planckiana
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error
from scipy.optimize import curve_fit

# ===========================================================================
# CONFIGURAZIONE
# ===========================================================================
PHI = np.pi / 2
N_SHOTS = 8192
TAU_VALS_US = [0, 1, 3, 10, 30, 60, 100, 200, 350, 500]

T1_US = 200.0
T2_US = 150.0
GATE_ERR_1Q = 3e-4
GATE_ERR_2Q = 8e-3
DEPOL_ERR_1Q = 1e-3
DEPOL_ERR_2Q = 2e-3


# ===========================================================================
# CIRCUITI
# ===========================================================================
def echo_circuit(phi, tau_us=0):
    """
    Circuito SHARED: A e B condividono la stessa memoria M.
    Qubit: 0=A, 1=M, 2=B
    Misura: cr[0]=A, cr[1]=B  (M non misurata per MI)
    """
    qc = QuantumCircuit(3, 2)
    qc.h(0)
    qc.h(1)
    qc.h(2)

    # forward imprint
    qc.cp(phi, 0, 1)

    # echo sequence
    half = tau_us / 2.0
    if half > 0:
        qc.delay(half, qc.qubits, unit="us")
    qc.x(1)
    if half > 0:
        qc.delay(half, qc.qubits, unit="us")

    # backward imprint
    qc.cp(phi, 2, 1)

    # misura in base X
    qc.h(0)
    qc.h(2)

    qc.measure(0, 0)
    qc.measure(2, 1)

    qc.name = f"echo_tau_{tau_us:03d}us"
    qc.metadata = {"tau_us": tau_us, "type": "shared"}
    return qc


def control_circuit(phi, tau_us=0):
    """
    Circuito SEPARATE: A usa memoria M1 (q1), B usa memoria M2 (q3).
    4 qubit: 0=A, 1=M1, 2=B, 3=M2
    Misura: cr[0]=A, cr[1]=B
    """
    qc = QuantumCircuit(4, 2)

    # A con M1
    qc.h(0)
    qc.h(1)
    qc.cp(phi, 0, 1)

    # echo su A-M1
    half = tau_us / 2.0
    if half > 0:
        qc.delay(half, [0, 1], unit="us")
    qc.x(1)
    if half > 0:
        qc.delay(half, [0, 1], unit="us")

    qc.h(0)

    # B con M2
    qc.h(2)
    qc.h(3)
    qc.cp(phi, 2, 3)

    if half > 0:
        qc.delay(half, [2, 3], unit="us")
    qc.x(3)
    if half > 0:
        qc.delay(half, [2, 3], unit="us")

    qc.h(2)

    qc.measure(0, 0)
    qc.measure(2, 1)

    qc.name = f"ctrl_tau_{tau_us:03d}us"
    qc.metadata = {"tau_us": tau_us, "type": "separate"}
    return qc


# ===========================================================================
# MUTUA INFORMAZIONE
# ===========================================================================
def mi_from_counts(counts, n_clbits_total=2):
    """
    Calcola MI(A:B) da counts dictionary.
    counts keys: bitstring little-endian (cr[0] = rightmost bit).
    n_clbits_total: numero di bit misurati (default=2: cr[0]=A, cr[1]=B).
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0

    p_ab = {}
    for bits, c in counts.items():
        a = bits[-1]  # cr[0] = rightmost = A
        b = bits[-2] if n_clbits_total >= 2 else "0"  # cr[1] = B
        p_ab[(a, b)] = p_ab.get((a, b), 0) + c / total

    p_a = {}
    p_b = {}
    for (a, b), p in p_ab.items():
        p_a[a] = p_a.get(a, 0) + p
        p_b[b] = p_b.get(b, 0) + p

    def entropy(dist):
        vals = np.array(list(dist.values()))
        vals = vals[vals > 0]
        return -np.sum(vals * np.log2(vals))

    h_a = entropy(p_a)
    h_b = entropy(p_b)
    h_ab = entropy(p_ab)

    return max(0.0, h_a + h_b - h_ab)


# ===========================================================================
# MODELLO RUMORE
# ===========================================================================
def build_noise_model(t1=T1_US, t2=T2_US, d1=DEPOL_ERR_1Q, d2=DEPOL_ERR_2Q):
    nm = NoiseModel()
    for q in range(4):
        nm.add_quantum_error(
            thermal_relaxation_error(t1 * 1e-3, t2 * 1e-3, 0.01),
            ["delay"], [q]
        )
    nm.add_all_qubit_quantum_error(depolarizing_error(d2, 2), ["cp"])
    nm.add_all_qubit_quantum_error(depolarizing_error(d1, 1), ["h", "x"])
    return nm


# ===========================================================================
# ESECUZIONE
# ===========================================================================
def run_simulation():
    nm = build_noise_model()
    sim = AerSimulator(noise_model=nm)

    shared_res = {}
    separate_res = {}

    for tau in TAU_VALS_US:
        qc = echo_circuit(PHI, tau)
        ct = control_circuit(PHI, tau)
        qc_t = transpile(qc, sim)
        ct_t = transpile(ct, sim)

        r1 = sim.run(qc_t, shots=N_SHOTS).result()
        r2 = sim.run(ct_t, shots=N_SHOTS).result()

        mi_sh = mi_from_counts(r1.get_counts(0))
        mi_se = mi_from_counts(r2.get_counts(0))
        shared_res[tau] = mi_sh
        separate_res[tau] = mi_se

        print(f"tau={tau:4d} us  MI_shared={mi_sh:.6f}  MI_sep={mi_se:.6f}  "
              f"Delta={mi_sh - mi_se:.6f}")

    return shared_res, separate_res


def run_qpu(backend_name="ibm_marrakesh"):
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

    print(f"Connessione a {backend_name}...")
    service = QiskitRuntimeService()
    backend = service.backend(backend_name)

    circuits = [echo_circuit(PHI, t) for t in TAU_VALS_US]
    circuits_t = transpile(circuits, backend)

    sampler = Sampler(mode=backend)
    job = sampler.run(circuits_t, shots=N_SHOTS)
    print(f"Job inviato: {job.job_id()}")

    results = job.result()
    res = {}
    for i, tau in enumerate(TAU_VALS_US):
        dist = results[i].data.meas.get_counts()
        mi = mi_from_counts(dist)
        res[tau] = mi
        print(f"tau={tau:4d} us  MI={mi:.6f}")
    return res


# ===========================================================================
# FIT I(tau) = I_imprint + I_noise * exp(-tau / T2*)
# ===========================================================================
def fit_echo(tau_vals, mi_vals):
    def model(t, i_imprint, i_noise, t2):
        return i_imprint + i_noise * np.exp(-np.array(t) / t2)

    p0 = [0.005, 0.070, 80.0]
    bounds = ([0, 0, 1], [0.1, 0.1, 500])
    try:
        popt, pcov = curve_fit(model, tau_vals, mi_vals, p0=p0,
                               bounds=bounds, maxfev=5000)
        perr = np.sqrt(np.diag(pcov))
        return popt, perr
    except Exception as e:
        print(f"Fit fallito: {e}")
        return None, None


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "sim"

    if mode == "qpu":
        res = run_qpu()
    else:
        shared, separate = run_simulation()

        print("\n" + "=" * 65)
        print("  FIT:  I(tau) = I_imprint + I_noise * exp(-tau / T2*)")
        print("=" * 65)

        tau_arr = np.array(TAU_VALS_US)
        mi_arr = np.array(list(shared.values()))
        popt, perr = fit_echo(tau_arr, mi_arr)

        if popt is not None:
            i_im, i_no, t2 = popt
            e_im, e_no, e_t2 = perr
            print(f"  I_imprint = {i_im:.6f} +/- {e_im:.6f} bits")
            print(f"  I_noise   = {i_no:.6f} +/- {e_no:.6f} bits")
            print(f"  T2*       = {t2:.1f} +/- {e_t2:.1f} us")
            print(f"  I(0)      = {i_im + i_no:.6f} bits")
            print(f"  I(inf)    = {i_im:.6f} bits")

            if i_im > 3 * e_im and i_im > 1e-4:
                print("\n  >>> EVIDENZA di imprint irreversibile (I_imprint > 3sigma) <<<")
            else:
                print("\n  >>> Solo rumore reversibile (I_imprint non significativo) <<<")

        print("\n" + "=" * 65)
        print(f"  {'tau(us)':>8s}  {'MI_shared':>10s}  {'MI_sep':>10s}  {'Delta':>10s}")
        print("  " + "-" * 42)
        for t in TAU_VALS_US:
            print(f"  {t:8d}  {shared[t]:10.6f}  {separate[t]:10.6f}  "
                  f"{shared[t] - separate[t]:10.6f}")
