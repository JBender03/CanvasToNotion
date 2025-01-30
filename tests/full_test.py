import os
import sys
import unittest
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the path for importing main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import CanvasNotionSync

class TestCanvasNotionSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        load_dotenv()
        cls.canvas_api_key = os.getenv("CANVAS_API_KEY")
        cls.canvas_domain = os.getenv("CANVAS_DOMAIN")
        cls.notion_api_key = os.getenv("NOTION_API_KEY")
        cls.notion_database_id = os.getenv("NOTION_DATABASE_ID")
        
        cls.syncer = CanvasNotionSync(
            cls.canvas_api_key,
            cls.canvas_domain,
            cls.notion_api_key,
            cls.notion_database_id
        )

    def test_1_environment_variables(self):
        """Test that all required environment variables are set"""
        print("\nTesting environment variables...")
        required_vars = {
            "CANVAS_API_KEY": self.canvas_api_key,
            "CANVAS_DOMAIN": self.canvas_domain,
            "NOTION_API_KEY": self.notion_api_key,
            "NOTION_DATABASE_ID": self.notion_database_id
        }
        
        for var_name, var_value in required_vars.items():
            print(f"Checking {var_name}...")
            self.assertIsNotNone(var_value, f"{var_name} is not set")
            self.assertNotEqual(var_value, "", f"{var_name} is empty")
            print(f"✓ {var_name} is properly set")

    def test_2_canvas_connection(self):
        """Test Canvas API connection and course retrieval"""
        print("\nTesting Canvas connection and course retrieval...")
        courses = self.syncer.get_canvas_courses()
        self.assertIsInstance(courses, list, "get_canvas_courses should return a list")
        print(f"Found {len(courses)} current semester courses:")
        for course in courses:
            print(f"- {course['name']}")
            self.assertIn('id', course, "Course should have an ID")
            self.assertIn('name', course, "Course should have a name")
            self.assertIn('term', course, "Course should have term information")

    def test_3_assignments(self):
        """Test assignment retrieval for the first course"""
        print("\nTesting assignment retrieval...")
        courses = self.syncer.get_canvas_courses()
        if not courses:
            self.skipTest("No courses found to test assignments")
        
        test_course = courses[0]
        print(f"Testing with course: {test_course['name']}")
        assignments = self.syncer.get_course_assignments(test_course['id'])
        
        self.assertIsInstance(assignments, list, "get_course_assignments should return a list")
        print(f"Found {len(assignments)} assignments:")
        for assignment in assignments:
            print(f"- {assignment['name']}")
            self.assertIn('id', assignment, "Assignment should have an ID")
            self.assertIn('name', assignment, "Assignment should have a name")

    def test_4_submission_status(self):
        """Test submission status retrieval"""
        print("\nTesting submission status retrieval...")
        courses = self.syncer.get_canvas_courses()
        if not courses:
            self.skipTest("No courses found to test submission status")
            
        test_course = courses[0]
        assignments = self.syncer.get_course_assignments(test_course['id'])
        if not assignments:
            self.skipTest("No assignments found to test submission status")
            
        test_assignment = assignments[0]
        status = self.syncer.get_submission_status(test_course['id'], test_assignment['id'])
        print(f"Submission status for '{test_assignment['name']}': {status}")
        self.assertIn(status, ["Not Submitted", "Submitted", "Graded", "Unknown"])

    def test_5_notion_connection(self):
        """Test Notion API connection by creating a test page"""
        print("\nTesting Notion connection...")
        test_assignment = {
            'name': 'Test Assignment (Will be deleted)',
            'due_at': datetime.now().isoformat() + 'Z',
            'points_possible': 100,
            'html_url': 'https://example.com',
            'id': 0
        }
        
        try:
            self.syncer.create_notion_page(
                assignment=test_assignment,
                course_name="TEST COURSE",
                course_id=0
            )
            print("✓ Successfully created test page in Notion")
        except Exception as e:
            self.fail(f"Failed to create Notion page: {str(e)}")

if __name__ == '__main__':
    print("Starting comprehensive test suite...")
    print("This will test all components of the Canvas-Notion sync system.")
    print("Make sure you have added the 'Submission Status' property to your Notion database!")
    print("=" * 50)
    unittest.main(verbosity=2)