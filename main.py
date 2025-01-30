import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

class CanvasNotionSync:
    def __init__(self, canvas_api_key: str, canvas_domain: str, notion_api_key: str, notion_database_id: str):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sync_log.txt'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.canvas_api_key = canvas_api_key
        canvas_domain = canvas_domain.rstrip('/')
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
        """Fetch current semester active courses from Canvas"""
        base_url = self.canvas_base_url.rstrip('/')
        
        response = requests.get(
            f"{base_url}/courses",
            headers=self.canvas_headers,
            params={
                "enrollment_state": "active",
                "include": "term",
                "enrollment_type": "student"
            }
        )
        response.raise_for_status()
        courses = response.json()
        
        current_courses = []
        for course in courses:
            if (course.get('term') and 
                '2025' in course['term'].get('name', '') and 
                'Spring' in course['term'].get('name', '') and
                not course['name'].startswith('ROLLA-NONCREDIT')):
                current_courses.append(course)
            
        return current_courses

    def get_course_assignments(self, course_id: int) -> List[Dict]:
        """Fetch assignments for a specific course"""
        response = requests.get(
            f"{self.canvas_base_url}/courses/{course_id}/assignments",
            headers=self.canvas_headers
        )
        response.raise_for_status()
        return response.json()

    def get_submission_status(self, course_id: int, assignment_id: int) -> str:
        """Get the submission status for an assignment"""
        response = requests.get(
            f"{self.canvas_base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self",
            headers=self.canvas_headers
        )
        if response.ok:
            submission = response.json()
            if submission.get('submitted_at'):
                if submission.get('graded_at'):
                    return "Graded"
                return "Submitted"
            return "Not Submitted"
        return "Unknown"

    def find_existing_page(self, assignment_name: str, course_name: str) -> Optional[str]:
        """Find existing Notion page for an assignment"""
        query = {
            "filter": {
                "and": [
                    {
                        "property": "Name",
                        "title": {
                            "equals": assignment_name
                        }
                    },
                    {
                        "property": "Course",
                        "rich_text": {
                            "equals": course_name
                        }
                    }
                ]
            }
        }

        response = requests.post(
            f"https://api.notion.com/v1/databases/{self.notion_database_id}/query",
            headers=self.notion_headers,
            json=query
        )
        
        if response.ok:
            results = response.json().get('results', [])
            if results:
                return results[0]['id']
        return None

    def update_page(self, page_id: str, properties: Dict) -> None:
        """Update an existing Notion page"""
        response = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=self.notion_headers,
            json={"properties": properties}
        )
        
        if not response.ok:
            self.logger.error(f"Error updating Notion page:")
            self.logger.error(f"Status code: {response.status_code}")
            self.logger.error(f"Response content: {response.text}")
        
        response.raise_for_status()

    def create_page(self, properties: Dict) -> None:
        """Create a new Notion page"""
        data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": properties
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=self.notion_headers,
            json=data
        )
        
        if not response.ok:
            self.logger.error(f"Error creating Notion page:")
            self.logger.error(f"Status code: {response.status_code}")
            self.logger.error(f"Response content: {response.text}")
        
        response.raise_for_status()

    def process_assignment(self, assignment: Dict, course_name: str, course_id: int) -> None:
        """Process a single assignment"""
        try:
            # Handle due date
            due_date = assignment.get('due_at')
            if due_date:
                try:
                    parsed_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(due_date.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        self.logger.warning(f"Could not parse date: {due_date}")
                        parsed_date = None
                due_date = parsed_date.date().isoformat() if parsed_date else None

            # Handle points
            points = assignment.get('points_possible')
            if points is None:
                points = 0
            else:
                try:
                    points = float(points)
                except (ValueError, TypeError):
                    points = 0

            # Get submission status
            submission_status = self.get_submission_status(course_id, assignment['id'])

            # Create properties
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
                    "number": points
                },
                "Status": {
                    "status": {
                        "name": "Done" if submission_status in ["Graded", "Submitted"] else "Not started"
                    }
                },
                "Submission Status": {
                    "select": {
                        "name": submission_status
                    }
                },
                "Canvas URL": {
                    "url": assignment.get('html_url', '')
                }
            }

            # Check for existing page
            existing_page_id = self.find_existing_page(assignment['name'], course_name)

            if existing_page_id:
                self.logger.info(f"Updating existing page for: {assignment['name']}")
                self.update_page(existing_page_id, properties)
            else:
                self.logger.info(f"Creating new page for: {assignment['name']}")
                self.create_page(properties)

        except Exception as e:
            self.logger.error(f"Error processing assignment {assignment.get('name', 'Unknown')}: {str(e)}")
            raise

    def sync_assignments(self):
        """Main function to sync Canvas assignments to Notion"""
        try:
            # Get all active courses
            courses = self.get_canvas_courses()
            self.logger.info(f"Found {len(courses)} current semester courses")
            
            for course in courses:
                course_name = course['name']
                course_id = course['id']
                self.logger.info(f"Processing course: {course_name}")
                
                # Get assignments for each course
                assignments = self.get_course_assignments(course['id'])
                self.logger.info(f"Found {len(assignments)} assignments in {course_name}")
                
                for assignment in assignments:
                    try:
                        self.process_assignment(assignment, course_name, course_id)
                    except Exception as e:
                        self.logger.error(f"Failed to process assignment: {str(e)}")
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            raise

def main():
    try:
        # Load environment variables
        load_dotenv()
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
        logger = logging.getLogger(__name__)
        logger.info("Starting Canvas to Notion sync")
        syncer = CanvasNotionSync(canvas_api_key, canvas_domain, notion_api_key, notion_database_id)
        syncer.sync_assignments()
        logger.info("Sync completed successfully")

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Sync failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()