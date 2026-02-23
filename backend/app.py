from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt,
)
import PyPDF2
import sqlite3

app = Flask(__name__)
CORS(app)

# -----------------------------
# JWT CONFIGURATION
# -----------------------------
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)

DATABASE = "database.db"

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# CREATE TABLES
# -----------------------------
def create_tables():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS question (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            skill_tag TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

create_tables()

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return {"message": "Backend running with JWT and Database"}

# -----------------------------
# REGISTER ROUTE
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not name or not email or not password or not role:
        return jsonify({"error": "All fields required"}), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO user (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, password, role)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM user WHERE email = ? AND password = ?",
        (email, password)
    ).fetchone()
    conn.close()

    if user:
        access_token = create_access_token(
            identity=str(user["user_id"]),
            additional_claims={"role": user["role"]}
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# -----------------------------
# STUDENT PROTECTED ROUTE
# -----------------------------
@app.route("/student-dashboard", methods=["GET"])
@jwt_required()
def student_dashboard():
    claims = get_jwt()

    if claims["role"] != "Student":
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"message": "Welcome Student"})

# -----------------------------
# HR PROTECTED ROUTE
# -----------------------------
@app.route("/hr-dashboard", methods=["GET"])
@jwt_required()
def hr_dashboard():
    claims = get_jwt()

    if claims["role"] != "HR":
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"message": "Welcome HR"})

# -----------------------------
# ADD QUESTION (HR ONLY)
# -----------------------------
@app.route("/add-question", methods=["POST"])
@jwt_required()
def add_question():
    claims = get_jwt()

    if claims["role"] != "HR":
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()

    question_text = data.get("question_text")
    category = data.get("category")
    difficulty = data.get("difficulty")
    skill_tag = data.get("skill_tag")

    if not question_text or not category or not difficulty or not skill_tag:
        return jsonify({"error": "All fields required"}), 400

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO question (question_text, category, difficulty, skill_tag) VALUES (?, ?, ?, ?)",
        (question_text, category, difficulty, skill_tag)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Question added successfully"})

# -----------------------------
# GET QUESTIONS BY SKILL (STUDENT)
# -----------------------------
@app.route("/get-questions", methods=["POST"])
@jwt_required()
def get_questions():
    claims = get_jwt()

    if claims["role"] != "Student":
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    skill = data.get("skill")
    category = data.get("category")

    if not skill or not category:
        return jsonify({"error": "Skill and category required"}), 400

    conn = get_db_connection()
    questions = conn.execute(
        "SELECT * FROM question WHERE skill_tag = ? AND category = ?",
        (skill, category)
    ).fetchall()
    conn.close()

    result = []
    for q in questions:
        result.append({
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "difficulty": q["difficulty"]
        })

    return jsonify(result)

# -----------------------------
# RESUME UPLOAD + SKILL DETECTION (FIXED)
# -----------------------------
@app.route("/upload-resume", methods=["POST"])
@jwt_required()
def upload_resume():
    claims = get_jwt()

    if claims["role"] != "Student":
        return jsonify({"error": "Access denied"}), 403

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Read PDF
    pdf_reader = PyPDF2.PdfReader(file)
    resume_text = ""

    for page in pdf_reader.pages:
        resume_text += page.extract_text()

    # UPDATED SKILL DETECTION LOGIC
    skill_list = ["Python", "Java", "SQL", "React", "Machine Learning", "HTML", "CSS"]

    # Clean text (important fix)
    clean_text = resume_text.replace("\n", " ")
    clean_text = clean_text.replace(" ", "")
    clean_text = clean_text.lower()

    detected_skills = []

    for skill in skill_list:
        if skill.lower().replace(" ", "") in clean_text:
            detected_skills.append(skill)

    return jsonify({
        "detected_skills": detected_skills,
        "resume_text_sample": resume_text[:500]
    })

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
