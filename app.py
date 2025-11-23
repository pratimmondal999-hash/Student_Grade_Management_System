from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json

app = Flask(__name__)
CORS(app)

DB = "students_subjects.db"

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            marks TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ----------------- HELPER FUNCTIONS -----------------
def calculate_grade(marks_list):
    if not marks_list:
        return "N/A"
    avg = sum(marks_list)/len(marks_list)
    if avg >= 90: return "A+"
    elif avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "F"

def calculate_cgpa(marks_list):
    if not marks_list:
        return 0.0
    avg = sum(marks_list)/len(marks_list)
    if avg >= 90: return 10
    elif avg >= 80: return 9
    elif avg >= 70: return 8
    elif avg >= 60: return 7
    elif avg >= 50: return 6
    elif avg >= 40: return 5
    else: return 4

# Initialize DB
init_db()

# ----------------- AUTH ROUTES -----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    if not username or not password:
        return jsonify({"error":"Username and password required"}),400
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",
                       (username, generate_password_hash(password)))
        conn.commit()
        return jsonify({"message":"Registration successful!"}),200
    except sqlite3.IntegrityError:
        return jsonify({"error":"Username already exists"}),400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username","").strip()
    password = data.get("password","").strip()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?",(username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error":"User not found"}),404
    hashed_password = row[0]
    if check_password_hash(hashed_password,password):
        return jsonify({"success":True,"message":"Login successful"}),200
    else:
        return jsonify({"success":False,"error":"Invalid password"}),401

# ----------------- STUDENT ROUTES -----------------
@app.route('/add', methods=['POST'])
def add_student():
    data = request.json
    roll = data.get("roll","").strip()
    name = data.get("name","").strip()
    marks_dict = data.get("marks",{})  # e.g., {"Math":95,"Physics":90}
    if not roll or not name:
        return jsonify({"error":"Roll and Name required"}),400
    marks_json = json.dumps(marks_dict)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (roll,name,marks) VALUES (?,?,?)",
                       (roll,name,marks_json))
        conn.commit()
        return jsonify({"message":"Student added successfully!"}),200
    except sqlite3.IntegrityError:
        return jsonify({"error":"Roll number already exists"}),400
    finally:
        conn.close()

@app.route('/update/<roll>', methods=['PUT'])
def update_student(roll):
    data = request.json
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE roll=?",(roll,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error":"Student not found"}),404
    student_id = row[0]
    new_name = data.get("name",None)
    new_marks = data.get("marks", None)
    if new_name:
        cursor.execute("UPDATE students SET name=? WHERE id=?",(new_name,student_id))
    if new_marks is not None:
        marks_json = json.dumps(new_marks)
        cursor.execute("UPDATE students SET marks=? WHERE id=?",(marks_json,student_id))
    conn.commit()
    conn.close()
    return jsonify({"message":"Student updated successfully!"}),200

@app.route('/show', methods=['GET'])
def show_students():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT roll,name,marks FROM students")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for roll,name,marks_json in rows:
        marks_dict = json.loads(marks_json) if marks_json else {}
        marks_list = list(marks_dict.values())
        total = sum(marks_list)
        num_subjects = len(marks_list) if marks_list else 1
        percentage = total / (num_subjects*100) * 100
        result.append({
            "roll": roll,
            "name": name,
            "marks": marks_dict,
            "total_marks": total,
            "percentage": round(percentage,2),
            "grade": calculate_grade(marks_list),
            "cgpa": calculate_cgpa(marks_list)
        })
    return jsonify(result),200

@app.route('/search/<roll>', methods=['GET'])
def search_student(roll):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT roll,name,marks FROM students WHERE roll=?",(roll,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error":"Student not found"}),404
    marks_dict = json.loads(row[2]) if row[2] else {}
    marks_list = list(marks_dict.values())
    total = sum(marks_list)
    num_subjects = len(marks_list) if marks_list else 1
    percentage = total / (num_subjects*100) * 100
    return jsonify({
        "roll": row[0],
        "name": row[1],
        "marks": marks_dict,
        "total_marks": total,
        "percentage": round(percentage,2),
        "grade": calculate_grade(marks_list),
        "cgpa": calculate_cgpa(marks_list)
    }),200

@app.route('/delete/<roll>', methods=['DELETE'])
def delete_student(roll):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE roll=?",(roll,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error":"Student not found"}),404
    conn.commit()
    conn.close()
    return jsonify({"message":"Student deleted successfully!"}),200

# ----------------- RUN SERVER -----------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)







