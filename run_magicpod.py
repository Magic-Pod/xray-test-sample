import os
import re
import requests
import sys
import json
import inspect
import subprocess
import zipfile
import shutil

class MagicpodApiClientWrapper:
    def __init__(self, secret_api_token, org_name, project_name, cmd_path, tmp_dir):
        self._secret_api_token = secret_api_token
        self._org_name = org_name
        self._project_name = project_name
        self._cmd_path = cmd_path
        self._tmp_dir = tmp_dir

    def _run_command(self, command):
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Get the output as text mode
                check=True  # Raise an error is error code is not 0
            )
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return None, f"Error: error code {e.returncode} "
        except FileNotFoundError:
            return None, "Error: Command not found"

    def batch_run(self, setting_id):
        command = [
            self._cmd_path,
            "batch-run",
            "-t", self._secret_api_token,
            "-o", self._org_name,
            "-p", self._project_name,
            "-S", str(setting_id)
        ]
        stdout, stderr = self._run_command(command=command)
        print(command)
        print(stdout)
        print(stderr)
        return stdout

    def get_latest_batch_number(self):
        latest_number = 0
        url = f"https://magic-pod.com/api/v1.0/{self._org_name}/{self._project_name}/batch-runs/?count=1"
        headers = {
            "Authorization": f"Token {self._secret_api_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            latest_number = result['batch_runs'][0]['batch_run_number']
        return latest_number

    def get_batch_run(self, batch_run_number):
        url = f"https://magic-pod.com/api/v1.0/{self._org_name}/{self._project_name}/batch-run/{batch_run_number}"
        headers = {
            "Authorization": f"Token {self._secret_api_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result

def run_magicpod(output_filename, magicpod_api_client_path, temp_dir):
    if not temp_dir.endswith('/'):
        temp_dir += '/'
    MAGICPOD_API_TOKEN = os.environ.get("MAGICPOD_API_TOKEN")
    MAGICPOD_ORGANIZATION_NAME = os.environ.get("MAGICPOD_ORGANIZATION_NAME")
    MAGICPOD_PROJECT_NAME = os.environ.get("MAGICPOD_PROJECT_NAME")
    MAGICPOD_TEST_SETTING_ID = os.environ.get("MAGICPOD_TEST_SETTING_ID")
    client = MagicpodApiClientWrapper(secret_api_token=MAGICPOD_API_TOKEN, org_name=MAGICPOD_ORGANIZATION_NAME, project_name=MAGICPOD_PROJECT_NAME, cmd_path=magicpod_api_client_path, tmp_dir=temp_dir)
    # Run MagicPod tests
    client.batch_run(MAGICPOD_TEST_SETTING_ID)
    # Get test results
    latest_batch_number = client.get_latest_batch_number()
    test_results = client.get_batch_run(latest_batch_number)
    # Save test results in a file
    with open(output_filename, "w", encoding='utf-8') as file:
        file.write(json.dumps(test_results))

run_magicpod(output_filename='./magicpod_result',magicpod_api_client_path='./magicpod-api-client', temp_dir='./')