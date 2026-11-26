import hashlib
import hmac
import os
import re
import streamlit as st
from database.db_connection import get_connection
from utils.settings import get_setting

ROLES = ["student", "mentor", "parent", "admin"]
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(candidate, digest_hex)
    except Exception:
        return False


def validate_username(username):
    username = (username or "").strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3–24 characters and use only letters, numbers, dots, underscores or hyphens.")
    return username


def create_user(full_name, username, password, role, student_code=None, email=None):
    if role not in ROLES:
        raise ValueError("Invalid role.")
    if not (full_name or "").strip():
        raise ValueError("Please enter the student's full name.")
    username = validate_username(username)
    if len(password or "") < 10:
        raise ValueError("Password must contain at least 10 characters.")
    # Email is retained internally for compatibility with existing records.
    # Students do not need to provide or use an email address.
    internal_email = (email or f"{username}@project90.local").strip().lower()
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()
        if exists:
            raise ValueError("That username is already taken. Please choose another.")
        cur = conn.execute(
            """INSERT INTO users(full_name,email,username,password_hash,role)
               VALUES(?,?,?,?,?)""",
            (full_name.strip(), internal_email, username, hash_password(password), role)
        )
        user_id = cur.lastrowid
        if role == "student":
            conn.execute(
                "INSERT INTO student_profiles(user_id,student_code) VALUES(?,?)",
                (user_id, student_code or f"P90-{user_id:04d}")
            )
        conn.commit()
    return user_id


def ensure_initial_admin():
    """Create the configured administrator, or synchronize the existing admin login.

    The configured .env / Streamlit secret credentials are authoritative for the
    bootstrap administrator. Existing student and non-admin records are untouched.
    """
    name = get_setting("PROJECT90_ADMIN_NAME", "Project 90 Administrator")
    email = get_setting("PROJECT90_ADMIN_EMAIL", "admin@example.org")
    password = get_setting("PROJECT90_ADMIN_PASSWORD")
    username = get_setting(
        "PROJECT90_ADMIN_USERNAME",
        (email.split("@", 1)[0] if email else "admin")
    )

    if not password:
        raise RuntimeError(
            "Administrator password is not configured. Add PROJECT90_ADMIN_PASSWORD "
            "to your .env file (or Streamlit secrets) and restart Project 90."
        )
    if len(password) < 10:
        raise RuntimeError("PROJECT90_ADMIN_PASSWORD must contain at least 10 characters.")

    username = validate_username(username)
    with get_connection() as conn:
        admin = conn.execute(
            "SELECT * FROM users WHERE role='admin' ORDER BY id LIMIT 1"
        ).fetchone()

        username_owner = conn.execute(
            "SELECT id, role FROM users WHERE username=? COLLATE NOCASE",
            (username,)
        ).fetchone()
        if username_owner and (admin is None or username_owner["id"] != admin["id"]):
            raise RuntimeError(
                f"The configured administrator username '{username}' is already used "
                f"by another account. Change PROJECT90_ADMIN_USERNAME in .env."
            )

        if admin:
            # Keep the existing administrator account and its ID/data, but make
            # the configured username and password usable for sign-in.
            conn.execute(
                "UPDATE users SET full_name=?, username=?, password_hash=?, active=1 WHERE id=?",
                (name, username, hash_password(password), admin["id"])
            )
        else:
            # Email is an internal legacy-required field; students never use it.
            admin_email = (email or "admin@example.org").strip().lower()
            email_owner = conn.execute(
                "SELECT id FROM users WHERE email=? COLLATE NOCASE", (admin_email,)
            ).fetchone()
            if email_owner:
                admin_email = f"{username}@project90.local"
            conn.execute(
                "INSERT INTO users(full_name,email,username,password_hash,role,active) "
                "VALUES(?,?,?,?, 'admin', 1)",
                (name, admin_email, username, hash_password(password))
            )
        conn.commit()


def register_student(full_name, username, password):
    return create_user(full_name, username, password, "student")


def login_form():
    st.markdown(
        "<div style='text-align:center;padding:2rem 0 1rem'>"
        "<div style='font-size:3rem'>🌱</div><h1>PROJECT 90</h1>"
        "<p>Recover. Learn. Grow.</p><p>KIWIMBI LIBRARY × ATEKER NU TRUST</p></div>",
        unsafe_allow_html=True
    )
    login_tab, register_tab = st.tabs(["Sign in", "Create student account"])

    with login_tab:
        with st.container(border=True):
            st.subheader("Welcome back")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                with get_connection() as conn:
                    row = conn.execute(
                        """SELECT * FROM users
                           WHERE (username=? COLLATE NOCASE OR (role='admin' AND email=? COLLATE NOCASE))
                           AND active=1""",
                        (username.strip(), username.strip().lower())
                    ).fetchone()
                if row and verify_password(password, row["password_hash"]):
                    st.session_state.user = dict(row)
                    st.rerun()
                else:
                    st.error("The username or password is incorrect, or the account is inactive.")

    with register_tab:
        with st.container(border=True):
            st.subheader("Create your Project 90 account")
            st.caption("Choose a username and password. No email address is required.")
            with st.form("student_registration_form"):
                full_name = st.text_input("Full name")
                new_username = st.text_input(
                    "Choose a username",
                    help="Use 3–24 letters, numbers, dots, underscores or hyphens."
                )
                new_password = st.text_input("Create password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                registered = st.form_submit_button("Create student account", use_container_width=True)
            if registered:
                if new_password != confirm_password:
                    st.error("The passwords do not match.")
                else:
                    try:
                        user_id = register_student(full_name, new_username, new_password)
                        st.success(f"Your account has been created. Your Project 90 ID is P90-{user_id:04d}. You can now sign in.")
                    except Exception as exc:
                        st.error(str(exc))


def current_user():
    return st.session_state.get("user")


def logout():
    st.session_state.user = None
    for key in list(st.session_state.keys()):
        if key.startswith("chat_"):
            del st.session_state[key]
