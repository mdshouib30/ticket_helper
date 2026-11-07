import json
import os

import pandas as pd
import streamlit as st

from src import knowledge
from src.classifier import Category, TicketResult, Urgency, classify_ticket
from src.replier import FAQ_THRESHOLD, reply_source, write_reply
from src.rules import apply_rules
from src.safety import decide_action

st.set_page_config(page_title="Support Ticket Helper", page_icon="🎫", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(120, 120, 200, 0.08);
        border: 1px solid rgba(120, 120, 200, 0.25);
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

URGENCY_ICON = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
ACTION_ICON = {"SEND TO HUMAN": "🧑 Human check", "AUTO-REPLY": "✅ Auto-reply"}

if not os.path.exists("output/results.json"):
    st.warning("No results yet. Run this first: uv run main.py")
    st.stop()

with open("output/results.json") as f:
    results = json.load(f)

# ---------- Sidebar ----------
st.sidebar.title("🎫 Ticket Helper")
st.sidebar.caption("Rules first, AI second, a human for risky tickets.")
urgency_filter = st.sidebar.multiselect(
    "Show urgency",
    ["high", "medium", "low"],
    default=["high", "medium", "low"],
)
action_filter = st.sidebar.multiselect(
    "Show action",
    ["SEND TO HUMAN", "AUTO-REPLY"],
    default=["SEND TO HUMAN", "AUTO-REPLY"],
)
st.sidebar.divider()
st.sidebar.markdown(
    "**How it works**\n\n"
    "1. Simple rules\n"
    "2. AI sorts the ticket\n"
    "3. FAQ search finds a fact\n"
    "4. Reply uses only that fact\n"
    "5. Safety check"
)

# ---------- Header and number cards ----------
st.title("🎫 AI Support Ticket Helper")
st.caption("Sorts customer tickets, drafts replies, and sends risky ones to a human.")

total = len(results)
by_rules = sum(1 for r in results if r["sorted_by"] == "RULES")
to_human = sum(1 for r in results if r["action"] == "SEND TO HUMAN")
high = sum(1 for r in results if r["urgency"] == "high")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total tickets", total)
c2.metric("Sorted without AI", by_rules)
c3.metric("Sent to a human", to_human)
c4.metric("High urgency", high)

shown = [
    r
    for r in results
    if r["urgency"] in urgency_filter and r["action"] in action_filter
]

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Tickets", "📊 Charts", "📚 FAQ", "⚡ Try a new ticket"]
)

# ---------- Tab 1: tickets ----------
with tab1:
    if not shown:
        st.info("No tickets match the filters in the sidebar.")
    else:
        table = [
            {
                "ID": r["id"],
                "Message": r["message"],
                "Category": r["category"],
                "Urgency": URGENCY_ICON[r["urgency"]],
                "Action": ACTION_ICON[r["action"]],
            }
            for r in shown
        ]
        st.dataframe(table, hide_index=True)

        st.subheader("Ticket details")
        chosen = st.selectbox("Pick a ticket", [r["id"] for r in shown])
        ticket = next(r for r in shown if r["id"] == chosen)

        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown("**Customer message**")
                st.write(ticket["message"])
                st.markdown("**Sorted by**")
                st.write(ticket["sorted_by"])
                st.markdown("**Why this category**")
                st.write(ticket["reason"])
        with right:
            with st.container(border=True):
                st.markdown("**Reply draft**")
                st.write(ticket["reply"])
                try:
                    source_result = TicketResult(
                        category=Category(ticket["category"]),
                        urgency=Urgency(ticket["urgency"]),
                        reason=ticket["reason"],
                    )
                    source, score = reply_source(ticket["message"], source_result)
                    st.caption(f"Reply source: {source}")
                except Exception:
                    st.caption("Reply source: unavailable (is Ollama running?)")
            if ticket["action"] == "SEND TO HUMAN":
                st.warning(f"Send to a human: {ticket['why']}")
            else:
                st.success(f"Auto-reply: {ticket['why']}")

# ---------- Tab 2: charts ----------
with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Tickets by category")
        st.bar_chart(pd.Series([r["category"] for r in results]).value_counts())
    with col_b:
        st.subheader("Tickets by urgency")
        st.bar_chart(pd.Series([r["urgency"] for r in results]).value_counts())

# ---------- Tab 3: FAQ ----------
with tab3:
    st.write(
        "The FAQ is the notebook of true facts. The reply writer may only "
        "use facts from here."
    )

    if st.session_state.pop("faq_added", False):
        st.success("FAQ added. The search now uses it.")

    st.subheader(f"FAQ notebook ({len(knowledge.FAQ)} entries)")
    st.dataframe(
        [
            {"ID": item["id"], "Question": item["question"], "Answer": item["answer"]}
            for item in knowledge.FAQ
        ],
        hide_index=True,
    )

    st.subheader("Test the FAQ search")
    st.caption("Type a customer message and see which FAQ page the search picks.")
    test_message = st.text_input("Customer message", key="faq_test")
    if test_message.strip():
        try:
            with st.spinner("Searching..."):
                match, score = knowledge.best_faq(test_message)
            st.progress(max(0.0, min(1.0, score)))
            st.write(f"**Best match:** {match['question']}")
            st.write(f"**Score:** {score:.2f} (cut-off: {FAQ_THRESHOLD:.2f})")
            if score >= FAQ_THRESHOLD:
                st.success(
                    f"Good match. The reply will use this fact: {match['answer']}"
                )
            else:
                st.warning(
                    "No good match. The customer gets the fixed "
                    "'a team member will follow up' reply."
                )
        except Exception as exc:
            st.error("Could not search. Is Ollama running? Start it with: ollama serve")
            st.caption(f"Details: {exc}")

    st.subheader("Add a new FAQ")
    with st.form("add_faq", clear_on_submit=True):
        new_question = st.text_input("Question")
        new_answer = st.text_area("Answer")
        submitted = st.form_submit_button("Add to FAQ")

    if submitted:
        if not new_question.strip() or not new_answer.strip():
            st.warning("Please fill in both the question and the answer.")
        else:
            new_id = max([item["id"] for item in knowledge.FAQ], default=0) + 1
            updated = knowledge.FAQ + [
                {
                    "id": new_id,
                    "question": new_question.strip(),
                    "answer": new_answer.strip(),
                }
            ]
            with open("data/faq.json", "w") as f:
                json.dump(updated, f, indent=2)
            knowledge.reload_faq()
            st.session_state["faq_added"] = True
            st.rerun()

# ---------- Tab 4: live box ----------
with tab4:
    st.write("Type a customer message and watch the whole system handle it.")
    new_message = st.text_area(
        "Customer message",
        placeholder="I was charged twice this month!",
    )

    if st.button("Process ticket", type="primary"):
        if not new_message.strip():
            st.warning("Please type a message first.")
        else:
            try:
                with st.spinner("The AI is working. This can take up to a minute."):
                    result = apply_rules(new_message)
                    sorted_by = "RULES" if result is not None else "AI"
                    if result is None:
                        result = classify_ticket(new_message)
                    reply = write_reply(new_message, result)
                    action, why = decide_action(result, reply)

                m1, m2, m3 = st.columns(3)
                m1.metric("Category", result.category.value)
                m2.metric("Urgency", URGENCY_ICON[result.urgency.value])
                m3.metric("Sorted by", sorted_by)
                st.write(f"**Why:** {result.reason}")

                with st.container(border=True):
                    st.markdown("**Reply draft**")
                    st.write(reply)

                if action == "SEND TO HUMAN":
                    st.warning(f"Send to a human: {why}")
                else:
                    st.success(f"Auto-reply: {why}")
            except Exception as exc:
                st.error(
                    "Could not finish. Is Ollama running? Start it with: ollama serve"
                )
                st.caption(f"Details: {exc}")
