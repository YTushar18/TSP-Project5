from flask import Flask, render_template
import os
import subprocess
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_app')
def start_app():
    # The path to your PyQt5 application script
    try:
        if sys.platform.startswith('win'):
            p = subprocess.Popen(['python', 'app.py'], shell=True)
        else:
            p = subprocess.Popen(['python3', 'app.py'])
        return "Application started successfully!", 200
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)
