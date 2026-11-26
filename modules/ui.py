import json
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from database.db_connection import get_connection
from modules.data import *
from utils.authentication import create_user
from ai.gemini_client import generate_reply
from ai.learning_modes import MODES

AREAS = {
    "Mathematics Recovery": ["Number and operations","Algebra","Geometry","Measurement","Statistics","Probability","Trigonometry","Functions"],
    "Sciences": ["Biology","Chemistry","Physics","Environmental science","Scientific method"],
    "Humanities and Social Sciences": ["History","Geography","Economics","Psychology","Sociology","Civic education"],
    "Philosophy and Critical Thinking": ["Logic","Ethics","Reasoning","Knowledge and evidence","Decision-making"],
    "Languages and Communication": ["English","Kiswahili","Reading comprehension","Writing","Public speaking"],
    "Technology and Digital Skills": ["Computer literacy","Programming","Artificial intelligence","Digital citizenship","Data literacy"],
    "Business and Entrepreneurship": ["Financial literacy","Budgeting","Business ideas","Entrepreneurship","Personal finance"],
    "Practical and Life Skills": ["Agriculture","Leadership","Health awareness","Environment","Collaboration"]
}

def render_app(user):
    role = user["role"]
    pages = ["Dashboard", "AI Learning Companion", "Explore Knowledge", "My Learning Plan", "Practice & Assessment", "Reflection Journal"]
    if role in ("admin","mentor"):
        pages += ["Circles & Blackboard"]
    if role == "admin":
        pages += ["Administration", "Programme Reports"]
    if role == "parent":
        pages = ["Dashboard", "Programme Announcements"]
    page = st.sidebar.radio("Navigate", pages)
    st.sidebar.markdown("---")
    st.sidebar.caption("The result is not your identity.")
    if page == "Dashboard": dashboard(user)
    elif page == "AI Learning Companion": companion(user)
    elif page == "Explore Knowledge": explore(user)
    elif page == "My Learning Plan": learning_plan(user)
    elif page == "Practice & Assessment": assessment_page(user)
    elif page == "Reflection Journal": reflection(user)
    elif page == "Circles & Blackboard": circles(user)
    elif page == "Administration": administration(user)
    elif page == "Programme Reports": reports()
    elif page == "Programme Announcements": announcements()

def dashboard(user):
    st.title(f"Welcome, {user['full_name'].split()[0]} 🌱")
    st.subheader("Recover. Learn. Grow.")
    st.write("Your journey is built one day, one question and one step at a time.")
    if user["role"] == "student":
        p = student_profile(user["id"]) or {}
        c1,c2,c3 = st.columns(3)
        c1.metric("Learning plans", len(plans(user["id"])))
        c2.metric("Assessments", len(assessments(user["id"])))
        c3.metric("Learning areas", len(AREAS))
        with st.container(border=True):
            st.markdown("### Your learning profile")
            st.write("**Interests:**", p.get("interests") or "Add your interests in your profile below.")
            st.write("**Ambitions:**", p.get("ambitions") or "Your ambitions can change as you discover more.")
            st.write("**Learning preference:**", p.get("learning_preferences") or "Not yet provided.")
        with st.expander("Update my learning profile"):
            with st.form("profile_form"):
                age = st.number_input("Age", min_value=10, max_value=100, value=int(p.get("age") or 18))
                location = st.text_input("General area / community (do not enter a home address)", p.get("location") or "")
                grade = st.text_input("KCSE grade (optional)", p.get("kcse_grade") or "")
                interests = st.text_area("What interests you?", p.get("interests") or "")
                ambitions = st.text_area("What would you like to explore or achieve?", p.get("ambitions") or "")
                pref = st.text_area("How do you prefer to learn?", p.get("learning_preferences") or "")
                resp = st.text_area("What responsibilities affect your study time? (optional)", p.get("responsibilities") or "")
                baseline = st.text_area("What do you find easy or difficult in learning?", p.get("baseline_notes") or "")
                if st.form_submit_button("Save profile"):
                    save_profile(user["id"], (age,location,grade,interests,ambitions,pref,resp,baseline))
                    st.success("Your learning profile has been updated.")
                    st.rerun()
    else:
        st.info("Use the navigation to support and monitor the Project 90 programme.")

def companion(user):
    st.title("🤖 AI Learning Companion")
    st.write("Ask questions, explore ideas and learn across appropriate knowledge areas.")
    mode = st.selectbox("Choose your learning mode", list(MODES.keys()))
    p = student_profile(user["id"]) if user["role"] == "student" else {}
    key = f"chat_{user['id']}_{mode}"
    if key not in st.session_state:
        st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("What would you like to learn or explore?")
    if prompt:
        st.session_state[key].append({"role":"user","content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking with you..."):
                try:
                    answer = generate_reply(prompt, mode, p, st.session_state[key][:-1])
                except Exception as exc:
                    answer = "The AI service could not respond. Please check the API configuration or try again later."
                    st.error(f"AI service error: {exc}")
                st.markdown(answer)
        st.session_state[key].append({"role":"assistant","content":answer})
        execute("INSERT INTO chat_messages(user_id,mode,role,content) VALUES(?,?,?,?)",
                (user["id"],mode,"user",prompt))
        execute("INSERT INTO chat_messages(user_id,mode,role,content) VALUES(?,?,?,?)",
                (user["id"],mode,"assistant",answer))
    if st.button("Clear this conversation"):
        st.session_state[key] = []
        st.rerun()

def explore(user):
    st.title("🌍 Explore Knowledge")
    st.write("Curiosity has no single subject. Choose an area or follow a question that interests you.")
    area = st.selectbox("Knowledge area", list(AREAS.keys()))
    topic = st.selectbox("Explore a topic", AREAS[area])
    st.info(f"Selected: **{area} — {topic}**")
    question = st.text_area("What would you like to understand about this topic?")
    if st.button("Explore with my AI companion", type="primary"):
        if question.strip():
            st.session_state.prefill_question = f"Help me explore {topic} in {area}. My question is: {question}"
            st.success("Open AI Learning Companion from the navigation to continue. Select a suitable learning mode and paste your question.")
        else:
            st.warning("Enter a question first.")
    st.markdown("### A few questions to get started")
    prompts = {
        "Mathematics Recovery":"How can I use percentages when running a small business?",
        "Sciences":"How do scientists know that an experiment is reliable?",
        "Humanities and Social Sciences":"How does geography influence where people live?",
        "Philosophy and Critical Thinking":"Can something be legal but still be wrong?",
        "Languages and Communication":"How can I make my writing clearer and more persuasive?",
        "Technology and Digital Skills":"How does artificial intelligence learn patterns?",
        "Business and Entrepreneurship":"How can I test whether a business idea is useful?",
        "Practical and Life Skills":"How can mathematics help a small-scale farmer?"
    }
    st.write("Try asking:", prompts[area])

def learning_plan(user):
    st.title("🗓️ My Learning Plan")
    today = date.today()
    selected = st.date_input("Plan date", value=today)
    with st.form("add_plan"):
        st.subheader("Add a learning activity")
        subject = st.selectbox("Learning area", list(AREAS.keys()))
        activity = st.text_area("What will you work on?")
        duration = st.number_input("Estimated time (minutes)", min_value=5, max_value=240, value=30, step=5)
        submitted = st.form_submit_button("Add to my plan")
    if submitted and activity.strip():
        create_plan(user["id"], selected.isoformat(), subject, activity.strip(), int(duration))
        st.success("Activity added.")
    rows = plans(user["id"], selected.isoformat())
    if rows:
        st.subheader("Your activities")
        for row in rows:
            cols = st.columns([0.08,0.72,0.20])
            done = cols[0].checkbox(" ", value=bool(row["completed"]), key=f"plan_{row['id']}")
            cols[1].markdown(f"**{row['subject']}**  \n{row['activity']} · {row['duration_minutes']} min")
            cols[2].caption("Completed" if done else "In progress")
            if int(done) != int(row["completed"]):
                execute("UPDATE learning_plans SET completed=? WHERE id=?", (int(done),row["id"]))
    else:
        st.info("Your plan is empty for this date. Add one manageable activity to get started.")

def assessment_page(user):
    st.title("📝 Practice & Assessment")
    st.write("Practice is for learning. Mistakes help us see what to work on next.")
    topic = st.selectbox("Assessment area", ["Mathematics","Science","English","Digital skills","General knowledge"])
    question_sets = {
        "Mathematics":[("What is 15% of 200?",["15","20","30","45"],2),
                       ("Solve: 3x = 21",["5","6","7","8"],2),
                       ("What is the mean of 2, 4 and 6?",["3","4","5","6"],1)],
        "Science":[("Which gas do plants absorb during photosynthesis?",["Oxygen","Carbon dioxide","Nitrogen","Hydrogen"],1),
                   ("What is the SI unit of force?",["Joule","Watt","Newton","Pascal"],2),
                   ("Which organ pumps blood?",["Lungs","Brain","Heart","Kidney"],2)],
        "English":[("Which word is a noun?",["Quickly","Happiness","Run","Blue"],1),
                   ("Choose the correct spelling.",["Recieve","Receive","Receeve","Receve"],1),
                   ("A synonym for 'brief' is:",["Short","Late","Wide","Heavy"],0)],
        "Digital skills":[("What does CPU stand for?",["Central Processing Unit","Computer Personal Utility","Control Program Unit","Central Power User"],0),
                          ("Which is a strong password practice?",["Use your name","Reuse one password","Use a long unique password","Share with friends"],2),
                          ("Which is a web browser?",["Excel","Chrome","PowerPoint","Calculator"],1)],
        "General knowledge":[("Which planet is known as the Red Planet?",["Venus","Mars","Jupiter","Mercury"],1),
                             ("How many sides does a hexagon have?",["5","6","7","8"],1),
                             ("Which ocean is the largest?",["Atlantic","Indian","Arctic","Pacific"],3)]
    }
    qs = question_sets[topic]
    with st.form(f"quiz_{topic}"):
        answers = []
        for i,(q,opts,correct) in enumerate(qs):
            answers.append(st.radio(f"{i+1}. {q}",opts,key=f"{topic}_{i}"))
        submitted = st.form_submit_button("Submit answers")
    if submitted:
        score = sum(1 for ans,(_,opts,correct) in zip(answers,qs) if opts.index(ans)==correct)
        st.metric("Your result",f"{score}/{len(qs)}",f"{score/len(qs)*100:.0f}%")
        st.write("Review the correct answers:")
        for i,(q,opts,correct) in enumerate(qs):
            st.write(f"{i+1}. {opts[correct]}")
        add_assessment(user["id"],topic,score,len(qs),json.dumps(answers))
        st.success("Your practice result has been saved.")

def reflection(user):
    st.title("🌱 Reflection Journal")
    st.write("Take a moment to notice your progress. You do not need to have everything figured out.")
    with st.form("reflection"):
        learned = st.text_area("What did I learn today?")
        difficult = st.text_area("What challenged me, and what did I do?")
        next_step = st.text_area("What is one small step I will take next?")
        mood = st.select_slider("How are you feeling about learning today?", options=["Very low","Low","Okay","Good","Very good"])
        submitted = st.form_submit_button("Save reflection")
    if submitted:
        save_reflection(user["id"],date.today().isoformat(),learned,difficult,next_step,mood)
        st.success("Your reflection has been saved. Returning after a difficult day is progress too.")
    history = all_rows("SELECT reflection_date,learned,difficult,next_step,mood FROM reflections WHERE user_id=? ORDER BY id DESC LIMIT 10",(user["id"],))
    if history:
        st.subheader("Recent reflections")
        for r in history:
            with st.expander(f"{r['reflection_date']} · Feeling: {r['mood']}"):
                st.write("**Learned:**",r["learned"])
                st.write("**Challenge:**",r["difficult"])
                st.write("**Next step:**",r["next_step"])

def circles(user):
    st.title("🤝 Circles & Blackboard")
    st.write("The pilot has five Circles of three students. The weekly host rotates so everyone teaches and learns.")
    if user["role"] == "admin":
        with st.expander("Create a Circle"):
            with st.form("create_circle"):
                name=st.text_input("Circle name",placeholder="Circle 1")
                area=st.text_input("General meeting area")
                day=st.selectbox("Usual meeting day",["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
                if st.form_submit_button("Create Circle") and name.strip():
                    try:
                        execute("INSERT INTO circles(name,meeting_area,meeting_day) VALUES(?,?,?)",(name,area,day))
                        st.success("Circle created.")
                    except Exception:
                        st.error("That Circle name already exists.")
        students = all_rows("SELECT id,full_name,username FROM users WHERE role='student' AND active=1 ORDER BY full_name")
        circles_list = all_rows("SELECT * FROM circles WHERE active=1")
        if circles_list and students:
            with st.expander("Add a student to a Circle"):
                with st.form("assign_circle"):
                    c = st.selectbox("Circle",circles_list,format_func=lambda x:x["name"])
                    s = st.selectbox("Student",students,format_func=lambda x:x["full_name"])
                    if st.form_submit_button("Assign"):
                        try:
                            execute("INSERT INTO circle_members(circle_id,user_id) VALUES(?,?)",(c["id"],s["id"]))
                            st.success("Student assigned.")
                        except Exception:
                            st.error("Student is already in this Circle.")
    circle_rows = all_rows("""SELECT c.*,COUNT(cm.user_id) AS members FROM circles c
                              LEFT JOIN circle_members cm ON cm.circle_id=c.id
                              WHERE c.active=1 GROUP BY c.id ORDER BY c.id""")
    for c in circle_rows:
        members=all_rows("""SELECT u.id,u.full_name FROM circle_members cm JOIN users u ON u.id=cm.user_id
                             WHERE cm.circle_id=? ORDER BY u.full_name""",(c["id"],))
        with st.container(border=True):
            st.subheader(c["name"])
            st.caption(f"{c.get('meeting_area') or 'Meeting area not set'} · {c.get('meeting_day') or 'Day not set'} · {c['members']} members")
            st.write(", ".join(m["full_name"] for m in members) or "No students assigned.")
            meetings=all_rows("""SELECT m.*,u.full_name AS host FROM circle_meetings m LEFT JOIN users u ON u.id=m.host_user_id
                                 WHERE m.circle_id=? ORDER BY m.meeting_date DESC LIMIT 5""",(c["id"],))
            if meetings:
                for m in meetings:
                    st.caption(f"{m['meeting_date']} · Host: {m['host'] or 'Not assigned'} · {m['topic'] or 'Topic not recorded'}")
            if user["role"]=="admin":
                with st.expander(f"Record meeting for {c['name']}"):
                    with st.form(f"meeting_{c['id']}"):
                        mdate=st.date_input("Meeting date",key=f"md_{c['id']}")
                        host_options=[{"id":None,"full_name":"Not assigned"}]+members
                        host=st.selectbox("Teacher for the Week / host",host_options,format_func=lambda x:x["full_name"],key=f"host_{c['id']}")
                        topic=st.text_input("Topic or challenge",key=f"topic_{c['id']}")
                        notes=st.text_area("Meeting notes (avoid sensitive personal details)",key=f"notes_{c['id']}")
                        if st.form_submit_button("Save meeting"):
                            execute("INSERT INTO circle_meetings(circle_id,meeting_date,host_user_id,topic,notes) VALUES(?,?,?,?,?)",
                                    (c["id"],mdate.isoformat(),host["id"],topic,notes))
                            st.success("Meeting recorded.")
    st.info("The current Blackboard area supports Circle meeting records and topics. A live shared whiteboard is a separate development item.")

def administration(user):
    st.title("⚙️ Programme Administration")
    st.subheader("Create a staff or programme account")
    st.caption("Students create their own accounts from the sign-in screen. Use this section for mentor, parent or administrator accounts.")
    with st.form("create_user"):
        name=st.text_input("Full name")
        username=st.text_input("Username")
        role=st.selectbox("Role",["mentor","parent","admin"])
        password=st.text_input("Temporary password (minimum 10 characters)",type="password")
        if st.form_submit_button("Create account"):
            try:
                uid=create_user(name,username,password,role)
                st.success(f"Account created. User ID: {uid}")
            except Exception as e:
                st.error(str(e))
    st.subheader("Current users")
    users=all_rows("SELECT id,full_name,username,role,active,created_at FROM users ORDER BY created_at DESC")
    if users:
        st.dataframe(pd.DataFrame(users),use_container_width=True,hide_index=True)
    st.subheader("Create the five pilot Circles")
    if st.button("Create Circle 1–5 if missing"):
        for i in range(1,6):
            try: execute("INSERT INTO circles(name) VALUES(?)",(f"Circle {i}",))
            except Exception: pass
        st.success("Five Circle records are available.")

def reports():
    st.title("📊 Programme Reports")
    users=all_rows("SELECT role,COUNT(*) AS total FROM users WHERE active=1 GROUP BY role")
    scores=assessments()
    plans_count=all_rows("SELECT COUNT(*) AS total FROM learning_plans")
    meetings=all_rows("SELECT COUNT(*) AS total FROM circle_meetings")
    a,b,c,d=st.columns(4)
    a.metric("Active accounts",sum(x["total"] for x in users))
    b.metric("Assessment attempts",len(scores))
    c.metric("Learning activities",plans_count[0]["total"] if plans_count else 0)
    d.metric("Circle meetings",meetings[0]["total"] if meetings else 0)
    if users: st.dataframe(pd.DataFrame(users),use_container_width=True,hide_index=True)
    if scores:
        df=pd.DataFrame(scores)
        df["percentage"]=df["score"]/df["total"]*100
        st.subheader("Assessment performance")
        st.dataframe(df[["full_name","topic","score","total","percentage","created_at"]],use_container_width=True,hide_index=True)
        fig=px.bar(df,x="full_name",y="percentage",color="topic",barmode="group",title="Recorded practice results")
        st.plotly_chart(fig,use_container_width=True)
    st.caption("These are operational pilot indicators, not proof of learning impact. Baseline and endline assessment design should be validated by the programme's academic lead.")

def announcements():
    st.title("📢 Programme Announcements")
    rows=all_rows("""SELECT a.*,u.full_name FROM announcements a LEFT JOIN users u ON u.id=a.created_by
                     ORDER BY a.created_at DESC""")
    if not rows:
        st.info("There are no announcements yet.")
    for r in rows:
        with st.container(border=True):
            st.subheader(r["title"])
            st.write(r["body"])
            st.caption(r["created_at"])
