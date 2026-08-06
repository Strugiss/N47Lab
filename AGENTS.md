# AGENTS.md — MatterMemory (N47Lab)

## Cos'è
Progetto di ricerca su imprint di fase sub-Planckiano come candidato materia oscura, verificato tramite PASM (Phase-Anchored State Multiplexing) su IBM Quantum.

## Architecture
- `mattermemorys.html` — report interattivo principale (v2.7, apri via localhost:8000)
- `n47lab_paper.tex` — paper LaTeX per arXiv
- `Immagini/` — 47 figure PNG/SVG
- Script `.py` in `C:\Users\Utente\AppData\Local\Temp\opencode\` (non nel workspace)
- `backup_v*.html` — backup del report HTML

## Comandi essenziali
| Azione | Comando (da MattterMemory/) |
|--------|-----------------------------|
| HTML preview | `http://localhost:8000/mattermemorys.html` |
| Esegui script | `python <script>.py` nel temp opencode |
| Submit QPU | `SamplerV2(mode=backend)` — **NO** Session/Batch su open plan |
| Export .env | API1=IBM_CRN, API2=IBM_OPEN |

## Backends IBM disponibili (API2, open plan)
- `ibm_kingston` — ~15 job coda (preferito)
- `ibm_marrakesh` — ~500 job
- `ibm_fez` — ~2000 job (congestionato)

## Template submit QPU
```python
S = QiskitRuntimeService(channel='ibm_cloud', token=API2)
backend = S.backend('ibm_kingston')
pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
qc_t = pm.run(qc)
sampler = SamplerV2(mode=backend)
job = sampler.run(qc_t, shots=8192)
```

## Risultati chiave (verificati)
- 13 esperimenti QPU completati, Z combinato > 50σ
- PASM: MI condivisa 0.063 ± 0.005 (marrakesh) / 0.047 ± 0.004 (kingston)
- Replica 10×: Z = 39.6σ
- φ-scan: MI modulata da φ, picco a π
- PASM Distanza: Z = 34σ, MI indipendente da distanza
- WITNESS controllo: MI = 0.00013 (zero)
- QST/DISCORD: MI=0.728, classico (<0.01)
- Scaling: MI picco a 3q = 0.159

## Credenziali
- `.env` in C:\Users\Utente\AppData\Local\Temp\opencode\
- API1: IBM Cloud (con CRN), API2: IBM Open (no CRN)
- `config.py`: `load_dotenv()` + variabili d'ambiente

## Vincoli tecnici (non cambiare)
- `optimization_level=1` sempre (preserva barriere/delay)
- **Niente** Session/Batch — solo `SamplerV2(mode=backend)` diretto
- AerSimulator GPU **non disponibile** su Windows (solo CPU 24 thread)
- Tutto l'output visibile in **italiano**

## File di configurazione opencode
- `.opencode/REGOLE.md` + `REGOLE_VINCOLANTI.md` + `PERSONALITA.md`
- `opencode.json` → `"instructions": [".opencode/REGOLE.md"]`

## Bug legacy noti (non fixare senza richiesta)
1. `chsh_bell_memory.py`: `channel='ibm_quantum'` → deve essere `ibm_cloud`
2. `entanglement_witness_pasm.py`: autenticazione usa channel sbagliato
3. `watch_pasm.py`: errore di indentazione
4. `n47lab_subplanckian_theory.py`: codice sperimentale (bug in fase di sviluppo)

## Workflow tipico
1. Leggi stato file su disco (non fidarti della memoria)
2. Verifica PHP server su localhost:8000 (non avviare senza chiedere)
3. Controlla backends disponibili e code
4. Sviluppa script in temp opencode
5. Per modifiche a `mattermemorys.html`: segui REGOLA 5 (AMBIENTE CHIUSO)
6. Dopo modifica incisiva: link ispezione → attesa approvazione → backup
