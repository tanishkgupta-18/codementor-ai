import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
API = "http://127.0.0.1:8000"

st.set_page_config(page_title="CodeMentor AI", layout="wide")
st.title("CodeMentor AI")
st.caption("An AI-powered DSA learning system that tracks your mistakes, decay, and spaced revision automatically.")

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

def parse_review(text: str):
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
        part("CORRECTED CODE:"),
    )

# ---------------- LOGOUT ----------------
if st.session_state.token:
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.rerun()

# ---------------- LOGIN / REGISTER ----------------
if st.session_state.token is None:
    st.subheader("Login / Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    c1, c2 = st.columns(2)
    with c1:
        # UPDATED: width='stretch' replaces use_container_width=True
        if st.button("Register", width="stretch"):
            r = requests.post(f"{API}/register", json={"email": email, "password": password})
            st.success(r.json())
    with c2:
        if st.button("Login", width="stretch"):
            r = requests.post(f"{API}/login", json={"email": email, "password": password})
            data = r.json()
            if "token" in data:
                st.session_state.token = data["token"]
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ---------------- REVIEW ON TOP (FIXED LOGIC) ----------------
if st.session_state.review_loading:
    st.info("Analyzing your code...")

if st.session_state.last_review:
    with st.container(border=True):
        st.subheader("AI Mentor Review")
        
        if "MISTAKE:" not in st.session_state.last_review:
            st.success(st.session_state.last_review)
        else:
            m, p, c, r, code = parse_review(st.session_state.last_review)
            if m: st.markdown(f"**MISTAKE**\n\n{m}")
            if p: st.markdown(f"**PATTERN**\n\n{p}")
            if c: st.markdown(f"**COMPLEXITY**\n\n{c}")
            if r: st.markdown(f"**REMINDER**\n\n{r}")
            if code:
                st.markdown("**CORRECTED CODE**")
                st.code(code, language='python')

# ---------------- DASHBOARD ----------------
st.divider()
st.header("Your Learning Dashboard")

rev_res = safe_get(f"{API}/revision-today", headers)
redo_res = safe_get(f"{API}/redo-list", headers)
flash_res = safe_get(f"{API}/flashcards", headers)
heat_res = safe_get(f"{API}/heatmap", headers)

least_topic = "-"
if heat_res:
    weakest = max(heat_res, key=lambda x: x["days_since_practice"])
    least_topic = weakest["topic"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revisions Due", len(rev_res))
c2.metric("Redo Problems", len(redo_res))
c3.metric("Flashcards", len(flash_res))
c4.metric("Least Revised Topic", least_topic)

# ---------------- FETCH PROBLEM ----------------
st.divider()
st.header("Fetch LeetCode Problem")
slug = st.text_input("Problem slug (e.g. two-sum)")

if st.button("Fetch Problem"):
    r = requests.get(f"{API}/fetch-problem", params={"slug": slug})
    st.session_state.problem = r.json()

# ---------------- MAIN LAYOUT ----------------
left, right = st.columns([2, 1])

with left:
    if st.session_state.problem:
        p = st.session_state.problem
        soup = BeautifulSoup(p["description"], "html.parser")
        clean = soup.get_text()
        lc_url = f"https://leetcode.com/problems/{slug}/"

        with st.container(border=True):
            st.subheader(p["title"])
            st.caption(", ".join(p["topics"]))
            # UPDATED: width='stretch'
            st.link_button("Open on LeetCode", lc_url, width="stretch")
            st.write(clean)

        code = st.text_area("Paste your solution", height=300)

        if st.button("Review Code", type="primary"):
            st.session_state.review_loading = True
            st.session_state.last_review = None
            payload = {"title": p["title"], "description": clean, "code": code, "topics": p["topics"]}

            with st.spinner("Analyzing your code..."):
                r = requests.post(f"{API}/review-code", json=payload, headers=headers)
                data = r.json()

            st.session_state.last_review = data.get("review", "Your solution is already optimal.")
            st.session_state.review_loading = False
            st.rerun()

with right:
    # --- Revision Section ---
    st.subheader("Revision Due Today")
    if not rev_res:
        st.success("No revisions due today")
    else:
        for item in rev_res:
            with st.container(border=True):
                st.write(item["pattern"])
                st.caption(f"Level {item['level']} • Next {item['next_revision']}")

    # --- Topic Health ---
    st.divider()
    st.subheader("Topic Health")
    if not heat_res:
        st.caption("No topic data yet.")
    else:
        for h in heat_res:
            color = {"Fresh": "#2ecc71", "Revise Soon": "#f39c12", "Forgotten": "#e74c3c"}.get(h["status"], "#bdc3c7")
            with st.container(border=True):
                c1_h, c2_h = st.columns([3, 1])
                with c1_h:
                    st.write(h["topic"])
                    st.caption(f"{h['days_since_practice']} days ago")
                with c2_h:
                    st.markdown(f'<div style="background:{color};padding:5px;border-radius:5px;text-align:center;color:white;font-size:12px;">{h["status"]}</div>', unsafe_allow_html=True)

    # --- Redo Problems ---
    st.divider()
    st.subheader("Redo Problems")
    for rd in redo_res:
        with st.container(border=True):
            st.write(rd["title"])
            # UPDATED: width='stretch'
            st.link_button("Try Again", f"https://leetcode.com/problems/{rd['slug']}/", width="stretch")

    # --- Mistake History (Chart) ---
    st.divider()
    st.subheader("Mistake Patterns")
    mh = safe_get(f"{API}/mistake-history", headers)
    if mh:
        df_mh = pd.DataFrame(mh)
        fig = px.bar(df_mh, x="pattern", y="count")
        # UPDATED: width='stretch' replaces use_container_width=True
        st.plotly_chart(fig, width="stretch")

    # --- Weak Patterns (Dataframe) ---
    st.divider()
    st.subheader("Weak Patterns")
    stats = safe_get(f"{API}/pattern-stats", headers)
    if stats:
        df_s = pd.DataFrame(stats)
        # UPDATED: width='stretch'
        st.dataframe(df_s[["pattern", "count", "status"]], width="stretch")