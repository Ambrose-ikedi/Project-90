# PROJECT 90 — Recover. Learn. Grow.

A Python + Streamlit pilot platform for Kiwimbi Library Digital Skills Empowerment Program × Ateker Nu Trust.

It combines:
- Student profiles and baseline learning information
- Gemini-powered AI Learning Companion with Tutor, Discovery, Philosophy, Career, Mentor and Creative modes
- Broad knowledge exploration, with mathematics recovery kept as a structured priority
- Daily learning plans and personal reflections
- Practice quizzes and recorded results
- Five-Circle management and weekly host rotation
- Basic programme administration and reporting

## 1. Requirements

- Python 3.10 or newer
- Internet connection for Gemini features and cloud deployment
- A Google Gemini API key from Google AI Studio
- Streamlit-compatible hosting

## 2. Run locally

Unzip the project folder, open a terminal in `PROJECT_90`, then run:

### Windows

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your Gemini API key and a strong administrator password. The default Gemini model is `gemini-3.8-flash`; you can override it with `GEMINI_MODEL` if your API key does not have access to that model.

```bash
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then:

```bash
streamlit run app.py
```

The application creates `data/project90.db` automatically. The first administrator is created from the environment variables on first startup. If no Gemini key is configured, the application still runs; AI responses will be unavailable until a key is added.

## 3. Streamlit Community Cloud deployment

1. Create a private GitHub repository and upload the project files.
2. Do **not** upload `.env`, `secrets.toml`, or the SQLite database.
3. In Streamlit Community Cloud, create an app pointing to `app.py`.
4. Add these secrets in the app settings:

```toml
GEMINI_API_KEY = "your_real_api_key"
GEMINI_MODEL = "gemini-3.8-flash"
PROJECT90_ADMIN_NAME = "Project 90 Administrator"
PROJECT90_ADMIN_EMAIL = "admin@example.org"
PROJECT90_ADMIN_USERNAME = "admin"
PROJECT90_ADMIN_PASSWORD = "use-a-long-unique-password"
```

5. Deploy.

**Important database hosting note:** Streamlit Community Cloud's local filesystem is not a reliable permanent database for a live programme. This package uses SQLite for a pilot/demo and local testing. Before using it for real student records or multiple concurrent users in production, move the database to managed PostgreSQL (or another persistent database), configure backups, and review privacy, consent, safeguarding and access controls. Do not store sensitive student records in a public repository.

## 4. First login and student self-registration

The administrator account is created or synchronized at startup from the credentials configured in `.env` or Streamlit secrets. The configured `PROJECT90_ADMIN_USERNAME` and `PROJECT90_ADMIN_PASSWORD` are authoritative: if an administrator already exists, its username/password are updated while its account ID and related records are retained. The administrator signs in with the configured username and password.

Students do not need an email address and do not need an administrator to create their accounts. From the sign-in screen, select **Create student account**, enter a full name, choose a unique username and set a password. Usernames must be 3–24 characters and may contain letters, numbers, dots, underscores and hyphens. Passwords must contain at least 10 characters. The system assigns the Student role, creates the student profile and generates a Project 90 ID automatically.

Students sign in using only their chosen username and password. Existing accounts are retained; on first startup after this update, the database adds usernames to existing records using their previous email-name as a starting username. An administrator can view usernames in Programme Administration.

There is no self-service password reset in this pilot. Keep administrator credentials private and arrange a secure password reset process before a wider rollout.

## 5. Roles

- `student`: personal dashboard, AI companion, learning areas, plans, reflections and quizzes.
- `mentor`: student learning and Circle support views.
- `parent`: limited programme overview placeholder; use only after the organisation defines consent and disclosure rules.
- `admin`: programme management, user creation, Circle management and reporting.

Students register themselves. The administrator can create mentor, parent and other administrator accounts in Administration.

## 6. AI use and safeguards

The AI is an educational companion, not a human teacher, therapist, doctor, lawyer or emergency service. It is instructed to teach through explanations and hints, avoid shaming students, encourage help-seeking, and use age-appropriate language. Human oversight remains essential. Review AI-generated content and assessment items before using them in formal instruction.

Gemini requests send the student's prompt and the limited profile context included by the application to Google's API. Review Google's applicable terms and your organisation's privacy requirements before enabling this for minors. Obtain appropriate parent/guardian consent where required.

## 7. Pilot limitations and production work still required

This is a complete runnable pilot foundation, not a certified production student information system. Before a full rollout, commission:
- Persistent managed database and automated backups
- HTTPS, stronger session and account controls, password reset and audit logs
- Formal safeguarding escalation procedures and content moderation review
- Parent/guardian consent and data-retention policy
- Curriculum mapping and expert validation of learning materials
- Reliable offline content synchronisation (not included in this initial version)
- Formal testing, accessibility review and security assessment
- A properly engineered collaborative real-time Blackboard (the current Circle area records meetings and host rotation; it is not a live multi-user whiteboard)

## 8. Folder map

- `app.py`: Streamlit entry point
- `database/`: SQLite schema and database access
- `ai/`: Gemini integration, learning modes and safety instructions
- `modules/`: application screens and programme workflows
- `utils/`: authentication, configuration and helpers
- `assets/`: local CSS and branding placeholder

## 9. Data

The SQLite database is created under `data/`. Keep it backed up and outside source control. Use synthetic data for testing until the organisation has approved its privacy and safeguarding arrangements.
