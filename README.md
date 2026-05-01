# 🏦 Horatio Invest – Porteføljerapport

Automatisk daglig rapport over Horatio Invest-gruppens portefølje.

## Hvad det gør
- Henter aktuelle kurser på alle aktier via Yahoo Finance
- Henter valutakurser (NOK, USD, EUR → DKK)
- Gemmer historik i `data/history.json`
- Genererer HTML-rapport i `docs/index.html`
- Kører automatisk hverdage kl. 17:30 dansk tid

## Opsætning (én gang)

### 1. Opret GitHub repository
1. Gå til [github.com](https://github.com) → **New repository**
2. Navn: `horatio-invest` (eller hvad du vil)
3. Sæt til **Public** (kræves til gratis GitHub Pages)
4. Klik **Create repository**

### 2. Upload filerne
Upload alle filer fra dette projekt til dit nye repo.

### 3. Aktiver GitHub Pages
1. Gå til dit repo → **Settings** → **Pages**
2. Under *Source*: vælg **Deploy from a branch**
3. Branch: `main`, Folder: `/docs`
4. Klik **Save**

Din rapport er nu tilgængelig på:
`https://DIT-BRUGERNAVN.github.io/horatio-invest/`

### 4. Kør manuelt første gang
1. Gå til **Actions** i dit repo
2. Klik på "Opdater Horatio Invest rapport"
3. Klik **Run workflow**

## Opdater porteføljen
Rediger `fetch_prices.py` – find `PORTFOLIO`-listen øverst og tilføj/fjern aktier.

## Tilføj ny aktie
```python
{"name": "Aktienavn", "ticker": "TICKER.BØRS", "shares": ANTAL, "gak": KURS, "currency": "DKK"},
```

**Ticker-format eksempler:**
- Dansk børs (Nasdaq Copenhagen): `CARL-B.CO`
- Norsk børs (Oslo): `KOG.OL`
- Tysk børs (Xetra): `RHM.DE`
- Amerikansk (NYSE/Nasdaq): `NVDA`

Find tickers på [finance.yahoo.com](https://finance.yahoo.com)

## Filer
```
horatio-invest/
├── fetch_prices.py          # Hoved-script
├── .github/workflows/
│   └── update.yml           # Automatisk kørsel
├── data/
│   └── history.json         # Historiske kurser (auto-genereret)
└── docs/
    └── index.html           # HTML-rapport (auto-genereret)
```
