import yfinance as yf
import json
import os
from datetime import datetime, date

# ── Portefølje ────────────────────────────────────────────────────────────────
PORTFOLIO = [
    {"name": "Carlsberg B",                          "ticker": "CARL-B.CO", "shares": 7,  "gak": 846.29,  "currency": "DKK"},
    {"name": "Kongsberg Gruppen",                    "ticker": "KOG.OL",    "shares": 25, "gak": 175.38,  "currency": "NOK"},
    {"name": "Kongsberg Maritime ASA",               "ticker": "KM.OL",     "shares": 25, "gak": 55.38,   "currency": "NOK"},
    {"name": "Microsoft",                            "ticker": "MSFT",      "shares": 1,  "gak": 418.30,  "currency": "USD"},
    {"name": "NKT",                                  "ticker": "NKT.CO",    "shares": 12, "gak": 528.83,  "currency": "DKK"},
    {"name": "Novo Nordisk B",                       "ticker": "NOVO-B.CO", "shares": 17, "gak": 457.77,  "currency": "DKK"},
    {"name": "NVIDIA",                               "ticker": "NVDA",      "shares": 9,  "gak": 87.96,   "currency": "USD"},
    {"name": "Rheinmetall",                          "ticker": "RHM.DE",    "shares": 1,  "gak": 508.00,  "currency": "EUR"},
    {"name": "Taiwan Semiconductor (TSMC ADR)",      "ticker": "TSM",       "shares": 6,  "gak": 130.46,  "currency": "USD"},
    {"name": "Vestas Wind Systems",                  "ticker": "VWS.CO",    "shares": 70, "gak": 105.52,  "currency": "DKK"},
]

FX_TICKERS = {
    "NOK": "NOKDKK=X",
    "USD": "USDDKK=X",
    "EUR": "EURDKK=X",
    "DKK": None,
}

DATA_FILE = "data/history.json"

# ── Hent valutakurser ─────────────────────────────────────────────────────────
def fetch_fx():
    fx = {"DKK": 1.0}
    for currency, ticker in FX_TICKERS.items():
        if ticker:
            try:
                t = yf.Ticker(ticker)
                price = t.fast_info["last_price"]
                fx[currency] = round(price, 4)
            except Exception as e:
                print(f"FX fejl {currency}: {e}")
                fx[currency] = None
    return fx

# ── Hent aktiekurser ──────────────────────────────────────────────────────────
def fetch_prices(fx):
    today = date.today().isoformat()
    results = []
    for stock in PORTFOLIO:
        try:
            t = yf.Ticker(stock["ticker"])
            price = t.fast_info["last_price"]
            rate = fx.get(stock["currency"], 1.0)
            price_dkk = round(price * rate, 2) if rate else None
            gak_dkk = round(stock["gak"] * rate, 2) if rate else None
            value_dkk = round(price_dkk * stock["shares"], 2) if price_dkk else None
            cost_dkk = round(gak_dkk * stock["shares"], 2) if gak_dkk else None
            gain_dkk = round(value_dkk - cost_dkk, 2) if (value_dkk and cost_dkk) else None
            gain_pct = round((price_dkk - gak_dkk) / gak_dkk * 100, 2) if (price_dkk and gak_dkk) else None
            results.append({
                "name": stock["name"],
                "ticker": stock["ticker"],
                "shares": stock["shares"],
                "gak": stock["gak"],
                "gak_dkk": gak_dkk,
                "currency": stock["currency"],
                "price": round(price, 2),
                "price_dkk": price_dkk,
                "value_dkk": value_dkk,
                "gain_dkk": gain_dkk,
                "gain_pct": gain_pct,
                "date": today,
            })
            print(f"✓ {stock['name']}: {price} {stock['currency']} = {price_dkk} DKK")
        except Exception as e:
            print(f"✗ {stock['name']} ({stock['ticker']}): {e}")
    return results

# ── Opdater historik ──────────────────────────────────────────────────────────
def update_history(new_data):
    history = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            history = json.load(f)

    today = date.today().isoformat()
    # Fjern evt. eksisterende entry for i dag (re-run)
    history = [h for h in history if h["date"] != today]
    history.append({"date": today, "stocks": new_data})

    # Behold max 365 dage
    history = sorted(history, key=lambda x: x["date"])[-365:]

    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"Historik gemt: {len(history)} dage")
    return history

# ── Generer HTML-rapport ──────────────────────────────────────────────────────
def generate_html(history, fx):
    today_data = history[-1]["stocks"] if history else []
    today_str = history[-1]["date"] if history else "–"

    total_value = sum(s["value_dkk"] for s in today_data if s["value_dkk"])
    total_cost  = sum(s["gak_dkk"] * s["shares"] for s in today_data if s["gak_dkk"])
    total_gain  = total_value - total_cost
    total_pct   = (total_gain / total_cost * 100) if total_cost else 0

    # Historiske porteføljeværdier til graf
    chart_labels = [h["date"] for h in history]
    chart_values = [
        round(sum(s["value_dkk"] for s in h["stocks"] if s["value_dkk"]), 2)
        for h in history
    ]

    # Enkeltaktie historik til sparklines
    all_names = [s["name"] for s in today_data]
    sparklines = {}
    for name in all_names:
        sparklines[name] = [
            next((s["price_dkk"] for s in h["stocks"] if s["name"] == name), None)
            for h in history
        ]

    fx_str = " &nbsp;|&nbsp; ".join(
        f"{k}/DKK: <strong>{v}</strong>"
        for k, v in fx.items() if k != "DKK" and v
    )

    rows = ""
    for s in sorted(today_data, key=lambda x: -(x["value_dkk"] or 0)):
        color = "#16a34a" if (s["gain_pct"] or 0) >= 0 else "#dc2626"
        sign  = "+" if (s["gain_pct"] or 0) >= 0 else ""
        spark_data = json.dumps([v for v in sparklines.get(s["name"], []) if v is not None])
        rows += f"""
        <tr>
          <td>{s['name']}</td>
          <td class="num">{s['shares']}</td>
          <td class="num">{s['price']} {s['currency']}</td>
          <td class="num">{s['price_dkk']:,.2f}</td>
          <td class="num">{s['gak_dkk']:,.2f}</td>
          <td class="num"><strong>{s['value_dkk']:,.0f}</strong></td>
          <td class="num" style="color:{color}">{sign}{s['gain_pct']:.2f}%</td>
          <td class="num" style="color:{color}">{sign}{s['gain_dkk']:,.0f}</td>
          <td><canvas class="spark" data-values='{spark_data}'></canvas></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Horatio Invest – Porteføljerapport</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #1e293b; }}
  header {{ background: #1e3a5f; color: white; padding: 24px 32px; }}
  header h1 {{ font-size: 1.6rem; font-weight: 700; }}
  header p {{ font-size: 0.9rem; opacity: 0.75; margin-top: 4px; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .kpi {{ background: white; border-radius: 10px; padding: 18px 22px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .kpi .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }}
  .kpi .value {{ font-size: 1.6rem; font-weight: 700; margin-top: 4px; }}
  .kpi .value.pos {{ color: #16a34a; }}
  .kpi .value.neg {{ color: #dc2626; }}
  .card {{ background: white; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 24px; margin-bottom: 24px; }}
  .card h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: #334155; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ text-align: left; padding: 8px 10px; border-bottom: 2px solid #e2e8f0; color: #64748b; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
  td {{ padding: 10px 10px; border-bottom: 1px solid #f1f5f9; }}
  tr:hover td {{ background: #f8fafc; }}
  .num {{ text-align: right; }}
  .spark {{ width: 80px; height: 30px; }}
  .fx {{ font-size: 0.8rem; color: #64748b; margin-bottom: 20px; }}
  .chart-wrap {{ height: 260px; position: relative; }}
</style>
</head>
<body>
<header>
  <h1>🏦 Horatio Invest</h1>
  <p>Porteføljerapport · Opdateret {today_str}</p>
</header>
<div class="container">
  <div class="kpi-grid">
    <div class="kpi">
      <div class="label">Samlet værdi</div>
      <div class="value">{total_value:,.0f} kr</div>
    </div>
    <div class="kpi">
      <div class="label">Samlet kostpris</div>
      <div class="value">{total_cost:,.0f} kr</div>
    </div>
    <div class="kpi">
      <div class="label">Gevinst/Tab</div>
      <div class="value {'pos' if total_gain >= 0 else 'neg'}">{'+' if total_gain >= 0 else ''}{total_gain:,.0f} kr</div>
    </div>
    <div class="kpi">
      <div class="label">Afkast</div>
      <div class="value {'pos' if total_pct >= 0 else 'neg'}">{'+' if total_pct >= 0 else ''}{total_pct:.2f}%</div>
    </div>
  </div>

  <div class="fx">Valutakurser: {fx_str}</div>

  <div class="card">
    <h2>Porteføljeudvikling (DKK)</h2>
    <div class="chart-wrap">
      <canvas id="portfolioChart"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>Beholdning</h2>
    <table>
      <thead>
        <tr>
          <th>Aktie</th><th class="num">Stk.</th><th class="num">Kurs</th>
          <th class="num">Kurs DKK</th><th class="num">GAK DKK</th>
          <th class="num">Værdi DKK</th><th class="num">Afkast %</th>
          <th class="num">Gevinst DKK</th><th>Trend</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>

<script>
// Porteføljegraf
const ctx = document.getElementById('portfolioChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {json.dumps(chart_labels)},
    datasets: [{{
      label: 'Porteføljeværdi (DKK)',
      data: {json.dumps(chart_values)},
      borderColor: '#1e3a5f',
      backgroundColor: 'rgba(30,58,95,0.08)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      y: {{ ticks: {{ callback: v => v.toLocaleString('da-DK') + ' kr' }} }},
      x: {{ ticks: {{ maxTicksLimit: 12 }} }}
    }}
  }}
}});

// Sparklines
document.querySelectorAll('.spark').forEach(canvas => {{
  const values = JSON.parse(canvas.dataset.values || '[]');
  if (values.length < 2) return;
  const first = values[0], last = values[values.length - 1];
  new Chart(canvas, {{
    type: 'line',
    data: {{
      labels: values.map((_, i) => i),
      datasets: [{{ data: values, borderColor: last >= first ? '#16a34a' : '#dc2626',
        borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.3 }}]
    }},
    options: {{
      responsive: false, animation: false,
      plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
      scales: {{ x: {{ display: false }}, y: {{ display: false }} }}
    }}
  }});
}});
</script>
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML rapport gemt: docs/index.html")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"=== Horatio Invest – {date.today()} ===")
    fx = fetch_fx()
    print(f"Valuta: {fx}")
    prices = fetch_prices(fx)
    history = update_history(prices)
    generate_html(history, fx)
    print("Færdig ✓")
