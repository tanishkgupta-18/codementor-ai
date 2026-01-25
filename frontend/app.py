import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CodeMentor AI", layout="wide")
st.title("CodeMentor AI")

# ---------------- SESSION INIT ----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "last_review" not in st.session_state:
    st.session_state.last_review = None

# ---------------- LOGIN / REGISTER ----------------
if st.session_state.token is None:
    st.subheader("Login / Register")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register"):
            res = requests.post(
                "http://127.0.0.1:8000/register",
                json={"email": email, "password": password}
            )
            st.success(res.json())

    with col2:
        if st.button("Login"):
            res = requests.post(
                "http://127.0.0.1:8000/login",
                json={"email": email, "password": password}
            )
            data = res.json()
            if "token" in data:
                st.session_state.token = data["token"]
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- FETCH PROBLEM ----------------
st.divider()
st.header("Fetch LeetCode Problem")

slug = st.text_input("Enter problem slug (e.g. two-sum)")

if st.button("Fetch Problem"):
    res = requests.get(
        "http://127.0.0.1:8000/fetch-problem",
        params={"slug": slug},
    )
    st.session_state.problem = res.json()

# ---------------- MAIN LAYOUT ----------------
col_left, col_right = st.columns([2, 1])

# ---------------- PROBLEM + REVIEW ----------------
with col_left:
    if "problem" in st.session_state:
        data = st.session_state.problem

        soup = BeautifulSoup(data["description"], "html.parser")
        clean_text = soup.get_text()

        with st.container(border=True):
            st.subheader(data["title"])
            st.caption(f"Topics: {', '.join(data['topics'])}")
            st.write(clean_text)

        code = st.text_area("Paste your solution code here", height=200)

        if st.button("Review Code"):
            payload = {
                "title": data["title"],
                "description": clean_text,
                "code": code,
                "topics": data["topics"]
            }

            headers = {
                "Authorization": f"Bearer {st.session_state.token}"
            }

            res = requests.post(
                "http://127.0.0.1:8000/review-code",
                json=payload,
                headers=headers
            )

            result = res.json()

            if "review" in result:
                st.session_state.last_review = result["review"]
            else:
                st.error(result)

    # -------- Show Review Persistently --------
    if st.session_state.last_review:
        with st.container(border=True):
            st.subheader("AI Mentor Review")
            st.code(st.session_state.last_review, language="markdown")

# ---------------- HEATMAP / GRAPH ----------------
with col_right:
    st.subheader("Topic Forgetting Curve")

    if st.button("Show Graph"):
        headers = {
            "Authorization": f"Bearer {st.session_state.token}"
        }

        res = requests.get(
            "http://127.0.0.1:8000/heatmap",
            headers=headers
        )

        data = res.json()
        df = pd.DataFrame(data)

        fig = px.bar(
            df,
            x="topic",
            y="days_since_practice",
            title="Forgetting Curve by Topic"
        )

        st.plotly_chart(fig, width="stretch")

    st.metric("Logged in", "Yes")
