from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
import os

def main():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # Użyj headed mode z xvfb (wirtualny display)
        browser = p.chromium.launch(
            headless=False,  # Ważne! Nie headless
            args=['--disable-blink-features=AutomationControlled']  # Ukryj webdriver
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL"
        )
        
        # Ukryj webdriver
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # KROK 1: Strona główna
        print("KROK 1: Strona główna...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Symuluj ruch myszką
        page.mouse.move(500, 300)
        page.wait_for_timeout(500)
        page.mouse.move(600, 400)
        
        # KROK 2: Strona PLOPLN1M
        print("KROK 2: Strona PLOPLN1M...")
        page.goto("https://stooq.pl/q/?s=plopln1m", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        
        # KROK 3: Kliknij "Dane historyczne"
        print("KROK 3: Dane historyczne...")
        page.click('a:has-text("Dane historyczne")')
        page.wait_for_timeout(3000)
        
        # Symuluj scrollowanie
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(1000)
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(1000)
        
        # KROK 4: Przewiń do linku i kliknij
        print("KROK 4: Szukam linku Pobierz dane...")
        download_link = page.locator('a:has-text("Pobierz dane")')
        
        if download_link.count() > 0:
            # Przewiń do linku
            download_link.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            
            # Symuluj najechanie myszką na link
            box = download_link.first.bounding_box()
            if box:
                page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(500)
            
            page.screenshot(path=os.path.join(download_dir, "01_przed_kliknieciem.png"))
            
            # KROK 5: Pobierz
            print("KROK 5: Klikam i pobieram...")
            try:
                with page.expect_download(timeout=60000) as download_info:
                    download_link.first.click()
                
                download = download_info.value
                filepath = os.path.join(download_dir, "plopln1m.csv")
                download.save_as(filepath)
                print(f"  SUKCES! Zapisano: {filepath}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    print("  Pierwsze linie:")
                    for line in lines:
                        print(f"    {line.strip()}")
                        
            except Exception as e:
                print(f"  Błąd: {e}")
                page.screenshot(path=os.path.join(download_dir, "02_blad.png"))
        
        browser.close()
    
    with open("last_update.txt", "w") as f:
        warsaw_time = datetime.now(ZoneInfo("Europe/Warsaw"))
        f.write(warsaw_time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
