import os
import sys
# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import CanvasNotionSync
from dotenv import load_dotenv

load_dotenv()

def test_sync():
    syncer = CanvasNotionSync(
        canvas_api_key=os.getenv('CANVAS_API_KEY'),
        canvas_domain=os.getenv('CANVAS_DOMAIN'),
        notion_api_key=os.getenv('NOTION_API_KEY'),
        notion_database_id=os.getenv('NOTION_DATABASE_ID')
    )
    
    # Get first course only for testing
    courses = syncer.get_canvas_courses()
    if not courses:
        print("No courses found!")
        return
        
    test_course = courses[0]
    print(f"Testing with course: {test_course['name']}")
    
    # Get assignments for test course
    assignments = syncer.get_course_assignments(test_course['id'])
    print(f"Found {len(assignments)} assignments")
    
    # Sync first assignment only
    if assignments:
        test_assignment = assignments[0]
        print(f"Testing sync with assignment: {test_assignment['name']}")
        syncer.create_notion_page(test_assignment, test_course['name'])
        print("Test sync completed!")

if __name__ == "__main__":
    test_sync()