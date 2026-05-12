import requests
import concurrent.futures
import time

# Assuming your local server is running on port 5011
BASE_URL = "https://api.gms-admin.net/api/v1"

def fetch_url(endpoint):
    """Make a GET request to the given endpoint and return the status code."""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=2)
        print(f"Status: {response.status_code} | Endpoint: {endpoint}")
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {endpoint}: {e}")
        return None

def test_rate_limiting():
    # Create a list of 20 requests: 10 for '/online' and 10 for '/search'
    endpoints_to_hit = ["/online"] * 10 + ["/search?callsign=RAVEN-1"] * 10
    
    print(f"Firing {len(endpoints_to_hit)} requests simultaneously...")
    print("-" * 40)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to fire all requests concurrently within the same second
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_url, endpoints_to_hit))
        
    end_time = time.time()
    
    # Analyze the results
    rate_limited_count = results.count(429)
    success_count = len([r for r in results if r is not None and r != 429])
    
    print("-" * 40)
    print("--- TEST RESULTS ---")
    print(f"Completed in: {end_time - start_time:.2f} seconds")
    print(f"Total Requests Fired: {len(endpoints_to_hit)}")
    print(f"Requests that bypassed limits (Not 429): {success_count}")
    print(f"Requests blocked (429 Rate Limited): {rate_limited_count}")
    
    print("\n--- CONCLUSION ---")
    if rate_limited_count == 0:
        print("🔴 BUG REPRODUCED: All 20 requests succeeded in under a second!")
        print("   The rate limit is acting 'per-route' (10 on /online AND 10 on /search).")
    else:
        print("🟢 BUG FIXED: Global rate limit enforced. Some requests were blocked.")

if __name__ == "__main__":
    test_rate_limiting()