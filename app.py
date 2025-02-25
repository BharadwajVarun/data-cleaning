from flask import Flask, render_template, url_for
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_preprocessing')
def start_preprocessing():
    try:
        subprocess.Popen(['python', 'new2.py'])
    except Exception as e:
        return f"Error starting the preprocessing application: {e}"
    return "Preprocessing application started."

if __name__ == '__main__':
    app.run(debug=True)
