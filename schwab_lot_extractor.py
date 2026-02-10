import asyncio
import csv
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(f"schwab-annualized-{datetime.today().date()}.csv")


def parse_option(symbol: str):
    if " " not in symbol:
        return "", ""
    try:
        opt = symbol.strip().split(" ")[-1]
        expiry = f"{opt[2:4]}-{opt[4:6]}-{opt[0:2]} {opt[6]}"
        strike = float(opt[7:]) / 1000
        return expiry, strike
    except Exception:
        return "", ""


def annualized_return(cost_basis, market_value, days_held):
    if days_held <= 0 or cost_basis <= 0:
        return 0
    mult = market_value / cost_basis
    if mult <= 0:
        return 0
    return round((mult ** (365.25 / days_held) - 1) * 100, 2)


async def extract_lots(page):
    rows = await page.query_selector_all("tbody tr.data-row")
    lots = []

    for r in rows:
        def txt(sel):
            el = r.query_selector(sel)
            return el.text_content().strip() if el else ""

        def num(sel):
            t = txt(sel)
            return float(t.replace("$", "").replace(",", "").replace("%", "") or 0)

        lots.append({
            "open_date": txt("th span"),
            "quantity": num('td[name="Qty"]'),
            "price": num('td[name="Price"]'),
            "market_value": num('td[name="MktVal"] span'),
            "cost_basis": num('td[name="CostBasis"] span'),
            "gain_or_loss": num('td[name="GainLoss"] span'),
            "holding_period": txt('td[name="HoldPeriod"] span'),
        })

    return lots


async def main():
    data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://client.schwab.com/app/accounts/positions", timeout=0)
        print("Log in to Schwab, then press ENTER here.")
        input()

        buttons = await page.query_selector_all('sdps-button[sdps-name="Next Steps"]')

        for idx, btn in enumerate(buttons, start=1):
            row = await btn.evaluate_handle("el => el.closest('tr[data-symbol]')")
            symbol = await row.get_attribute("data-symbol")

            print(f"[{idx}/{len(buttons)}] Processing {symbol}")
            await btn.click()
            await page.wait_for_selector("#nextStepsList.show", timeout=5000)

            await page.click("text=Lot Details")
            await page.wait_for_selector("#open-lot-overlay.sdps-modal--open", timeout=5000)

            lots = await extract_lots(page)
            today = datetime.today()

            for lot in lots:
                open_dt = datetime.strptime(lot["open_date"], "%m/%d/%Y")
                days_held = (today - open_dt).days

                expiry, strike = parse_option(symbol)
                ann_ret = annualized_return(
                    lot["cost_basis"], lot["market_value"], days_held
                )

                lt_date = open_dt + timedelta(days=365)
                days_to_lt = max(0, (lt_date - today).days) if lot["holding_period"] == "Short Term" else 0

                data.append([
                    symbol,
                    symbol.split(" ")[0],
                    " " in symbol,
                    expiry,
                    strike,
                    lot["open_date"],
                    days_held,
                    ann_ret,
                    lot["quantity"],
                    lot["price"],
                    lot["market_value"],
                    lot["gain_or_loss"],
                    lot["holding_period"],
                    days_to_lt
                ])

            await page.click(".sdps-modal__close")
            await page.wait_for_timeout(800)

        await browser.close()

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "raw_symbol", "ticker", "is_option", "expiry", "strike",
            "open_date", "days_held", "annualized_return_pct",
            "quantity", "price", "market_value",
            "gain_or_loss", "holding_period", "days_until_long_term"
        ])
        writer.writerows(data)

    print(f"✓ Complete — CSV written to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
