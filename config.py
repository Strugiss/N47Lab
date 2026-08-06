"""
Config N47Lab — carica credenziali da .env
"""
import os, pathlib

def _load_dotenv(path=None):
    if path is None:
        path = pathlib.Path(__file__).parent / ".env"
    if not path.exists():
        return {}
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

_env = _load_dotenv()

API_TOKEN = _env.get("IBM_API_TOKEN") or os.environ.get("IBM_API_TOKEN") or ""
CRN = _env.get("IBM_CRN") or os.environ.get("IBM_CRN") or ""

if not API_TOKEN:
    print("ATTENZIONE: IBM_API_TOKEN non trovato in .env o variabili ambiente")
if not CRN:
    print("ATTENZIONE: IBM_CRN non trovato in .env o variabili ambiente")
