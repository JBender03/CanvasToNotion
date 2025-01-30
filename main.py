import os
import requests
from datetime import datetime
from typing import Dict, List, Optional

class CanvasNotionSync:
    def __init__(self, canvas_api_key: str, canvas_domain: str, notion_api_key: str, notion_database_id: str):
        self.canvas_api_key = canvas_api_key
        self.canvas_base_url = f"https://{canvas_domain}/api/v1"
        self.notion_api_key = notion_api_key
        self.notion_database_id = notion_database_id
        
        # Headers for API requests
        self.canvas_headers = {
            "Authorization": f"Bearer {self.canvas_api_key}"
        }
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def get_canvas_courses(self) -> List[Dict]:
        """Fetch active courses from Canvas"""
        response = requests.get(
            f"{self.canvas_base_url}/courses",
            headers=self.canvas_headers,
            params={"enrollment_state": "active"}
        )
        response.raise_for_status()
        return response.json()

    def get_course_assignments(self, course_id: int) -> List[Dict]:
        """Fetch assignments for a specific course"""
        response = requests.get(
            f"{self.canvas_base_url}/courses/{course_id}/assignments",
            headers=self.canvas_headers
        )
        response.raise_for_status()
        return response.json()

    def create_notion_page(self, assignment: Dict, course_name: str) -> None:
        """Create a new page in Notion for an assignment"""
        due_date = assignment.get('due_at')
        if due_date:
            due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ").date().isoformat()

        properties = {
            "Name": {
                "title": [{"text": {"content": assignment['name']}}]
            },
            "Course": {
                "rich_text": [{"text": {"content": course_name}}]
            },
            "Due Date": {
                "date": {"start": due_date} if due_date else None
            },
            "Points": {
                "number": assignment.get('points_possible', 0)
            },
            "Status": {
                "select": {"name": "Not Started"}
            },
            "Canvas URL": {
                "url": assignment.get('html_url', '')
            }
        }

        data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": properties
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=self.notion_headers,
            json=data
        )
        response.raise_for_status()

    def sync_assignments(self):
        """Main function to sync Canvas assignments to Notion"""
        try:
            # Get all active courses
            courses = self.get_canvas_courses()
            
            for course in courses:
                course_name = course['name']
                print(f"Processing course: {course_name}")
                
                # Get assignments for each course
                assignments = self.get_course_assignments(course['id'])
                
                for assignment in assignments:
                    try:
                        print(f"Creating Notion page for assignment: {assignment['name']}")
                        self.create_notion_page(assignment, course_name)
                    except requests.exceptions.RequestException as e:
                        print(f"Error creating Notion page for {assignment['name']}: {str(e)}")
                        continue
                    
        except requests.exceptions.RequestException as e:
            print(f"Error during sync: {str(e)}")
            raise

def main():
    # Load environment variables
    canvas_api_key = os.getenv("CANVAS_API_KEY")
    canvas_domain = os.getenv("CANVAS_DOMAIN") 
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    # Validate environment variables
    required_vars = {
        "CANVAS_API_KEY": canvas_api_key,
        "CANVAS_DOMAIN": canvas_domain,
        "NOTION_API_KEY": notion_api_key,
        "NOTION_DATABASE_ID": notion_database_id
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Initialize and run sync
    syncer = CanvasNotionSync(canvas_api_key, canvas_domain, notion_api_key, notion_database_id)
    syncer.sync_assignments()

if __name__ == "__main__":
    main()