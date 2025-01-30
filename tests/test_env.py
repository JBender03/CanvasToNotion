# test_env.py
from dotenv import load_dotenv
import os

load_dotenv()

# Check if variables are loaded
variables = [
    'CANVAS_API_KEY',
    'CANVAS_DOMAIN',
    'NOTION_API_KEY',
    'NOTION_DATABASE_ID'
]

for var in variables:
    value = os.getenv(var)
    print(f"{var}: {'✓ Found' if value else '✗ Missing'}")
    if value:
        # Only show first few characters of keys for security
        print(f"  First few chars: {value[:4]}...")