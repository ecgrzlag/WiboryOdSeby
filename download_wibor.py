from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
import os

TICKERS = {
    'plopln1m': 'WIBOR_1M',
    'plopln3m': 'WIBOR_3M',
    'plopln6m': 'WIBOR_6M',
    'ploplnon': 'WIBOR_ON',
    'plbplnon': 'WIBID_ON'
}

def download_single_ticker(page, ticker, name, download_dir):
    """Pobiera CSV dla jednego tickera"""
    print(f"Pobieram {name} ({ticker})...")
    
    page.goto(f"https://stooq.pl/q/d/?s={ticker}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    
    # Pobierz plik
    with page.expect_download(timeout=30000) as download_info:
        page.click('a:has-text("Pobierz dane")')
    
    download = download_info.value
    filepath = os.path.join(download_dir, f"{ticker}.csv")
    download.save_as(filepath)
    print(f"  Zapisano: {filepath}")
    return filepath

def merge_csv_files(download_dir, output_file):
    """Łączy wszystkie CSV w jeden plik z kolumną Ticker"""
    all_rows = []
    
    for ticker, name in TICKERS.items():
        filepath = os.path.join(download_dir, f"{ticker}.csv")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Pomiń nagłówek
                for row in reader:
                    if len(row) >= 5:
                        all_rows.append({
                            'Date': row[0],
                            'Open': row[1],
                            'High': row[2],
                            'Low': row[3],
                            'Close': row[4],
                            'Ticker': name
                        })
            print(f"  {name}: {sum(1 for r in all_rows if r['Ticker'] == name)} wierszy")
    
    all_rows.sort(key=lambda x: (x['Date'], x['Ticker']), reverse=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Open', 'High', 'Low', 'Close', 'Ticker'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nŁącznie wierszy: {len(all_rows)}")

def main():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL"
        )
        page = context.new_page()
        
        # Wejdź na stronę główną (ustaw cookies)
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        
        # Pobierz dane dla każdego tickera
        for ticker, name in TICKERS.items():
            try:
                download_single_ticker(page, ticker, name, download_dir)
            except Exception as e:
                print(f"  Błąd przy {ticker}: {e}")
        
        browser.close()
    
    merge_csv_files(download_dir, "wibor_all.csv")
    
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))

if __name__ == "__main__":
    main()
