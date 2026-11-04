import json
import os

import streamlit as st

st.set_page_config(page_title="Support Ticket Helper", layout="wide")
st.title("AI Support Ticket Helper")

if not os.path.exists("output/results.json"):
    st.warning("No results yet. Run this first: uv run main.py")
    st.stop()

with open("output/results.json") as f:
    results = json.load(f)

total = len(results)
by_rules = sum(1 for r in results if r["sorted_by"] == "RULES")
to_human = sum(1 for r in results if r["action"] == "SEND TO HUMAN")
high = sum(1 for r in results if r["urgency"] == "high")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total tickets", total)
c2.metric("Sorted without AI", by_rules)
c3.metric("Sent to a human", to_human)
c4.metric("High urgency", high)

st.subheader("All tickets")
table = [
    {
        "ID": r["id"],
        "Message": r["message"],
        "Category": r["category"],
        "Urgency": r["urgency"],
        "Action": r["action"],
    }
    for r in results
]
st.dataframe(table, hide_index=True)

st.subheader("Ticket details")
chosen = st.selectbox("Pick a ticket", [r["id"] for r in results])
ticket = next(r for r in results if r["id"] == chosen)

st.write(f"**Message:** {ticket['message']}")
st.write(f"**Sorted by:** {ticket['sorted_by']}")
st.write(f"**Why this category:** {ticket['reason']}")
st.write(f"**Reply draft:** {ticket['reply']}")

if ticket["action"] == "SEND TO HUMAN":
    st.warning(f"Send to a human: {ticket['why']}")
else:
    st.success(f"Auto-reply: {ticket['why']}")
