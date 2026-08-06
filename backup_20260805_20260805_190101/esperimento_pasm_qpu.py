"""
N47Lab — PASM (Phase Accumulation in Shared Memory) su IBM QPU
Protocollo definitivo: CPhase(phi=pi/2) su memoria condivisa
Confronto: shared vs separate
Metrica: Mutua Informazione I(field0:field2)
"""
import os
import numpy as np
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

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
PHI = np.pi / 2
SHOTS = 8192

def calc_mi(cnt, nq, qi, qj):
    shots = sum(cnt.values()) or 1
    pk = {k: v/shots for k,v in cnt.items()}
    p00 = sum(v for k,v in pk.items() if k[nq-1-qi]=='0' and k[nq-1-qj]=='0')
    p01 = sum(v for k,v in pk.items() if k[nq-1-qi]=='0' and k[nq-1-qj]=='1')
    p10 = sum(v for k,v in pk.items() if k[nq-1-qi]=='1' and k[nq-1-qj]=='0')
    p11 = sum(v for k,v in pk.items() if k[nq-1-qi]=='1' and k[nq-1-qj]=='1')
    def H(ps):
        ps = [x for x in ps if x>0]
        return -sum(x*np.log2(x) for x in ps)
    return H([p00+p01, p10+p11]) + H([p00+p10, p01+p11]) - H([p00,p01,p10,p11])

print("="*60)
print("N47Lab - PASM su ibm_fez")
print("="*60)

# Circuito SHARED: 2 field su STESSA memoria
qc_s = QuantumCircuit(3, 2)
qc_s.h(0); qc_s.h(2); qc_s.h(1)
qc_s.cp(PHI, 0, 1)
qc_s.barrier()
qc_s.cp(PHI, 2, 1)
qc_s.barrier()
qc_s.h(0); qc_s.h(2)
qc_s.measure(0, 0); qc_s.measure(2, 1)
qc_s.name = "pasm_shared"

# Circuito SEPARATE: 2 field su memorie DIVERSE
qc_p = QuantumCircuit(4, 2)
qc_p.h(0); qc_p.h(2); qc_p.h(1); qc_p.h(3)
qc_p.cp(PHI, 0, 1)
qc_p.barrier()
qc_p.cp(PHI, 2, 3)
qc_p.barrier()
qc_p.h(0); qc_p.h(2)
qc_p.measure(0, 0); qc_p.measure(2, 1)
qc_p.name = "pasm_separate"

# Connessione
service = QiskitRuntimeService(channel='ibm_cloud', token=API_TOKEN, instance=CRN)
backend = service.backend("ibm_fez")
print(f"Backend: {backend.name}")
print(f"Qubits: {backend.num_qubits}")

# Transpila
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
qc_s_t = pm.run(qc_s)
qc_p_t = pm.run(qc_p)

print(f"Shared depth: {qc_s_t.depth()}, gates: {qc_s_t.count_ops()}")
print(f"Separate depth: {qc_p_t.depth()}, gates: {qc_p_t.count_ops()}")

# Esegui
sampler = SamplerV2(backend)
job = sampler.run([qc_s_t, qc_p_t], shots=SHOTS)
print(f"Job inviato! ID: {job.job_id()}")
print("Attesa risultati...")

result = job.result()
cs = result[0].data.c.get_counts()
cp = result[1].data.c.get_counts()

mi_s = calc_mi(cs, 2, 0, 1)
mi_p = calc_mi(cp, 2, 0, 1)

print("\n" + "="*60)
print("RISULTATI PASM su ibm_fez")
print("="*60)
print(f"Counts shared:   {dict(sorted(cs.items()))}")
print(f"Counts separate: {dict(sorted(cp.items()))}")
print(f"\nMI_shared   = {mi_s:.6f} bits")
print(f"MI_separate = {mi_p:.6f} bits")
print(f"Differenza  = {mi_s - mi_p:.6f} bits")

if mi_s > mi_p + 0.005:
    print("\n>>> TESI SUPPORTATA: imprint condiviso produce correlazione residua")
elif mi_s < mi_p - 0.005:
    print("\n>>> TESI INVERSA: imprint separato produce piu' correlazione")
else:
    print("\n>>> TESI NON SUPPORTATA: nessuna differenza significativa")

import json
risultati = {
    "job_id": job.job_id(),
    "backend": backend.name,
    "MI_shared": mi_s,
    "MI_separate": mi_p,
    "diff": mi_s - mi_p,
    "counts_shared": {k: int(v) for k,v in cs.items()},
    "counts_separate": {k: int(v) for k,v in cp.items()}
}
with open("risultati_pasm.json", "w") as f:
    json.dump(risultati, f, indent=2)
print(f"\nRisultati salvati in risultati_pasm.json")
