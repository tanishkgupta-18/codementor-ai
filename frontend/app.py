import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import time

API = "http://backend:8000"

st.set_page_config(page_title="CodeMentor AI", layout="wide")
st.title("CodeMentor AI")
st.caption("AI-powered DSA learning with mistakes, decay & spaced repetition")

# ---------------- SESSION ----------------
for k, v in {
    "token": None,
    "last_review": None,
    "review_loading": False,
    "problem": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------- HELPERS ----------------
def safe_get(url, headers):
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []


def parse_review(text):
    def part(a, b=None):
        if a in text:
            x = text.split(a)[1]
            if b and b in x:
                x = x.split(b)[0]
            return x.strip()
        return ""
    return (
        part("MISTAKE:", "PATTERN:"),
        part("PATTERN:", "COMPLEXITY:"),
        part("COMPLEXITY:", "REMINDER:"),
        part("REMINDER:", "CORRECTED CODE:"),
        part("CORRECTED CODE:")
    )


# ---------------- AUTH ----------------
if st.session_state.token:
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()
else:
    st.subheader("Welcome to CodeMentor AI")
    
    with st.form("auth_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        c1, c2 = st.columns(2)
        submit_login = c1.form_submit_button("Login", use_container_width=True)
        submit_reg = c2.form_submit_button("Register", use_container_width=True)

    if submit_login:
        res = requests.post(f"{API}/login", json={"email": email, "password": password}).json()
        if "token" in res:
            st.session_state.token = res["token"]
            st.rerun()
        else:
            st.error(res.get("detail", "Invalid credentials"))

    if submit_reg:
        res = requests.post(f"{API}/register", json={"email": email, "password": password})
        if res.status_code == 200:
            st.success("Account created! You can now login.")
        else:
            st.error(res.json().get("detail", "Registration failed"))

    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}


# ---------------- REVIEW DISPLAY ----------------
if st.session_state.review_loading:
    st.info("Analyzing your code...")

if st.session_state.last_review:
    with st.container(border=True):
        st.subheader("AI Mentor Review")
        
        if "MISTAKE:" not in st.session_state.last_review:
            st.success(st.session_state.last_review)
        else:
            m, p, c, r, raw_code = parse_review(st.session_state.last_review)
            
            clean_code = raw_code.strip()
            if clean_code.startswith("```"):
            
                lines = clean_code.splitlines()
                if len(lines) > 2:
                    clean_code = "\n".join(lines[1:-1])
                else:
                    clean_code = clean_code.replace("```", "")
            
            st.markdown(f"**MISTAKE**\n\n{m}")
            st.markdown(f"**PATTERN**\n\n{p}")
            st.markdown(f"**COMPLEXITY**\n\n{c}")
            st.markdown(f"**REMINDER**\n\n{r}")
            
            st.write("**CORRECTED CODE**")
            st.code(clean_code, language=None)


# ---------------- DASHBOARD ----------------
st.divider()
st.header("Your Learning Dashboard")

rev = safe_get(f"{API}/revision-today", headers)
redo = safe_get(f"{API}/redo-list", headers)
flash = safe_get(f"{API}/flashcards", headers)
heat = safe_get(f"{API}/heatmap", headers)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revisions Due", len(rev))
c2.metric("Redo Problems", len(redo))
c3.metric("Flashcards", len(flash))
least = max(heat, key=lambda x: x["days_since_practice"])["topic"] if heat else "-"
c4.metric("Least Revised Topic", least)


# ---------------- FETCH PROBLEM ----------------
st.divider()
slug = st.text_input("LeetCode slug (e.g. two-sum)")
if st.button("Fetch Problem"):
    st.session_state.problem = requests.get(
        f"{API}/fetch-problem", params={"slug": slug}
    ).json()


# ---------------- LAYOUT ----------------
left, right = st.columns([2, 1])

# ===== LEFT =====
with left:
    if st.session_state.problem:
        p = st.session_state.problem
        soup = BeautifulSoup(p["description"], "html.parser")
        clean = soup.get_text()

        st.subheader(p["title"])
        st.caption(", ".join(p["topics"]))
        st.link_button(
            "Open on LeetCode",
            f"https://leetcode.com/problems/{slug}/",
            width="stretch"
        )
        st.write(clean)

        code = st.text_area("Paste your code", height=220)

        if st.button("Review Code"):
            st.session_state.review_loading = True
            st.rerun()

        if st.session_state.review_loading:
            payload = {
                "title": p["title"],
                "description": clean,
                "code": code,
                "topics": p["topics"]
            }

            rid = requests.post(
                f"{API}/review_code",
                json=payload,
                headers=headers
            ).json()["review_id"]

            while True:
                status = requests.get(
                    f"{API}/review_status/{rid}"
                ).json()

                if status["status"] == "DONE":
                    st.session_state.last_review = status["result"]
                    st.session_state.review_loading = False
                    st.rerun()

                time.sleep(1)

# ===== RIGHT =====
with right:
    st.subheader("Revision Due Today")
    for item in rev:
        with st.container(border=True):
            st.write(f"**{item['pattern']}**")
            
            raw_date = item.get('next_revision', "")
            if raw_date:
                clean_date = pd.to_datetime(raw_date).strftime("%b %d, %I:%M %p")
            else:
                clean_date = "Pending"
                
            st.caption(f"Level {item['level']} • {clean_date}")

    # ---- Redo ----
    st.divider()
    st.subheader("Redo Problems")
    for r in redo:
        with st.container(border=True):
            st.write(f"**{r['title']}**")
            st.caption(r["pattern"])
            st.write(r["mistake"])
            st.link_button(
                "Open LeetCode",
                f"https://leetcode.com/problems/{r['slug']}/",
                width="stretch"
            )
            if st.button("Remove", key=r["slug"], width="stretch"):
                requests.delete(f"{API}/redo-list/{r['slug']}", headers=headers)
                st.rerun()

    # ---- Flashcards ----
    st.divider()
    st.subheader("Today’s Flashcards")
    for c in flash[:5]:
        with st.container(border=True):
            st.caption(f"{c['pattern']} • {c['count']} times")
            st.write("Mistake:", c["mistake"])
            st.write("Reminder:", c["reminder"])

    # ---- Graph ----
    st.divider()
    st.subheader("Mistake Frequency")
    mh = safe_get(f"{API}/mistake-history", headers)
    if mh:
        df = pd.DataFrame(mh)
        fig = px.bar(df, x="pattern", y="count")
        st.plotly_chart(fig, width="stretch")

    # ---- Table ----
    st.divider()
    st.subheader("Weak Patterns")
    stats = safe_get(f"{API}/pattern-stats", headers)
    if stats:
        df_stats = pd.DataFrame(stats)
        if "last_date" in df_stats.columns:
            df_stats["last_date"] = pd.to_datetime(df_stats["last_date"]).dt.date
        st.dataframe(df_stats[["pattern", "count", "last_date", "status"]], width="stretch")
