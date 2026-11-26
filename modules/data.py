from database.db_connection import get_connection

def one(query, params=()):
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

def all_rows(query, params=()):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]

def execute(query, params=()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.lastrowid

def student_profile(user_id):
    return one("""SELECT u.id,u.full_name,u.email,u.role,p.* FROM users u
                  LEFT JOIN student_profiles p ON p.user_id=u.id WHERE u.id=?""", (user_id,))

def save_profile(user_id, values):
    execute("""UPDATE student_profiles SET age=?,location=?,kcse_grade=?,interests=?,
               ambitions=?,learning_preferences=?,responsibilities=?,baseline_notes=?
               WHERE user_id=?""",
            (*values, user_id))

def create_plan(user_id, date, subject, activity, duration):
    execute("INSERT INTO learning_plans(user_id,plan_date,subject,activity,duration_minutes) VALUES(?,?,?,?,?)",
            (user_id,date,subject,activity,duration))

def plans(user_id, date=None):
    if date:
        return all_rows("SELECT * FROM learning_plans WHERE user_id=? AND plan_date=? ORDER BY id", (user_id,date))
    return all_rows("SELECT * FROM learning_plans WHERE user_id=? ORDER BY plan_date DESC,id DESC", (user_id,))

def save_reflection(user_id, date, learned, difficult, next_step, mood):
    execute("INSERT INTO reflections(user_id,reflection_date,learned,difficult,next_step,mood) VALUES(?,?,?,?,?,?)",
            (user_id,date,learned,difficult,next_step,mood))

def add_assessment(user_id, topic, score, total, answers_json=""):
    execute("INSERT INTO assessments(user_id,topic,score,total,answers_json) VALUES(?,?,?,?,?)",
            (user_id,topic,score,total,answers_json))

def assessments(user_id=None):
    if user_id:
        return all_rows("SELECT * FROM assessments WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return all_rows("""SELECT a.*,u.full_name FROM assessments a JOIN users u ON u.id=a.user_id
                       ORDER BY a.created_at DESC""")
