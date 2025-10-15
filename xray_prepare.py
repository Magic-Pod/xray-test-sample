import os
import argparse
import json
import requests
from datetime import datetime
import base64

class JiraAPIWrapper:
    """
    Handles creating Test Plan issues in Jira (Xray is installed on Jira).
    """

    def __init__(self, jira_url, jira_user, jira_token):
        self.jira_url = jira_url.rstrip("/")
        self.jira_user = jira_user
        self.jira_token = jira_token
        self.headers = {
            "Authorization": self._basic_auth(),
            "Content-Type": "application/json"
        }

    def _basic_auth(self):
        # Encode Jira email + API token for Basic Auth
        token_bytes = f"{self.jira_user}:{self.jira_token}".encode("utf-8")
        return f"Basic {base64.b64encode(token_bytes).decode('utf-8')}"

    def create_test_plan(self, project_key, summary=None, description=None):
        if not summary:
            summary = datetime.now().strftime("%Y-%m-%d-%H-%M") + " MagicPod Test Plan"
        if not description:
            description = "Created automatically by script"

        url = f"{self.jira_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Test Plan"}
            }
        }

        resp = requests.post(url, headers=self.headers, json=payload)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("❌ Failed to create Test Plan.")
            print("Response:", resp.text)
            raise e
        return resp.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Test Plan in Jira/Xray")

    # Jira credentials
    parser.add_argument(
        "--jira-url",
        default=os.getenv("JIRA_URL"),
        help="Your Jira Cloud base URL (e.g., https://yourcompany.atlassian.net)"
    )
    parser.add_argument(
        "--jira-user",
        default=os.getenv("JIRA_USER"),
        help="Jira user email (or set JIRA_USER env var)"
    )
    parser.add_argument(
        "--jira-token",
        default=os.getenv("JIRA_API_TOKEN"),
        help="Jira API token (or set JIRA_API_TOKEN env var)"
    )

    # Test Plan details
    parser.add_argument("--project", required=True, help="Project key in Jira/Xray (e.g., XSP)")
    parser.add_argument("--summary", help="Summary for the Test Plan")
    parser.add_argument("--description", help="Description for the Test Plan")

    args = parser.parse_args()

    if not args.jira_url or not args.jira_user or not args.jira_token:
        parser.error("Missing Jira credentials: provide --jira-url, --jira-user, --jira-token or set env vars JIRA_URL/JIRA_USER/JIRA_API_TOKEN")

    api = JiraAPIWrapper(args.jira_url, args.jira_user, args.jira_token)
    result = api.create_test_plan(args.project, args.summary, args.description)

    print("✅ Test Plan created successfully:")
    print(json.dumps(result, indent=2))
