import os
import requests
import json
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

# Set Color Scheme
green = "\033[92m"
reset_color = "\033[0m"
bold = "\033[1m"
underline = "\033[4m"

# Load environment variables from the project-level .env file
print(f"{green}{bold}Loading environment variables...{reset_color}")
load_dotenv()

# Load global environment variables using the path set in the project .env file
global_env_path = os.getenv('GLOBAL_ENV_PATH')
if global_env_path and os.path.exists(global_env_path):
    load_dotenv(global_env_path)
else:
    print(f"Error: You need to set a global path in your project-level .env.")
    raise ValueError("Global .env file loading failed.")

# Get GitHub token from the loaded environment variables
TOKEN = os.getenv('GITHUB_TOKEN')
if not TOKEN:
    raise ValueError(f"{green}Error: GITHUB_TOKEN environment variable is missing.{reset_color}")

# Load repository owner and list from YAML file
print(f"{green}{bold}Loading repository list from YAML...{reset_color}")
with open('Repo_List.yml', 'r') as file:
    config = yaml.safe_load(file)

# Extract owner and repository list from the loaded YAML file
OWNER = config['owner']
REPOS = config['repositories']

# Start fetching Dependabot alerts for each repository
print(f"{green}{bold}Starting to fetch Dependabot alerts for {len(REPOS)} repositories...{reset_color}")

# Initialize counters and lists to track success and failure
success_count = 0
failure_count = 0
results = []

# Initialize a dictionary to store the summary of alerts by severity
summary = {}

# Iterate over repositories and fetch Dependabot alerts with a status bar
for repo in tqdm(REPOS, bar_format="{l_bar}%s{bar}%s{r_bar}" % (green, reset_color)):
    REPO = repo

    # Construct the API URL dynamically for each repository
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/dependabot/alerts'
    print(f"{green}{bold}Fetching alerts from {url}...{reset_color}")

    # Set up headers for the API request including authorization
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Make the API request to fetch alerts
    response = requests.get(url, headers=headers)

    # Handle API response based on status code
    if response.status_code == 200:
        alerts = response.json()
        results.append({
            "repository": REPO,
            "status": "success",
            "alerts": alerts
        })
        success_count += 1
        print(f"{green}Success fetching alerts for {OWNER}/{REPO}.{reset_color}")
        
        # Initialize severity counters for this repo
        critical = 0
        high = 0
        medium = 0
        low = 0

        # Count the number of open alerts by severity
        for alert in alerts:
            if alert.get('state') == 'open':
                severity = alert.get('security_advisory', {}).get('severity')
                if severity == 'critical':
                    critical += 1
                elif severity == 'high':
                    high += 1
                elif severity == 'medium':
                    medium += 1
                elif severity == 'low':
                    low += 1

        # Store the summary for this repository
        summary[REPO] = {
            "Critical": critical,
            "High": high,
            "Medium": medium,
            "Low": low,
            "Total Vulnerabilities": critical + high + medium + low
        }
        
    elif response.status_code == 403:
        results.append({
            "repository": REPO,
            "status": "failure",
            "error_code": response.status_code,
            "error_message": "Insufficient permissions. Check the scope of your GITHUB_TOKEN."
        })
        failure_count += 1
        print(f'{green}{bold}Failed to fetch alerts for {OWNER}/{REPO} - Insufficient permissions (403).{reset_color}')
    elif response.status_code == 401:
        results.append({
            "repository": REPO,
            "status": "failure",
            "error_code": response.status_code,
            "error_message": "Unauthorized access. Invalid GITHUB_TOKEN."
        })
        failure_count += 1
        print(f'{green}{bold}Failed to fetch alerts for {OWNER}/{REPO} - Unauthorized (401).{reset_color}')
    else:
        results.append({
            "repository": REPO,
            "status": "failure",
            "error_code": response.status_code,
            "error_message": f"Failed with status code {response.status_code}."
        })
        failure_count += 1
        print(f'{green}{bold}Failed to fetch alerts for {OWNER}/{REPO} - Status code: {response.status_code}.{reset_color}')

    print(f"{green}Completed fetching for {OWNER}/{REPO}.{reset_color}")

# Print summary of the fetch operation
total_repos = len(REPOS)
print(f"\n{green}{bold}Summary:{reset_color}")
print(f"{green}{bold}Total repositories: {total_repos}{reset_color}")
print(f"{green}Successful fetches: {success_count}{reset_color}")
print(f"{green}Failed fetches: {failure_count}{reset_color}")

# Print the summary of alerts by severity for each repository
print(f"\n{green}{bold}Alerts by Severity:{reset_color}")
for repo, stats in summary.items():
    print(f"{green}{underline}Repository: {repo}{reset_color}\n")
    print(f"    Vulnerabilities:\n")
    print(f"        Critical - {stats['Critical']}")
    print(f"            \\_ High - {stats['High']}")
    print(f"                \\_ Medium - {stats['Medium']}")
    print(f"                      \\_ Low - {stats['Low']}\n")
    print(f"    Total Vulnerabilities: {stats['Total Vulnerabilities']}\n")

# Save results to a JSON file
output_file = "dependabot_alerts_report.json"
with open(output_file, 'w') as file:
    json.dump(results, file, indent=2)

print(f"{green}Results saved to {output_file}{reset_color}")
