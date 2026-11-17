import json
import os
import urllib.request

import pandas as pd
import streamlit as st

from src import database, knowledge
from src.pipeline import process_ticket
from src.replier import FAQ_THRESHOLD

st.set_page_config(page_title="Support Ticket Helper", page_icon="🎫", layout="wide")
database.init_db()

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

CATEGORY_LABEL = {
    "billing": "💳 Billing",
    "technical": "🛠️ Technical problem",
    "refund": "↩️ Refund or return",
    "general": "💬 General question",
}
URGENCY_LABEL = {"high": "🔴 Urgent", "medium": "🟡 Medium", "low": "🟢 Not urgent"}
ACTION_LABEL = {
    "SEND TO HUMAN": "🧑 Needs a person",
    "AUTO-REPLY": "✅ Safe to send",
}
HANDLED_LABEL = {"RULES": "A simple rule (no AI)", "AI": "The AI"}

EXAMPLES = [
    "Do you deliver abroad?",
    "I was charged twice this month!",
    "Please unsubscribe me from your emails.",
    "Do you sell gift cards?",
]


def ai_is_running() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def use_example(text: str):
    st.session_state["ticket_text"] = text


def load_samples():
    with open("output/results.json") as f:
        samples = json.load(f)
    for sample in samples:
        data = dict(sample)
        data.setdefault("reply_source", "Sample ticket")
        database.save_ticket(data)


def show_result(data: dict):
    if data["action"] == "SEND TO HUMAN":
        st.warning(
            f"**Next step: a team member should check this ticket.**\n\n{data['why']}"
        )
    else:
        st.success("**Next step: this reply is safe to send automatically.**")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Type of problem**\n\n{CATEGORY_LABEL[data['category']]}")
    c2.markdown(f"**How urgent**\n\n{URGENCY_LABEL[data['urgency']]}")
    c3.markdown(
        f"**Handled by**\n\n{HANDLED_LABEL.get(data['sorted_by'], data['sorted_by'])}"
    )

    with st.container(border=True):
        st.markdown("**Suggested reply**")
        st.write(data["reply"])
        st.caption(f"Where this reply came from: {data['reply_source']}")
    st.caption(f"Why it was sorted this way: {data['reason']}")


# ---------- Sidebar ----------
st.sidebar.title("🎫 Ticket Helper")
st.sidebar.caption("Sorts customer messages and suggests replies.")
if ai_is_running():
    st.sidebar.success("🟢 The AI is running")
else:
    st.sidebar.error("🔴 The AI is not running")
    st.sidebar.caption("Open a terminal and run: ollama serve")
st.sidebar.divider()
st.sidebar.markdown("**Colors**\n\n🔴 urgent  \n🟡 medium  \n🟢 not urgent")

# ---------- Header ----------
st.title("🎫 Support Ticket Helper")
st.caption(
    "Paste a customer message and get a category, an urgency, and a suggested reply."
)

tab_check, tab_all, tab_faq, tab_help = st.tabs(
    ["✨ Check a ticket", "📋 All tickets", "📚 Help center (FAQ)", "ℹ️ How it works"]
)

# ---------- Tab 1: check a ticket ----------
with tab_check:
    st.subheader("Check a customer message")
    st.write("Type a message from a customer, or click an example.")

    example_cols = st.columns(len(EXAMPLES))
    for col, text in zip(example_cols, EXAMPLES):
        col.button(text, on_click=use_example, args=(text,), key=f"example_{text}")

    message = st.text_area(
        "Customer message",
        key="ticket_text",
        height=110,
        placeholder="Type or paste a customer message here...",
    )

    if st.button("Check this ticket", type="primary"):
        if not message.strip():
            st.warning("Please type a message first.")
        else:
            try:
                with st.spinner("Working on it. This can take up to a minute..."):
                    data = process_ticket(message.strip())
                    data["id"] = database.save_ticket(data)
                st.session_state["last_result"] = data
            except Exception as exc:
                st.session_state.pop("last_result", None)
                st.error(
                    "Something went wrong. Is the AI running? "
                    "Open a terminal and run: ollama serve"
                )
                st.caption(f"Technical details: {exc}")

    if "last_result" in st.session_state:
        st.divider()
        show_result(st.session_state["last_result"])
        st.caption(f"Saved as ticket #{st.session_state['last_result']['id']}")

# ---------- Tab 2: all tickets ----------
with tab_all:
    tickets = database.list_tickets(limit=500)

    if not tickets:
        st.info("No tickets yet. Check one in the first tab.")
        if os.path.exists("output/results.json"):
            if st.button("Load the sample tickets"):
                load_samples()
                st.rerun()
    else:
        df = pd.DataFrame(tickets)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("All tickets", len(df))
        m2.metric("Need a person", int((df["action"] == "SEND TO HUMAN").sum()))
        m3.metric("Handled without AI", int((df["sorted_by"] == "RULES").sum()))
        m4.metric("Urgent", int((df["urgency"] == "high").sum()))

        f1, f2, f3 = st.columns([2, 2, 1])
        search = f1.text_input("Search messages", placeholder="Type a word...")
        urgency_choice = f2.multiselect(
            "Urgency",
            ["high", "medium", "low"],
            default=["high", "medium", "low"],
            format_func=lambda value: URGENCY_LABEL[value],
        )
        only_person = f3.checkbox("Only needs a person")

        view = df[df["urgency"].isin(urgency_choice)]
        if search.strip():
            view = view[
                view["message"].str.contains(
                    search.strip(), case=False, na=False, regex=False
                )
            ]
        if only_person:
            view = view[view["action"] == "SEND TO HUMAN"]

        if view.empty:
            st.info("No tickets match your search or filters.")
        else:
            table = pd.DataFrame(
                {
                    "#": view["id"],
                    "When": view["created_at"],
                    "Message": view["message"],
                    "Type": view["category"].map(CATEGORY_LABEL),
                    "Urgency": view["urgency"].map(URGENCY_LABEL),
                    "Next step": view["action"].map(ACTION_LABEL),
                }
            )
            st.dataframe(table, hide_index=True)
            st.download_button(
                "Download as CSV",
                table.to_csv(index=False).encode("utf-8"),
                "tickets.csv",
                "text/csv",
            )

            st.subheader("Open a ticket")
            chosen = st.selectbox("Pick a ticket number", [int(i) for i in view["id"]])
            data = next(t for t in tickets if t["id"] == chosen)
            st.write(f"**Customer wrote:** {data['message']}")
            show_result(data)

# ---------- Tab 3: FAQ ----------
with tab_faq:
    st.write(
        "This is the notebook of true facts. The reply writer may only use "
        "facts from here."
    )

    if st.session_state.pop("faq_added", False):
        st.success("FAQ added. The search now uses it.")

    st.subheader(f"Help center ({len(knowledge.FAQ)} entries)")
    st.dataframe(
        [
            {"#": item["id"], "Question": item["question"], "Answer": item["answer"]}
            for item in knowledge.FAQ
        ],
        hide_index=True,
    )

    st.subheader("Test the search")
    st.caption("Type a customer message and see which FAQ page the search picks.")
    test_message = st.text_input("Customer message", key="faq_test")
    if test_message.strip():
        try:
            with st.spinner("Searching..."):
                match, score = knowledge.best_faq(test_message)
            st.progress(max(0.0, min(1.0, score)))
            st.write(f"**Best match:** {match['question']}")
            st.write(f"**Score:** {score:.2f} (needs {FAQ_THRESHOLD:.2f} or more)")
            if score >= FAQ_THRESHOLD:
                st.success(
                    f"Good match. The reply will use this fact: {match['answer']}"
                )
            else:
                st.warning(
                    "No good match. The customer gets the standard "
                    "'a team member will follow up' reply."
                )
        except Exception as exc:
            st.error("Could not search. Is the AI running? Run: ollama serve")
            st.caption(f"Technical details: {exc}")

    st.subheader("Add a new FAQ")
    with st.form("add_faq", clear_on_submit=True):
        new_question = st.text_input("Question")
        new_answer = st.text_area("Answer")
        submitted = st.form_submit_button("Add to the help center")

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

# ---------- Tab 4: how it works ----------
with tab_help:
    st.subheader("How it works")
    st.markdown(
        """
        1. **A simple rule** checks the message first. Easy questions like "unsubscribe"
           are answered without any AI.
        2. **The AI** decides the type of problem and how urgent it is.
        3. **The help center** is searched for a true fact. The reply may only use that fact.
        4. **A safety check** decides if the reply can be sent or if a person should look first.
        """
    )

    st.subheader("When does a person check a ticket?")
    st.markdown(
        """
        - The customer is **urgent** (blocked or losing money).
        - The ticket is about **money** (billing or a refund).
        - The reply contains a **number or time** that must be checked.
        - The reply contains a word like **"guarantee"** or **"promise"**.
        """
    )

    st.subheader("Good to know")
    st.markdown(
        """
        - The tickets and the help center facts are **made up** for this demo.
        - The AI runs on this computer, so it costs nothing, but it can be slow.
        - Tickets are saved in a database, so they are still here tomorrow.
        """
    )
