import requests
import sys
from concurrent.futures import ThreadPoolExecutor

# Better list of fallback gateways in case GitHub fails
FALLBACK_NODES = [
    "https://cloudflare-ipfs.com/ipfs/", "https://ipfs.io/ipfs/", "https://dweb.link/ipfs/",
    "https://gateway.pinata.cloud/ipfs/", "https://4everland.io/ipfs/", "https://cf-ipfs.com/ipfs/",
    "https://storry.tv/ipfs/", "https://ipfs.eth.aragon.network/ipfs/", "https://nftstorage.link/ipfs/"
]

def get_dynamic_gateways():
    url = "https://raw.githubusercontent.com/ipfs/public-gateway-list/master/gateways.json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        print("[*] Fetching global gateway list (Masked as Browser)...")
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Clean templates like https://{gatewayURL}/ipfs/{contentPath}
            gateways = []
            for g in data:
                clean = g.replace(":hash", "").replace("{contentPath}", "").replace("{gatewayURL}", "")
                if not clean.startswith("http"): clean = "https://" + clean
                gateways.append(clean)
            return gateways
    except Exception as e:
        print(f"[!] GitHub Blocked us. Using Hardcoded Elite Fallback...")
    return FALLBACK_NODES

def blast_gateway(gw, cid):
    base_url = gw if gw.endswith("/") else gw + "/"
    target = f"{base_url}{cid}"
    try:
        r = requests.head(target, timeout=5, headers={'User-Agent': 'CIPFSUF-Bot/1.0'})
        if r.status_code in [200, 201, 403, 405]: # 405 is Method Not Allowed but means it hit the node
            print(f"[+] PROPAGATED: {gw}")
            return True
    except:
        pass
    return False

def force_propagation(cid):
    all_gateways = get_dynamic_gateways()
    print(f"[*] LAUNCHING GLOBAL BLAST on {len(all_gateways)} nodes for CID: {cid}")
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(lambda gw: blast_gateway(gw, cid), all_gateways)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        force_propagation(sys.argv[1])
