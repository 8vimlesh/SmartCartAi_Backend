from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

def check_active_alerts():
    print(f"\n[SCHEDULER] Waking up to check for price drops...")
    from services.database import alerts_col
    from services.scraper import scrape_all
    from services.database import save_price, check_alerts
    
    # Find all unique products that have at least one untriggered alert
    active_alerts = list(alerts_col.find({'triggered': False}))
    products_to_check = set([a['product_name'] for a in active_alerts])
    
    if not products_to_check:
        print("[SCHEDULER] No active untriggered alerts. Going back to sleep.\n")
        return
        
    print(f"[SCHEDULER] Actively checking {len(products_to_check)} tracked products...")
    
    for product in products_to_check:
        try:
            print(f"  -> Scraping live prices for '{product}'...")
            results = scrape_all(product)
            
            for r in results:
                if r.get('price'):
                    # Save the new price to DB
                    save_price(product, r['platform'], r['price'], r.get('rating'), r.get('url'))
                    # Check if this new price triggers any alerts (sends emails)
                    check_alerts(product, r['platform'], r['price'])
                    
            time.sleep(2) # be gentle with the API
        except Exception as e:
            print(f"[SCHEDULER ERROR] Failed to check product {product}: {str(e)}")
            
    print("[SCHEDULER] Check complete.\n")

def start_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    
    # Default to 60 minutes, allow override for testing (e.g. SCHEDULER_MINUTES=5)
    interval_minutes = int(os.getenv('SCHEDULER_MINUTES', 60))
    
    scheduler.add_job(check_active_alerts, 'interval', minutes=interval_minutes)
    scheduler.start()
    print(f"[SCHEDULER] Background price checker started (runs every {interval_minutes} minutes).")
