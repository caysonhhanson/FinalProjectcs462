import sys
import os
sys.path.insert(0, os.getcwd())
from flask import Flask

app = Flask('src.web.app', template_folder='src/web/templates')

@app.route('/')
def test():
    return '<h1>Flask is working</h1>'

if __name__ == '__main__':
    app.run(port=5000, debug=True)
