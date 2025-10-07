from flask import Flask, request, render_template_string
import psycopg2
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Database connection function using environment variables
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT", 5432)
    )
    return conn

# Simple HTML template
HTML_TEMPLATE = """
<!doctype html>
<title>Student Results Lookup</title>
<h2>Enter your Matric Number to view your EEG 326 score for the 2024/2025 session </h2>
<form method="POST">
  <input type="text" name="matric_no" placeholder="Matric Number" required>
  <input type="submit" value="Check Results">
</form>
{% if result %}
  <h3>Result for {{ result.student_name }} ({{ result.matric_no }})</h3>
  <ul>
  <li> CA <em>/40</em>: {{ result.ca }}</li>
  <li>Exam <em>/60</em>: {{ result.exam }}</li>
  <li>Total <em>/100</em>: {{ result.total }}</li>
  </ul>
{% elif searched %}
  <p><strong>No results found for Matric Number: {{ matric_no }}</strong></p>
{% endif %}
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    searched = False
    matric_no = ""

    if request.method == 'POST':
        matric_no = request.form['matric_no'].strip()
        searched = True

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT student_name, matric_no, ca, exam, total FROM student_results WHERE matric_no = %s", (matric_no,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            result = {
                "student_name": row[0],
                "matric_no": row[1],
                "ca": row[2],
                "exam": row[3],
                "total": row[4]
            }

    return render_template_string(HTML_TEMPLATE, result=result, searched=searched, matric_no=matric_no)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
