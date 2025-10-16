from flask import Flask, request, render_template_string
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables for local testing (optional)
load_dotenv()

app = Flask(__name__)

# --- Database Connection ---
def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")

    # psycopg2 prefers postgres:// instead of postgresql://
    if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgres://", 1)

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')  # Supabase requires SSL
        print("✅ Database connection established.")
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None


# --- HTML Template ---
HTML_TEMPLATE = """
<!doctype html>
<title>Student Results Lookup</title>
<h2>Enter your Matric Number to view your EEG 346 result for the 2024/2025 session</h2>
<form method="POST">
  <input type="text" name="matric_no" placeholder="Matric Number" required>
  <input type="submit" value="Check Results">
</form>
{% if result %}
  <h3>Result for {{ result.student_name }} ({{ result.matric_no }})</h3>
  <ul>
    <li>Lab score <em>/30</em>: {{ result.ca }}</li>
    <li>Exam <em>/70</em>: {{ result.exam }}</li>
    <li>Total <em>/100</em>: {{ result.total }}</li>
  </ul>
{% elif searched %}
  <p><strong>No results found for Matric Number: {{ matric_no }}</strong></p>
{% endif %}
"""


# --- Home Route ---
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    searched = False
    matric_no = ""

    if request.method == 'POST':
        matric_no = request.form['matric_no'].strip()
        searched = True
        print(f"🔍 Searching for matric number: {matric_no}")

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                # Use BTRIM to remove leading/trailing spaces from DB values
                cur.execute("""
                    SELECT student_name, matric_no, ca, exam, total
                    FROM public.student_results
                    WHERE BTRIM(matric_no) = %s
                """, (matric_no,))
                row = cur.fetchone()
                print("🧾 Query result:", row)
            except Exception as e:
                print("⚠️ Query failed:", e)
                row = None
            finally:
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
        else:
            print("❌ Unable to connect to database — please verify DATABASE_URL or Supabase connectivity.")

    return render_template_string(HTML_TEMPLATE, result=result, searched=searched, matric_no=matric_no)


# --- Debug Route to Test DB Connection ---
@app.route('/testdb')
def testdb():
    try:
        conn = get_db_connection()
        if not conn:
            return "❌ Could not connect to database."
        cur = conn.cursor()
        cur.execute("SELECT current_database();")
        dbname = cur.fetchone()[0]
        cur.close()
        conn.close()
        return f"✅ Connected successfully to database: {dbname}"
    except Exception as e:
        return f"❌ Database connection error: {e}"


# --- Temporary route to check stored matric numbers ---
@app.route('/check')
def check_db():
    conn = get_db_connection()
    if not conn:
        return "❌ Cannot connect"
    cur = conn.cursor()
    cur.execute("SELECT matric_no FROM public.student_results LIMIT 10;")
    sample = cur.fetchall()
    cur.close()
    conn.close()
    return f"Sample matric numbers: {sample}"


# --- App Runner ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
