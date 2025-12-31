import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_KV_NAMESPACE = os.environ.get("CF_KV_NAMESPACE")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

CF_KV_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_KV_NAMESPACE}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android)",
    "Referer": "https://vahanx.in/"
}

def kv_get(key):
    r = requests.get(
        f"{CF_KV_BASE}/values/{key}",
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"}
    )
    if r.status_code == 200:
        return r.json()
    return None

def kv_put(key, value):
    requests.put(
        f"{CF_KV_BASE}/values/{key}",
        headers={
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json"
        },
        data=json.dumps(value)
    )

def scrape_rc(rc):
    url = f"https://vahanx.in/rc-search/{rc}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    def get(label):
        s = soup.find("span", string=lambda x: x and label.lower() in x.lower())
        if s:
            p = s.find_next("p")
            return p.text.strip() if p else None
        return None

    return {
        "status": "success",
        "rc_number": rc,
        "owner": get("Owner Name"),
        "father": get("Father"),
        "model": get("Model"),
        "fuel": get("Fuel Type"),
        "rto": get("RTO")
    }

@app.route("/", methods=["GET"])
def api():
    rc = request.args.get("rc_number")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "unauthorized"}), 403

    if not rc:
        return jsonify({"error": "missing rc_number"}), 400

    rc = rc.upper()

    cached = kv_get(rc)
    if cached:
        cached["cached"] = True
        return jsonify(cached)

    data = scrape_rc(rc)
    kv_put(rc, data)
    data["cached"] = False
    return jsonify(data)
