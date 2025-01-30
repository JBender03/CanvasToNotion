# test_notion.py
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

api_key = os.getenv('NOTION_API_KEY')
database_id = os.getenv('NOTION_DATABASE_ID')

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

url = f"https://api.notion.com/v1/databases/{database_id}"

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    database = response.json()
    print("\nNotion Database Properties:")
    print(json.dumps(database['properties'], indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error connecting to Notion: {str(e)}")