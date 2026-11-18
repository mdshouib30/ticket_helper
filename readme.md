AI Support Ticket Helper

Tests

An AI system that sorts customer support tickets, drafts replies from a company FAQ, and sends risky tickets to a human. It has a REST API, a database, and a dashboard. It runs on free local models with Ollama, or on a hosted model by changing a few settings.

Live demo

Try it here: https://ticketapper-csmdiiwfhxvcq6shx9r9qy.streamlit.app/

The demo runs in a public mode. Each visitor gets 5 free checks, nothing you type is saved, and editing the FAQ is turned off. It uses a hosted model and a made-up FAQ. The free host puts the app to sleep after 12 hours without visitors, so the first visit may show a "wake up" button and take about a minute to start.

Dashboard

How to use the live demo (1 minute)
Open the link. If you see a button that says the app is asleep, click it and wait about a minute. The free host sleeps when nobody visits for 12 hours.
Pick a message. Click one of the four example buttons, or type your own customer message. Please do not type personal information.
Click "Check this ticket". The first answer can take up to a minute.
Read the result:
What you see	What it means
Green box: "safe to send automatically"	The system is confident, and a reply can go out without a person
Yellow box: "a team member should check this ticket"	The ticket is urgent, about money, or the reply contains a number that a person must verify
Type of problem	Billing, technical problem, refund or return, or general question
How urgent	Urgent, medium, or not urgent
Handled by	A simple rule (no AI) or the AI
Suggested reply	The reply draft, and the FAQ page or rule it came from
Look around. My tickets lists what you checked in this visit. Help center (FAQ) shows the company facts and lets you test which FAQ page a message would match. How it works explains the steps in plain words.

Messages to try

Message	What you should see
Do you deliver abroad?	A reply built from the shipping FAQ. It contains numbers, so the box is yellow: a person must check them
I was charged twice this month!	Billing and urgent, with a yellow box
Please unsubscribe me from your emails.	Handled by a simple rule with no AI, and a fixed reply
Do you sell gift cards?	No FAQ page matches, so the reply says a team member will follow up. Nothing is invented

Each visitor gets 5 checks per visit, and nothing you type is saved after you leave.

Why I built it

Support teams spend a lot of time reading and sorting the same kinds of messages. I wanted to build a small version of a real AI system where the model is only one part of the design, and where plain code decides what is safe to send.

What it does
Rules first. Easy tickets (unsubscribe, opening hours, password reset, returns) are handled by plain code. No AI is used, and they get a fixed reply.
AI sorts the rest. A language model picks a category and an urgency. Pydantic forces the answer into a fixed shape.
FAQ search. The message is turned into an embedding and matched against a small company FAQ.
Grounded reply. If an FAQ page matches, the model may only rewrite that fact. If nothing matches, no AI is used and the customer gets a fixed "a team member will follow up" reply.
Reply guards. If the model adds a new number or much more text than the fact, its reply is thrown away and the plain fact is used instead.
A safety check decides. Risky tickets go to a human instead of being sent automatically.
It fails safe. If the model service is busy or down, a ticket is sent to a person and replies fall back to plain facts. Nothing crashes and nothing is guessed.
Everything is saved. The REST API stores every ticket in a SQLite database. A Streamlit dashboard shows tickets, the FAQ, and a live box to try a new message.
Workflow
Yes
No
Yes
No
Risky or unsure
Safe
Customer ticket from theAPI or the dashboard
Matches a simple rule?
Sort with the rule and use afixed reply
AI sorts the ticket: categoryand urgency
FAQ page found?
AI rewrites the FAQ fact,guards check the reply
Fixed holding reply, no AI
Safety check
Human review
Auto-reply
Saved in the SQLitedatabase
Dashboard and API read theresults
Safety check

A ticket is sent to a human if any of these is true. This check is plain code, not AI, so it behaves the same every time.

Check	Why
Urgency is high	The customer is blocked or losing money right now.
Category is billing or refund	Money decisions need a person.
The reply contains a number or time	The model can invent facts, such as made-up opening hours.
The reply contains a risky word (for example "guarantee" or "promise")	The model should never promise things on behalf of the company.
The AI was unavailable	Nobody could sort the ticket, so a person looks at it.
Keeping replies grounded

An early test showed the model inventing details even when told not to (a made-up unsubscribe link, made-up opening hours, and "yes, we sell gift cards" with no such fact). Instructions alone were not enough, so the controls moved into code:

The model only writes when it has a fact from the FAQ. Without a fact, a fixed reply is used.
A reply with a number that is not in the fact is replaced by the plain fact.
A reply much longer than the fact is replaced by the plain fact.

Every reply also records its source (a fixed rule reply, a named FAQ page, or a holding reply), so a reviewer can see why the system said what it said.

Dashboard and public demo mode

The Streamlit dashboard has four tabs: check a ticket, all tickets (search, filters, CSV download), the FAQ help center (with a search test), and a short explanation of how it works.

Setting DEMO_MODE=true makes it safe to host publicly:

In demo mode	Why
Each visit gets a limited number of checks, and there is a daily limit for all visitors	Strangers cannot use up the free model quota.
Tickets are kept only in the visitor's own session and are not saved	Visitors cannot read each other's messages.
Editing the FAQ is turned off	Strangers cannot change the company facts.
Messages are limited to 500 characters, and a note asks people not to type personal information	Keeps the demo cheap and safe.
REST API

Start it with uv run uvicorn api:app --reload. FastAPI builds an interactive test page at http://127.0.0.1:8000/docs.

Endpoint	What it does
POST /tickets	Send a customer message. It runs the whole pipeline, saves the result, and returns it.
GET /tickets	List the newest saved tickets.
GET /tickets/{id}	Get one saved ticket.
GET /stats	Count total tickets, tickets sent to a human, and tickets sorted by rules.
GET /health	Check that the service is running.
Tech stack
Part	Tool
Language	Python 3.12
Chat model	llama3.2 (local, with Ollama) or a hosted model such as Gemini
Embeddings (FAQ search)	nomic-embed-text (local) or gemini-embedding-001 (hosted)
Model access	OpenAI-compatible Python SDK (model and server are set in .env)
Structured output	Pydantic
API	FastAPI and Uvicorn
Database	SQLite
Dashboard	Streamlit
Tests and CI	pytest and GitHub Actions
Packages and environment	uv
Results

Measured against hand-labeled data. The tickets and messages are fake. A perfect score on a small test does not prove a model is perfect, so these numbers are only a starting point.

Sorting (30 tickets, answer key labeled by me)

Model and test	Category	Urgency
llama3.2 (local): first version, tickets 1-10	9 of 10	7 of 10
llama3.2 (local): after prompt and rule changes, tickets 1-10	10 of 10	10 of 10
llama3.2 (local): fresh tickets 11-30	19 of 20	18 of 20
Gemini flash-lite (hosted): tickets 1-10	10 of 10	10 of 10
Gemini flash-lite (hosted): fresh tickets 11-30	20 of 20	20 of 20

With the local model, all 3 mistakes on the fresh tickets were still sent to a human by the safety check. The hosted model name ends in -latest, which Google can move to a newer model, so these scores are from November 2026.

FAQ replies (10 messages I wrote: 7 with an FAQ answer, 3 without)

Test	Result
Right FAQ page chosen (or correctly none), local and hosted search	9 of 10
Replies with no invented facts, before the guards (llama3.2)	about 8 of 10
Replies with no invented facts, after the guards (llama3.2)	10 of 10
Replies with no invented facts, after the guards (Gemini)	10 of 10

The one wrong FAQ choice was a safe miss: the ticket got the "a team member will follow up" reply. The FAQ cut-off depends on the search model. Local embeddings use 0.60. With the hosted embeddings, unrelated messages scored 0.58 to 0.65 and correct matches scored 0.66 to 0.91, so I set the cut-off to 0.70 from only 12 messages. I changed the guards after seeing these same messages, so the reply scores are not a fresh test.

Tests

The pytest tests cover the rules, the safety check, the database, and the API. The database and API tests use a temporary database and a fake pipeline, so they run in a second and need no model. GitHub Actions runs them on every push.

uv run pytest
Project structure
ticket_helper/
├── .github/workflows/tests.yml   runs the tests on every push
├── src/
│   ├── classifier.py   AI sorter: category and urgency
│   ├── rules.py        simple rules that run before the AI
│   ├── knowledge.py    FAQ search with embeddings
│   ├── replier.py      grounded reply writer, fixed replies, reply guards
│   ├── safety.py       decides auto-reply or human review
│   ├── pipeline.py     one function that runs the whole system for a message
│   └── database.py     SQLite storage for tickets
├── data/
│   ├── tickets.json    30 fake tickets
│   ├── answer_key.json the correct category and urgency for each ticket
│   └── faq.json        the company FAQ (made-up facts for the demo)
├── tests/              tests for the rules, safety check, database, and API
├── docs/dashboard.png  dashboard screenshot
├── api.py              FastAPI service
├── dashboard.py        Streamlit dashboard
├── main.py             runs the pipeline over the sample tickets
├── evaluate.py         scores the sorter against the answer key
├── evaluate_replies.py checks FAQ choice and reply grounding
├── conftest.py         lets pytest find the src folder
├── .env.example        the settings the project needs, with no secrets
├── pyproject.toml      packages
└── uv.lock             exact package versions
Settings

All settings live in a .env file (see .env.example). The real .env is never committed.

Setting	What it does	Local example	Hosted example
LLM_BASE_URL	Where the model is	http://localhost:11434/v1	https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY	The key	ollama (not a real key)	your key
LLM_MODEL	Chat model	llama3.2	a Flash model name
EMBED_MODEL	Search model	nomic-embed-text (default)	gemini-embedding-001
FAQ_THRESHOLD	How close an FAQ match must be	0.60	0.70
DEMO_MODE	Public demo mode	false	true
SESSION_LIMIT / DAILY_LIMIT	Checks per visit and per day in demo mode	5 / 100	5 / 100

The FAQ cut-off depends on the search model, so it must be set again whenever the embedding model changes.

How to run it
Install uv and install the packages:
uv sync
Copy .env.example to .env (on Windows: copy .env.example .env).
For the local setup, install Ollama, download the two models, and keep the server running in its own terminal:
ollama pull llama3.2
ollama pull nomic-embed-text
ollama serve

For a hosted model, put its settings in .env instead (see the table above).

In another terminal, run any of these:
uv run uvicorn api:app --reload      # start the REST API
uv run streamlit run dashboard.py    # open the dashboard
uv run main.py                       # process the sample tickets
uv run evaluate.py                   # score the sorter against the answer key
uv run evaluate_replies.py           # check the FAQ replies
uv run pytest                        # run the tests

If Ollama crashes with a CUDA error on a computer with an old graphics driver, run it on the CPU instead. In PowerShell:

$env:CUDA_VISIBLE_DEVICES="-1"
ollama serve

Free hosted models can answer "too many requests" (429) or "busy" (503). The client retries, and the system falls back safely if the model still does not answer.

Design decisions
Use as little AI as possible. Plain rules run first because they are free, instant, and always the same.
Plain code decides what is risky. The model can be wrong, so a deterministic safety check has the final say.
Controls live in code, not in the prompt. The model ignored "do not invent facts" in testing, so the limits are enforced by code.
Fail safe. When the model service is unavailable, the system asks a person instead of guessing.
One function runs the system. process_ticket hides all the steps, so the API, the dashboard, and the scripts share the same logic.
Measure before changing. Prompt changes were tested against an answer key, and fresh tickets were added so the score is not just memorized.
The models are configurable. The model and server are set in .env, so a local or hosted model can be used without code changes. The FAQ cut-off had to be recalibrated when the embedding model changed.
Limits and next steps
The tickets, FAQ, and test messages are fake, and I labeled them myself. The test sets are small.
The reply guards are strict, so the model's own wording is often replaced by the plain fact. The replies are safe but plain.
FAQ search misses some phrasings (for example "When can I reach your support team?"). A missed match gives the safe "a team member will follow up" reply.
The FAQ cut-off was chosen from only 12 messages.
The public demo stores nothing, and the free host sleeps after a period without visitors.
Next: more labeled tickets, several phrasings per FAQ entry, Docker, and a comparison of more models.
