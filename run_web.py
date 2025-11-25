import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app

if __name__ == '__main__':
    print("🚀 Starting CarWatch Web App...")
    print("📍 Open your browser to: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)
