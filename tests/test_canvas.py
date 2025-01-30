# test_canvas.py
from dotenv import load_dotenv
import os
import requests

load_dotenv()

api_key = os.getenv('CANVAS_API_KEY')
domain = os.getenv('CANVAS_DOMAIN')

url = f"https://{domain}/api/v1/courses"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    courses = response.json()
    print("Canvas Connection Successful!")
    print(f"Found {len(courses)} courses:")
    for course in courses:
        print(f"- {course.get('name', 'Unnamed course')}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to Canvas: {str(e)}")