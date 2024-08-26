import os
import requests
import yaml
from dotenv import load_dotenv

# Load the project .env file to get GLOBAL_ENV_PATH
load_dotenv()

# Load the global .env file using the path from the project .env
global_env_path = os.getenv('GLOBAL_ENV_PATH')
if global_env_path and os.path.exists(global_env_path):
    load_dotenv(global_env_path)
else:
    raise ValueError("Error: GLOBAL_ENV_PATH is not set correctly or file does not exist.")

# Get the GitHub personal access token from environment variables
TOKEN = os.getenv('GITHUB_TOKEN')

# Load owner from YAML file
with open('Repo_List.yml', 'r') as file:
    config = yaml.safe_load(file)

OWNER = config['owner']

# Variable Error Check: Check for Missing Token
if not TOKEN:
    raise ValueError("Error: GITHUB_TOKEN environment variable is missing.")

# GitHub API URL to list repositories for the owner
url = f'https://api.github.com/users/{OWNER}/repos'

# Headers for the API request
headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Make the API request
response = requests.get(url, headers=headers)

# Check for successful response
if response.status_code == 200:
    repos = response.json()
    print(f"Repositories under {OWNER}:")
    for repo in repos:
        print(f"- {repo['name']}")
else:
    print(f"Failed to fetch repositories: {response.status_code}")
    print(response.json())
