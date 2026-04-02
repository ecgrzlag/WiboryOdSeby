from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
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
    
    # Strona instrumentu
    page.goto(f"https://stooq.pl/q/?s={ticker}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    
    # Symuluj ruch myszką
    page.mouse.move(500, 300)
    page.wait_for_timeout(300)
    
    # Kliknij "Dane historyczne"
    page.click('a:has-text("Dane historyczne")')
    page.wait_for_timeout(2000)
    
    # Symuluj scrollowanie
    page.mouse.wheel(0, 500)
    page.wait_for_timeout(500)
    page.mouse.wheel(0, 500)
    page.wait_for_timeout(500)
    
    # Znajdź link do pobrania
    download_link = page.locator('a:has-text("Pobierz dane")')
    if download_link.count() == 0:
        raise Exception("Nie znaleziono linku do pobrania")
    
    # Przewiń do linku i najedź myszką
    download_link.first.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    
    box = download_link.first.bounding_box()
    if box:
        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        page.wait_for_timeout(300)
    
    # Pobierz plik
    with page.expect_download(timeout=60000) as download_info:
        download_link.first.click()
    
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
                header = next(reader)  # Pomijamy nagłówek
                count = 0
                for row in reader:
                    if len(row) >= 5:
                        all_rows.append({
                            'Data': row[0],
                            'Otwarcie': row[1],
                            'Najwyższy': row[2],
                            'Najniższy': row[3],
                            'Zamknięcie': row[4],
                            'Ticker': name
                        })
                        count += 1
            print(f"  {name}: {count} wierszy")
    
    # Sortuj po dacie (malejąco) i tickerze
    all_rows.sort(key=lambda x: (x['Data'], x['Ticker']), reverse=True)
    
    # Zapisz do CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Otwarcie', 'Najwyższy', 'Najniższy', 'Zamknięcie', 'Ticker'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nŁącznie wierszy: {len(all_rows)}")

def main():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL"
        )
        
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Strona główna (ustaw sesję)
        print("Wchodzę na stronę główną Stooq...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.mouse.move(500, 300)
        page.wait_for_timeout(500)
        
        # Pobierz każdy ticker
        for ticker, name in TICKERS.items():
            try:
                download_single_ticker(page, ticker, name, download_dir)
            except Exception as e:
                print(f"  Błąd przy {ticker}: {e}")
        
        browser.close()
    
    # Połącz wszystkie pliki
    print("\nŁączę pliki CSV...")
    merge_csv_files(download_dir, "wibor_all.csv")
    
    # Zapisz timestamp
    with open("last_update.txt", "w") as f:
        warsaw_time = datetime.now(ZoneInfo("Europe/Warsaw"))
        f.write(warsaw_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    print("Zakończono!")

if __name__ == "__main__":
    main()
