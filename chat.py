
import sqlite3
import re
import ollama
import sympy as sp

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "ai_memory.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def setup_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        fact TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS problem_memory_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        topic TEXT,
        solution TEXT,
        correct INTEGER,
        mistake TEXT
    )
    """)

    conn.commit()
    conn.close()


setup_database()


# =========================================================
# PERSONAL MEMORY
# =========================================================

def save_memory(fact, value):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO memory (fact, value)
    VALUES (?, ?)
    """, (fact, value))

    conn.commit()
    conn.close()


def get_memory(fact):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT value FROM memory WHERE fact=?",
        (fact,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


def remember(text):

    patterns = {

        "name":
            r"my name is (.+)",

        "favourite food":
            r"my favou?rite food is (.+)",

        "favourite subject":
            r"my favou?rite subject is (.+)",

        "hobby":
            r"my hobby is (.+)",

        "city":
            r"(?:i live in|my city is) (.+)",

        "school":
            r"(?:i study in|my school is) (.+)",

        "goal":
            r"(?:my goal is|i want to become) (.+)",

        "favourite colour":
            r"my favou?rite colou?r is (.+)"
    }

    for fact, pattern in patterns.items():

        match = re.fullmatch(
            pattern,
            text.strip(),
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            save_memory(
                fact,
                value
            )

            return fact, value

    return None, None


def recall(text):

    t = text.lower().strip()

    questions = {

        "name": [
            "what is my name",
            "what's my name",
            "who am i"
        ],

        "favourite food": [
            "what is my favourite food",
            "what's my favourite food",
            "what is my fav food"
        ],

        "favourite subject": [
            "what is my favourite subject",
            "what's my favourite subject",
            "what is my fav subject"
        ],

        "hobby": [
            "what is my hobby",
            "what's my hobby"
        ],

        "city": [
            "what is my city",
            "where do i live"
        ],

        "school": [
            "what is my school",
            "where do i study"
        ],

        "goal": [
            "what is my goal",
            "what do i want to become"
        ],

        "favourite colour": [
            "what is my favourite colour",
            "what is my favourite color",
            "what's my favourite colour",
            "what's my favourite color"
        ]
    }

    for fact, keys in questions.items():

        if t in keys:

            value = get_memory(fact)

            if value:
                return value

            return "I don't know that yet."

    return None


# =========================================================
# PROBLEM MEMORY
# =========================================================

def get_topic(question):

    q = question.lower()

    if any(
        x in q
        for x in ["x^2", "x**2", "quadratic"]
    ):
        return "quadratic"

    if any(
        x in q
        for x in ["log", "ln"]
    ):
        return "logarithm"

    if any(
        x in q
        for x in ["sin", "cos", "tan"]
    ):
        return "trigonometry"

    if "sqrt" in q:
        return "root"

    if any(
        x in q
        for x in ["x^3", "x**3"]
    ):
        return "cubic"

    return "general"


def save_problem(
    question,
    solution,
    correct,
    mistake=""
):

    conn = get_connection()
    cur = conn.cursor()

    topic = get_topic(question)

    cur.execute("""
    INSERT INTO problem_memory_v2
    (question, topic, solution, correct, mistake)
    VALUES (?, ?, ?, ?, ?)
    """, (
        question,
        topic,
        str(solution),
        correct,
        mistake
    ))

    conn.commit()
    conn.close()


def get_relevant_mistakes(question):

    conn = get_connection()
    cur = conn.cursor()

    topic = get_topic(question)

    cur.execute("""
    SELECT question, mistake
    FROM problem_memory_v2
    WHERE topic=?
    AND correct=0
    ORDER BY id DESC
    LIMIT 3
    """, (topic,))

    result = cur.fetchall()

    conn.close()

    return result


# =========================================================
# MATHEMATICS
# =========================================================

x, y, z = sp.symbols("x y z")


transformations = (
    standard_transformations
    + (
        convert_xor,
        implicit_multiplication_application
    )
)


symbols = {

    "x": x,
    "y": y,
    "z": z,

    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,

    "log": sp.log,
    "ln": sp.log,

    "sqrt": sp.sqrt
}


def format_value(value):

    value = sp.simplify(value)

    # Fraction
    if isinstance(
        value,
        sp.Rational
    ):

        if value.q != 1:

            return str(
                value
            )

    # Square root / complex etc.
    return sp.sstr(value)


def format_answer(answer):

    if isinstance(answer, list):

        if len(answer) == 0:
            return "No solution found."

        lines = []

        for value in answer:

            lines.append(
                "x = "
                + format_value(value)
            )

        return "\n".join(lines)

    return format_value(answer)


def maths(text):

    text = text.strip()

    # Check if input looks mathematical
    if not re.search(
        r"[0-9x-zX-Z]"
        r"|\^"
        r"|="
        r"|sin"
        r"|cos"
        r"|tan"
        r"|log"
        r"|ln"
        r"|sqrt",
        text,
        re.IGNORECASE
    ):

        return None

    try:

        # Convert ^ into **
        text = text.replace(
            "^",
            "**"
        )

        # -------------------------
        # EQUATION
        # -------------------------

        if "=" in text:

            left, right = text.split(
                "=",
                1
            )

            left = parse_expr(
                left,
                transformations=transformations,
                local_dict=symbols
            )

            right = parse_expr(
                right,
                transformations=transformations,
                local_dict=symbols
            )

            equation = sp.Eq(
                left,
                right
            )

        # -------------------------
        # EXPRESSION
        # -------------------------

        else:

            expression = parse_expr(
                text,
                transformations=transformations,
                local_dict=symbols
            )

            variables = list(
                expression.free_symbols
            )

            # If it is simply an arithmetic expression
            if not variables:

                return sp.simplify(
                    expression
                )

            equation = sp.Eq(
                expression,
                0
            )

        variables = list(
            equation.free_symbols
        )

        if not variables:

            return sp.simplify(
                equation.lhs - equation.rhs
            )

        result = sp.solve(
            equation,
            variables[0]
        )

        return result

    except Exception as e:

        print(
            "Math error:",
            e
        )

        return None


# =========================================================
# NORMAL AI
# =========================================================

def normal_ai(message):

    try:

        response = ollama.chat(

            model="qwen3:0.6b",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are Chitragupt, "
                    "a helpful personal AI assistant. "
                    "Answer clearly and directly. "
                    "Do not invent personal facts."
                },

                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        return response[
            "message"
        ][
            "content"
        ]

    except Exception as e:

        print(
            "Ollama error:",
            e
        )

        return (
            "Ollama is not running "
            "or the model is unavailable."
        )


# =========================================================
# MAIN CHAT PROCESSOR
# =========================================================

def process_message(msg):

    msg = msg.strip()

    if not msg:

        return ""


    # =====================================================
    # REMEMBER
    # =====================================================

    fact, value = remember(msg)

    if fact:

        return (
            "Okay, I'll remember that."
        )


    # =====================================================
    # RECALL
    # =====================================================

    value = recall(msg)

    if value:

        return value


    # =====================================================
    # MATHS
    # =====================================================

    answer = maths(msg)

    if answer is not None:

        readable_answer = format_answer(
            answer
        )

        # Check previous mistakes
        old_mistakes = (
            get_relevant_mistakes(msg)
        )

        reply = (
            "Answer:\n"
            + readable_answer
        )

        if old_mistakes:

            reply += (
                "\n\n"
                "Relevant previous mistakes:\n"
            )

            for question, mistake in old_mistakes:

                reply += (
                    f"- {question}"
                    f" → {mistake}\n"
                )

        # Save current solution
        save_problem(
            msg,
            readable_answer,
            1
        )

        return reply


    # =====================================================
    # NORMAL AI
    # =====================================================

    return normal_ai(msg)
