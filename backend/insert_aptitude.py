import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

aptitude_questions = [
    ("What is 20% of 250?", "Aptitude", "Easy", "Quantitative"),
    ("If a train travels 120 km in 2 hours, what is its speed?", "Aptitude", "Easy", "Quantitative"),
    ("Find the compound interest on 1000 at 10% for 2 years.", "Aptitude", "Medium", "Quantitative"),
    ("A man buys an item for 500 and sells for 650. Find profit percentage.", "Aptitude", "Easy", "Quantitative"),
    ("If 5 workers complete work in 10 days, how many days for 10 workers?", "Aptitude", "Medium", "Quantitative"),
    ("Solve: 2x + 5 = 15", "Aptitude", "Easy", "Quantitative"),
    ("Find average of 10, 20, 30, 40.", "Aptitude", "Easy", "Quantitative"),
    ("What is the ratio of 15:45?", "Aptitude", "Easy", "Quantitative"),
    ("Probability of getting head when tossing coin?", "Aptitude", "Easy", "Quantitative"),
    ("Find simple interest on 2000 at 5% for 3 years.", "Aptitude", "Medium", "Quantitative"),
]

for q in aptitude_questions:
    cursor.execute(
        "INSERT INTO question (question_text, category, difficulty, skill_tag) VALUES (?, ?, ?, ?)",
        q
    )

conn.commit()
conn.close()

print("Aptitude questions inserted successfully!")