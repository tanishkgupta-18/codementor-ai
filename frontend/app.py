import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("CodeMentor AI")

# ---- Fetch Problem ----
slug = st.text_input("Enter LeetCode problem slug (e.g. two-sum)")

if st.button("Fetch Problem"):
    res = requests.get(
        "http://127.0.0.1:8000/fetch-problem",
        params={"slug": slug},
    )
    st.session_state.problem = res.json()

# ---- Show Problem if available ----
if "problem" in st.session_state:
    data = st.session_state.problem

    soup = BeautifulSoup(data["description"], "html.parser")
    clean_text = soup.get_text()

    st.subheader(data["title"])
    st.write(clean_text)
    st.write("Topics:", data["topics"])

    # ---- Code Review ----
    code = st.text_area("Paste your solution code here")

    if st.button("Review Code"):
        payload = {
            "title": data["title"],
            "description": clean_text,
            "code": code,
            "topics": data["topics"]
        }


        res = requests.post(
            "http://127.0.0.1:8000/review-code",
            json=payload
        )
        st.write(res.json()["review"])
