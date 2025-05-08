import sqlite3

# Create a new SQLite database (or overwrite if deleted)
conn = sqlite3.connect("questions.db")
cursor = conn.cursor()

# Create the 'questions' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    row INTEGER NOT NULL,
    col INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
""")

# Insert some sample questions
sample_questions = [
    ("Sport", 0, 0, "What is the fastest land animal?", "Cheetah"),
    ("Sport", 1, 0, "How many players are in a soccer team?", "11"),
    ("Geograafia", 0, 1, "What is the capital of France?", "Paris"),
    ("Geograafia", 1, 1, "What is the largest ocean?", "Pacific Ocean"),
    ("Loodus", 0, 2, "What is the tallest tree species?", "Redwood"),
    ("Kultuur", 1, 3, "Who painted the Mona Lisa?", "Leonardo da Vinci"),
    ("Varia", 0, 4, "What is the chemical symbol for gold?", "Au")
]

# Insert the sample data
cursor.executemany("INSERT INTO questions (category, row, col, question, answer) VALUES (?, ?, ?, ?, ?)", sample_questions)

# Commit and close the connection
conn.commit()
conn.close()

print("✅ Database recreated successfully with sample questions!")
