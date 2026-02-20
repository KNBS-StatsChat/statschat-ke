# StatsChat (NSO) Participant Pre-Course Questionnaire (5–15 minutes)



## Intro text

Thanks for taking this short questionnaire. This is **not an exam**—it helps us tailor the training (pace, prerequisites, and which topics to emphasize). Please answer honestly; “I’m not sure yet” is a perfectly good answer.



**What we’re training on (high level):** a Retrieval-Augmented Generation (RAG) workflow that (1) ingests PDF reports and converts the PDFs to structured JSON, (2) retrieves relevant passages and (3) asks an LLM to answer questions **using only the retrieved context**.



---



## Section A — Background (2–3 minutes)






**A1. Organisation / NSO**

Type: Short answer



**A2. Primary role(s)**

Type: Checkboxes (choose all that apply)

- Statistician

- Data Analyst

- Data Scientist

- Geoinformation specialist

- Software engineer

- AI / Data engineer

- Other: ____

**A3. Briefly describe what your current role involves or what tasks you perform regularly:**

Type text box



**A4. What would “success” look like for you after this course?**
Please answer in 1–3 sentences.

Examples:
- Use StatsChat to answer questions from reports
- Adapt StatsChat to our own NSO documents
- Operate/maintain the StatsChat pipeline (updates, monitoring)
- Deploy an API service internally

Type: text box




---



## Section B — Practical readiness (2–4 minutes)



**B1. What is your main working operating system?**

Type: Multiple choice

- Windows

- macOS

- Linux



**B2. Do you expect to have permission to install software on your machine for the course?**

Type: Multiple choice

- Yes

- No

- Not sure



**B3. Which of these have you used before (even once)?**

Type: Checkboxes

- `python` from a terminal

- Creating a virtual environment (venv/conda)

- Installing packages with `pip`

- Using environment variables / `.env` files for API keys

- `git clone`, `git pull`, `git commit`

- Running a web API locally (e.g., `uvicorn`/FastAPI)

- Running Docker



**B4. If you’ve used Python, which best describes your comfort level?**

Type: Multiple choice

- I haven’t used Python

- Basic (can modify scripts, run notebooks, follow examples)

- Intermediate (write functions/classes, debug issues)

- Advanced (build packages/services, tests, async, profiling)



---



## Section C — Short skills check (Python + data) (3–6 minutes)



(These are quick diagnostic questions to help us pitch the level.)



**C1. In Python, what is the output of this code?**

Type: Multiple choice



```python

x = [1, 2, 3]

y = x

y.append(4)

print(x)

```



- `[1, 2, 3]`

- `[1, 2, 3, 4]`

- `[4]`

- Not sure



**C2. Which line reads a JSON file from disk in a robust, cross-platform way?**

Type: Multiple choice

- `data = open('file.json').read()`

- `data = json.load(open('file.json'))`

- `data = json.loads(Path('file.json').read_text(encoding='utf-8'))`

- Not sure



**C3. You run a script and get `ModuleNotFoundError: No module named 'fastapi'`. What is the most likely fix?**

Type: Multiple choice

- Restart the computer

- Install the missing package in the active environment (e.g., `pip install fastapi`)

- Delete the repository and re-download

- Not sure



**C4. In pandas, what does `groupby` most commonly help you do?**

Type: Multiple choice

- Split data into groups and compute summaries per group

- Convert text to embeddings

- Download PDFs from a website

- Not sure



---



## Section D — Software engineering & collaboration (2–4 minutes)



**D1. How comfortable are you with Git?**

Type: Multiple choice

- I’ve never used Git

- I can clone/pull and make small changes

- I can use branches, resolve simple conflicts

- I can review PRs, manage workflows, handle conflicts confidently



**D2. How comfortable are you with debugging in Python?**

Type: Multiple choice

- I usually get stuck

- I can debug with print/logs

- I can use a debugger and read stack traces

- I can debug complex issues across modules



**D3. Have you used any of these before?**

Type: Checkboxes

- `pytest` (testing)

- `pre-commit` or linters/formatters (ruff/black/etc.)

- packaging/project config (`pyproject.toml`)



---



## Section E — RAG / StatsChat concepts (3–6 minutes)

These questions are included to understand any prior familiarity. **You are not expected to know these yet**—we will explain these concepts during the course. Feel free to choose “Not sure”.



**E1. Which ordering best matches the StatsChat-style pipeline?**

Type: Multiple choice

- Download PDFs → Convert to JSON → Chunk text → Create embeddings → Build FAISS index

- Create embeddings → Download PDFs → Build FAISS index → Convert to JSON → Chunk text

- Ask LLM → Download PDFs → Return answer

- Not sure



**E2. What does an “embedding” represent in this context?**

Type: Multiple choice

- A compressed numeric representation of text meaning used for similarity search

- A ZIP file containing PDFs

- A citation to a PDF page

- Not sure



**E3. What does a vector store (e.g., FAISS) mainly do for us?**

Type: Multiple choice

- Stores and searches embeddings to retrieve relevant text chunks

- Generates answers directly

- Converts PDFs into JSON

- Not sure



**E4. In a RAG system, what is the main purpose of the “retrieval” step?**

Type: Multiple choice

- Find relevant context passages to constrain the LLM

- Train the embedding model from scratch

- Host the API server

- Not sure



**E5. Which is the best description of “hallucination” risk in LLMs?**

Type: Multiple choice

- The model may produce fluent but incorrect statements not supported by sources

- The model refuses to answer any question

- The vector store returns too many results

- Not sure



**E6. Have you evaluated LLM (or RAG) responses before?**
Type: Multiple choice
- No
- Yes, informally (manual checks / spot-checking)
- Yes, using a simple rubric (e.g., accuracy, completeness, citations)
- Yes, using structured evaluation (datasets, review process, automated checks)

---



## Section F — API & deployment (optional emphasis) (2–4 minutes)

These questions are only to gauge prior experience. **You are not expected to have worked with APIs or deployment before**—we will cover what you need in the course. “Not sure” is fine.



**F1. Have you used FastAPI (or similar) before?**

Type: Multiple choice

- No

- A little (ran an example)

- Yes (built endpoints)

- Yes (deployed/operated an API)



**F2. What does `uvicorn` typically do in a FastAPI project?**

Type: Multiple choice

- Runs the API server process

- Downloads PDFs

- Creates embeddings

- Not sure



**F3. How comfortable are you with Docker?**

Type: Multiple choice

- Never used it
- I can run existing containers
- I can build images and troubleshoot basics
- I can design multi-service deployments


**F4. Have you worked with compute setups to speed up model inference (GPU or high-performance CPU)?**
Type: Multiple choice
- No
- A little (I’ve used a GPU-enabled machine or instance)
- Yes (I can verify GPU availability, install/maintain tooling, and troubleshoot basics)
- Yes (I’ve tuned performance or managed GPU/compute in production)




---



## Section G — Logistics & learning preferences (1–2 minutes)



**G1. What learning format helps you most?**

Type: Multiple choice

- Live walkthroughs

- Hands-on exercises

- Pair/small-group work

- Reading docs then Q&A



**G2. Any constraints we should plan around? (time, connectivity, compute, permissions, etc.)**

Type: Paragraph



**G3. Anything else you want us to know?**

Type: Paragraph



---



# Internal scoring rubric (for organisers; don’t show to participants)



This is intentionally lightweight—use it to identify who may benefit from a short pre-course prep session.



## Suggested banding (from diagnostic questions only)

- **Python/Data readiness**: C1–C4 (0–4 points)

- Give 1 point per correct answer (ignore “Not sure”).

- 0–1: recommend Python/pandas pre-session

- 2–3: ok for core course, may need support

- 4: can handle faster pace



## Suggested “prep topic” flags (from self-report)

- If B3 lacks venv/pip: prep on environments + installation

- If D1 is “never used Git”: prep on git basics for the repo workflow

- If E1–E4 mostly “Not sure”: spend more time on RAG mental model before deep dives

- If F1/F3 low but deployment is a course goal: schedule an optional API/Docker primer
