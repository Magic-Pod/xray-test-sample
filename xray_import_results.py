import os
import json
import argparse
import requests
from datetime import datetime


class XrayResultImporter:
    """Authenticate and upload test results to Xray Cloud."""

    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.authenticate()

    def authenticate(self):
        url = f"{self.base_url}/api/v2/authenticate"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.text.strip('"')  # Xray returns raw string

    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def import_results(self, execution_payload):
        url = f"{self.base_url}/api/v2/import/execution"
        resp = requests.post(url, headers=self.headers(), json=execution_payload)
        if not resp.ok:
            print("❌ Failed to upload test results. Response:", resp.text)
            resp.raise_for_status()
        return resp.json()


def map_status(mp_status: str) -> str:
    """Map MagicPod statuses to Xray statuses."""
    mp_status = (mp_status or "").lower()
    if mp_status in ("succeeded"):
        return "PASSED"
    if mp_status in ("failed"):
        return "FAILED"
    if mp_status == "skipped":
        return "TODO"
    return "TODO"


def convert_magicpod_to_xray(mp_file: str, summary: str = None) -> dict:
    """Convert MagicPod result JSON into Xray execution JSON."""
    with open(mp_file, "r", encoding="utf-8") as f:
        mp = json.load(f)

    if not summary:
        summary = f"MagicPod Batch Run: {mp['url']}"
        description = f"Imported automatically from MagicPod. \n MagicPod URL: {mp['url']}"

    execution = {
        "info": {
            "summary": summary,
            "description": description
        },
        "tests": []
    }

    # Adjust this part depending on your MagicPod JSON structure
    details = mp.get("test_cases", {}).get("details", [])
    for detail in details:
        for result in detail.get("results", []):
            tc = result.get("test_case", {})
            test_name = tc.get("name", "Unnamed Test")
            status = map_status(result.get("status", ""))

            # Try to extract Xray testKey from test name, e.g. "Login [PROJ-12]"
            test_key = None
            if "[" in test_name and "]" in test_name:
                candidate = test_name.split("[")[-1].strip("]")
                if "-" in candidate:        # rudimentary check for JIRA key pattern
                    test_key = candidate

            test_entry = {
                "status": status,
                "comment": f"Imported from MagicPod. Original test: {test_name}"
            }

            if test_key:
                test_entry["testKey"] = test_key
            else:
                test_entry["testInfo"] = {
                    "summary": test_name,
                    "type": "Manual"  # or "Automated" if desired
                }

            execution["tests"].append(test_entry)

    return execution


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import MagicPod test results into Xray")
    parser.add_argument("--base-url",
                        default=os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app"),
                        help="Xray base URL")
    parser.add_argument("--client-id",
                        default=os.getenv("XRAY_ID"),
                        help="Xray client ID")
    parser.add_argument("--client-secret",
                        default=os.getenv("XRAY_SECRET"),
                        help="Xray client secret")
    parser.add_argument("--magicpod-json",
                        default="magicpod_result",
                        help="Path to MagicPod result JSON file")
    parser.add_argument("--summary",
                        help="Summary for the Test Execution in Xray")

    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        parser.error("Missing Xray credentials (client_id / client_secret)")

    importer = XrayResultImporter(args.base_url, args.client_id, args.client_secret)
    payload = convert_magicpod_to_xray(args.magicpod_json, args.summary)

    print("➡️ Payload being sent to Xray:")
    print(json.dumps(payload, indent=2))

    response = importer.import_results(payload)
    print("✅ Upload successful. Xray response:")
    print(json.dumps(response, indent=2))
    if not args.client_id or not args.client_secret:
        parser.error("Missing Xray credentials (client_id / client_secret)")


