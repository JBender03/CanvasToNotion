import os
import sys
# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# test_current_courses.py
from main import CanvasNotionSync
from dotenv import load_dotenv
import json
import requests

load_dotenv()

def test_current_courses():
    syncer = CanvasNotionSync(
        canvas_api_key=os.getenv('CANVAS_API_KEY'),
        canvas_domain=os.getenv('CANVAS_DOMAIN'),
        notion_api_key=os.getenv('NOTION_API_KEY'),
        notion_database_id=os.getenv('NOTION_DATABASE_ID')
    )
    
    # Print raw response first
    print("\nFetching courses...")
    response = requests.get(
        f"{syncer.canvas_base_url}/courses",
        headers=syncer.canvas_headers,
        params={
            "enrollment_state": "active",
            "include": "term",
            "enrollment_type": "student"
        }
    )
    
    courses = response.json()
    print("\nAll courses found:")
    for course in courses:
        print(f"\nCourse details:")
        print(f"Name: {course.get('name')}")
        print(f"Term: {course.get('term', {}).get('name') if course.get('term') else 'No term info'}")
        
    print("\nFiltered current semester courses:")
    current_courses = syncer.get_canvas_courses()
    if not current_courses:
        print("No current semester courses found!")
    for course in current_courses:
        print(f"- {course['name']} ({course['term']['name']})")

if __name__ == "__main__":
    test_current_courses()