import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

questions = [
# ---- PYTHON ----
("What is Python?", "Technical", "Easy", "Python"),
("Explain OOP concepts.", "Technical", "Medium", "Python"),
("What is list comprehension?", "Technical", "Medium", "Python"),
("What are decorators?", "Technical", "Hard", "Python"),
("What is lambda function?", "Technical", "Medium", "Python"),

# ---- SQL ----
("What is SQL?", "Technical", "Easy", "SQL"),
("Explain joins.", "Technical", "Medium", "SQL"),
("What is normalization?", "Technical", "Medium", "SQL"),
("Explain ACID properties.", "Technical", "Hard", "SQL"),
("What is index?", "Technical", "Hard", "SQL"),

# ---- HTML ----
("What is HTML?", "Technical", "Easy", "HTML"),
("What are semantic tags?", "Technical", "Medium", "HTML"),
("Difference between div and span?", "Technical", "Easy", "HTML"),

# ---- CSS ----
("What is CSS?", "Technical", "Easy", "CSS"),
("Explain box model.", "Technical", "Medium", "CSS"),
("What is flexbox?", "Technical", "Medium", "CSS"),

# ---- HR ----
("Tell me about yourself.", "HR", "Easy", "HR"),
("Why should we hire you?", "HR", "Medium", "HR"),
("What are your strengths?", "HR", "Easy", "HR"),
("Describe a challenging situation.", "HR", "Hard", "HR"),

# ---- STRESS ----
("Why are your grades low?", "Stress", "Hard", "Stress"),
("Why is there a gap in your resume?", "Stress", "Hard", "Stress"),
("Why should we not hire you?", "Stress", "Hard", "Stress"),
]

cursor.executemany(
    "INSERT INTO question (question_text, category, difficulty, skill_tag) VALUES (?, ?, ?, ?)",
    questions
)

conn.commit()
conn.close()

print("Questions inserted successfully!")