"""Award providers, one module per loyalty program. Register a new one by adding its module name here."""
import importlib

MODULES = ["delta", "alaska", "jetblue", "southwest", "frontier", "qantas", "velocity", "sas", "smiles", "ceair", "ethiopian", "etihad", "ana"]

# Programs that were investigated and cannot be searched signed-out from headless Chrome. The CLI names
# the reason instead of saying "unknown program". Evidence and next steps: reference/<name>.md, or
# reference/coverage.md for the programs that only got a survey visit.
LOGIN = "the airline shows award space only to signed-in members, and no account is configured"
UNAVAILABLE = {
    "united": LOGIN,
    "flyingblue": LOGIN,
    "virgin": LOGIN,
    "emirates": LOGIN,
    "korean": LOGIN,
    "ba": LOGIN,
    "iberia": LOGIN,
    "finnair": LOGIN,
    "cathay": LOGIN,
    "jal": LOGIN,
    "qatar": LOGIN,
    "singapore": LOGIN,
    "lufthansa": LOGIN,
    "eva": LOGIN,
    "lifemiles": LOGIN,
    "latam": LOGIN,
    "tap": LOGIN,
    "westjet": LOGIN,
    "aerlingus": LOGIN,
    "aireuropa": LOGIN,
    "saudia": LOGIN,
    "gulfair": LOGIN,
    "royalairmaroc": LOGIN,
    "omanair": LOGIN,
    "chinasouthern": LOGIN,
    "hainan": LOGIN,
    "thai": LOGIN,
    "malaysia": LOGIN,
    "vietnam": LOGIN,
    "garuda": LOGIN,
    "airindia": LOGIN,
    "asiana": LOGIN + " (a signed-out seat-availability calendar exists, without miles prices)",
    "ita": "ita-airways.com answers headless Chrome with a Cloudflare security check",
    "turkish": "turkishairlines.com answers headless Chrome with a press-and-hold human check",
    "aeroplan": LOGIN + "; the results page also answers headless Chrome with 403",
    "aeromexico": "aeromexico.com answers the points search with an Akamai challenge (HTTP 429)",
    "copa": "copaair.com answers headless Chrome with a slider CAPTCHA (providers/copa.py exists but never ran live)",
    "american": "aa.com answers headless Chrome with a CAPTCHA before any search",
}


def load(name):
    return importlib.import_module(f"{__name__}.{name}").PROVIDER


def available():
    return {m: load(m) for m in MODULES}
