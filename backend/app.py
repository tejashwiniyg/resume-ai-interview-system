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
import requests
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
            password TEXT NOT NULL
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interview_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
  #interview session table 
    conn.execute("""
    CREATE TABLE IF NOT EXISTS interview_session (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        round_type TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    #interview answers table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS interview_answers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        answer_text TEXT NOT NULL
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
    current_user_id = int(claims["sub"])
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

    conn = get_db_connection()

    final_questions = []

    # Fetch 3 random technical questions per detected skill
    for skill in detected_skills:
        questions = conn.execute(
            """
            SELECT * FROM question
            WHERE skill_tag = ? AND category = 'Technical'
            AND question_id NOT IN (
                SELECT question_id FROM interview_history
                WHERE user_id = ?
            )
            ORDER BY RANDOM()
            LIMIT 3
            """,
            (skill, current_user_id)
        ).fetchall()
        for q in questions:
            final_questions.append({
                "skill": skill,
                "question_text": q["question_text"],
                "difficulty": q["difficulty"]
            })
            conn.execute(
                "INSERT INTO interview_history (user_id, question_id) VALUES (?, ?)",
                (current_user_id, q["question_id"])
            )
    conn.commit()
    conn.close()

    return jsonify({
        "detected_skills": detected_skills,
        "questions": final_questions
    })
#aptitude
@app.route("/aptitude-practice", methods=["GET"])
@jwt_required()
def aptitude_practice():
    claims = get_jwt()
    current_user_id = int(claims["sub"])

    conn = get_db_connection()

    questions = conn.execute(
        """
        SELECT * FROM question
        WHERE category = 'Aptitude'
        AND question_id NOT IN (
            SELECT question_id FROM interview_history
            WHERE user_id = ?
        )
        ORDER BY RANDOM()
        LIMIT 5
        """,
        (current_user_id,)
    ).fetchall()

    final_questions = []

    for q in questions:
        final_questions.append({
            "question_text": q["question_text"],
            "difficulty": q["difficulty"]
        })

        conn.execute(
            "INSERT INTO interview_history (user_id, question_id) VALUES (?, ?)",
            (current_user_id, q["question_id"])
        )

    conn.commit()
    conn.close()

    return jsonify(final_questions)
@app.route("/hr-round", methods=["GET"])
@jwt_required()
def hr_round():
    claims = get_jwt()
    current_user_id = int(claims["sub"])

    prompt = """
    Generate 5 scenario-based HR interview questions 
    for a final year Computer Science student applying 
    for a software engineering role.
    Questions should be practical and problem-solving based.
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    return jsonify({
        "mode": "AI HR Round",
        "questions": data["response"]
    })
# START HR ROUND (SINGLE QUESTION + SESSION CREATION)
@app.route("/start-hr-round", methods=["POST"])
@jwt_required()
def start_hr_round():
    claims = get_jwt()
    user_id = int(claims["sub"])

    if claims["role"] != "Student":
        return jsonify({"error": "Access denied"}), 403

    conn = get_db_connection()

    # Create new session
    cursor = conn.execute(
        "INSERT INTO interview_session (user_id, round_type) VALUES (?, ?)",
        (user_id, "HR")
    )
    session_id = cursor.lastrowid
    conn.commit()

    # Generate ONE HR question
    prompt = """
    Generate ONE realistic scenario-based HR interview question 
    for a final year Computer Science student.
    Do not number it. Just give the question.
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )

    question_text = response.json()["response"].strip()

    conn.close()

    return jsonify({
        "session_id": session_id,
        "question": question_text
    })
# SUBMIT HR ANSWER + GET NEXT QUESTION
@app.route("/submit-hr-answer", methods=["POST"])
@jwt_required()
def submit_hr_answer():
    claims = get_jwt()
    user_id = int(claims["sub"])

    data = request.get_json()
    session_id = data.get("session_id")
    question = data.get("question")
    answer = data.get("answer")

    if not session_id or not question or not answer:
        return jsonify({"error": "Missing data"}), 400

    conn = get_db_connection()

    # Store answer
    conn.execute(
        "INSERT INTO interview_answers (session_id, question_text, answer_text) VALUES (?, ?, ?)",
        (session_id, question, answer)
    )
    conn.commit()

    # Generate next question
    prompt = """
    Generate ONE new scenario-based HR interview question 
    different from previous typical ones.
    Do not number it.
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )

    next_question = response.json()["response"].strip()

    conn.close()

    return jsonify({
        "next_question": next_question
    })
# END HR ROUND + GET FINAL FEEDBACK
@app.route("/end-hr-round", methods=["POST"])
@jwt_required()
def end_hr_round():
    claims = get_jwt()
    user_id = int(claims["sub"])

    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "Session ID required"}), 400

    conn = get_db_connection()

    answers = conn.execute(
        "SELECT question_text, answer_text FROM interview_answers WHERE session_id = ?",
        (session_id,)
    ).fetchall()

    full_interview_text = ""

    for row in answers:
        full_interview_text += f"Question: {row['question_text']}\n"
        full_interview_text += f"Answer: {row['answer_text']}\n\n"

    conn.close()

    evaluation_prompt = f"""
    Evaluate the following HR interview session.

    {full_interview_text}

    Provide:
    - Overall score out of 10
    - Communication score
    - Confidence level
    - Strengths
    - Weaknesses
    - Final improvement suggestions
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": evaluation_prompt,
            "stream": False
        }
    )

    feedback = response.json()["response"]

    return jsonify({
        "final_feedback": feedback
    })
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
