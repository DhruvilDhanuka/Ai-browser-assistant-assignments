# AI Browser Assistant — Context Doc

Paste this into a new chat to resume exactly where we left off. Covers Module 1 (Intelligent Form Filling, functionally complete) and Module 2 (Email Assistant, mid-build, currently debugging a live bug).

## Project & working rules
- 6-module personal AI browser assistant. Building module by module, deeply enough to explain every piece to an interviewer.
- **User writes all code himself.** Claude guides/explains/reviews only — does not proactively create files or write implementation code unless explicitly asked.
- Stack: React + TypeScript + TanStack Router/Query/Form (frontend), FastAPI + SQLAlchemy + SQLite (backend), Playwright (browser automation), LangChain (`create_react_agent` + `AgentExecutor`), Gemini 2.5 Flash (LLM, via both `langchain_google_genai.ChatGoogleGenerativeAI` and raw `google.genai` SDK), Groq (originally used, dropped — see "Key decisions").
- Repo: `AI-browser-assistant/backend` and `AI-browser-assistant/frontend`, Windows machine.

## Key architectural decisions
- **Fresh project**, not built on old Assignment 6 code.
- **Browser control**: server-driven Playwright (`launch_persistent_context`) against the user's **real Chrome profile** (`Profile 2`), not a bare Chromium and not a browser extension. A full profile clone is made once into `AgentChromeProfile` (via `shutil.copytree`, with `ignore_patterns` planned but not yet applied) so the agent's browser and the user's real open Chrome can run simultaneously without file-lock conflicts.
- **URL input**: user pastes/types the target URL directly in the command — no active-tab-detection extension was built (deferred).
- **Top-level routing**: single Gemini LLM call (`topLevelModuleClassifier.py`) classifies each command into one or more of: `form_filling`, `email`, `summarization`, `calendar`, `general`. Returns structured JSON with per-module `actions` (each carrying only its own module-specific data key, e.g. `form_filling_data`, `email_data`). `load_modules()` dispatches to the matching module's `.run(user_id, task_id, command)`.
- **No separate Module 6 (memory) classifier target** — memory (profile, documents, contacts) is infrastructure every module reads/writes into, not a command category.
- **Task/status pattern**: `Commands` table, one row per command (`task_id`, `user_id`, `command`, `status`). `status` is intended to be a **JSON column holding a growing list of activity-log strings** (not the original `SQLEnum(StatusTask)` design) — background task appends to it, WebSocket polls and streams only new entries to the frontend. **This is the subject of the current live bug — see "Open bug" below.**
- **Live activity feed**: WebSocket `/commands/ws/{task_id}`, polls every 1s, tracks `last_sent_index` to avoid resending old entries, breaks the loop when the last entry contains "Task Completed" or "Task Failed".
- **Ask-user pattern (blocking)**: `app/AgentsForModules/pendingAnswers.py` — a module-level `dict[task_id] -> {event: threading.Event, answer}`. A tool calls `register_question(task_id)`, appends a specially-prefixed string to `status` (e.g. `ASKING_USER::...`, `ASKING_USER_FILE::...|||doc_type`, `CONFIRM_SEND::to|||subject|||body`), then blocks on `event.wait()`. Frontend detects the prefix on the last activity-log entry, shows the matching UI, POSTs the answer to `/commands/{task_id}/answer` (text/confirm) or `/documents/{task_id}/answer/file` (file), which calls `submit_answer(task_id, answer)` to set the answer and `.set()` the Event, unblocking the tool.
- **Rate-limit-driven redesign (important)**: original form-filling agent reasoned field-by-field via ReAct (one LLM call per field) — this exhausted Groq's free tier (30 RPM/6000 TPM) and then Gemini's actual free tier (**5 RPM** for gemini-2.5-flash, verified via real 429 error, not just docs). Fixed by collapsing per-field reasoning into **one batch LLM call**: `map_profile_to_fields()` (in `form_filler.py`, uses raw `google.genai` SDK, structured JSON output) takes the full detected-fields list + profile + documents in one call, returns `{filled: {ffId: value}, missing_text: [...], missing_file: [...]}`. `auto_fill_form_tool` (the only tool the ReAct agent needs to call after navigating) executes that plan in plain Python — no further LLM calls per field. Cut a 16-field form from ~20-30 LLM calls down to ~4-5 total.
- Corollary refactor: extracted `_fill_field`, `_ask_user_text`, `_ask_user_file`, `_append_status` as **plain Python methods** on `Form_Filler` (not `@tool`-wrapped), since `@tool` functions can't cleanly call each other — `auto_fill_form_tool` and the individual thin `@tool` wrappers (`fill_field_tool`, `ask_user_tool`, etc.) both call these shared plain methods.
- **LLM swapped Groq → Gemini 2.5 Flash** for `Form_Filler` specifically, both for the rate-limit headroom and because Gemini is natively multimodal (needed later for vision fallback). Groq's free tier (30 RPM / 6000 TPM) was the original crash cause before the batch redesign made it moot anyway.
- **Documents/profile storage**: `UserProfile` has fixed columns (`Name`, `Email`, `Contact_number`, `College`, `Skills`) + `extra_info: JSON` (dict, dynamic facts learned over time — populated automatically by `ask_user_text`). `Documents` table: **one row per user** (`user_id` unique), `docs: JSON` = list of `{doc_type, path, filename}` dicts (not one-row-per-document — deliberately chosen to avoid an FK-per-doc table). File uploads validated by extension + `content_type` (PDF only for resumes).
- **Contacts for email module**: `ContactGroup` table, one row per user (`user_id` unique), `groups_with_number: JSON` = **plain dict** `{"team": ["a@x.com", ...], "classmates": [...]}` (not list-of-single-key-dicts — simplified after discussion). **Not yet populated** — no UI/endpoint exists yet to add groups.
- **Gmail integration**: OAuth (not SMTP/IMAP) — chosen because Module 4 (Calendar) will need Google OAuth too, so auth is shared infrastructure. Standalone `quickstart.py` OAuth test succeeded (Desktop app credentials, External + Testing mode, test user added under Google Auth Platform → Audience, scopes `gmail.readonly` + `gmail.send`). Real per-user integration (`GmailCredentials` table + `gmail_auth.py` helper wrapping `get_gmail_service(db, user_id)`) is designed but the auth helper module itself has not yet been built/wired — `email_sender.py` currently calls `get_gmail_service` assuming it exists.

## Module 1 — Intelligent Form Filling: STATUS = functionally complete, not fully re-tested since last redesign
Built and working (confirmed via real test runs against `demoqa.com/automation-practice-form`):
- `detect_fields()` — Playwright, walks `page.frames` (handles iframes natively, no manual recursion needed), injects JS (`EXTRACTION_SCRIPT`) that stamps a random `data-ff-id` attribute on every fillable element, extracts label via a cascade (`<label for>` → wrapping `<label>` → `aria-label` → `aria-labelledby` → `placeholder` → nearby-sibling-text fallback), returns flat list of field dicts tagged with `frameUrl`.
- `map_profile_to_fields()` — single Gemini call, batch field-mapping (see "Key decisions" above).
- `auto_fill_form_tool` — orchestrates: detect → map (1 LLM call) → loop through `filled`/`missing_text`/`missing_file` in plain Python, calling `_fill_field`/`_ask_user_text`/`_ask_user_file` directly.
- `_fill_field(ff_id, value)` — locates via `data-ff-id` across all frames, branches on tag/type: `select` (tries `value=` then falls back to `label=`), `checkbox` (check/uncheck based on truthy string), `file` (`set_input_files(path)`), `radio` (`check()`), else `fill(value)`.
- `_ask_user_text(label, question)` — blocks via `pendingAnswers`, **auto-saves the answer to `UserProfile.extra_info[label]`** on return (the "asks once, remembers forever" feature).
- `_ask_user_file(doc_type, question)` — blocks, **auto-saves to `Documents.docs`** on return.
- Live activity feed fully wired (`update_status` tool + `_append_status` helper, WebSocket streaming).
- Chrome profile persistence via `launch_persistent_context` + one-time profile clone.

Confirmed via real run: correctly split "Dhruvil Dhanuka" into separate First/Last Name fields, correctly identified unmapped fields (gender, DOB, hobbies, picture, address, state, city) and planned to ask for each, filled matched fields correctly. **This run predates the batch-mapper redesign being applied** — the redesigned version has been written and reviewed but not yet run end-to-end. Next actual test should confirm the full loop completes in ~4-5 LLM calls without hitting a 429.

Not built (from the original slide, still open for Module 1):
1. **Preview/confirm before final form submission** — nothing currently gates a submit click behind user approval (note: `CONFIRM_SEND::` pattern from Module 2 could be reused for this).
2. **Long-text answer generation** (SOP, "why do you want to join") + the `AnswerTemplate` table (designed early on: `category`, `name`, `content`, `times_used`) — table was designed but never actually created/wired in.
3. **Validation-error retry loop** — no logic to detect a failed submission and re-correct.
4. **Google Forms native support** — untested; Google Forms uses non-standard div/aria widgets, not plain `<input>`.
5. **Vision fallback** (screenshot → multimodal Gemini) — not built.

## Module 2 — Email Assistant: STATUS = mid-build, blocked on a live bug
Built:
- Gmail OAuth quickstart proven working standalone (see "Key decisions").
- `ContactGroup`, `GmailCredentials` models designed (GmailCredentials: `user_id` unique FK, `token_json: String`, `updated_at`).
- `email_sender.py` (`Email_Sender` class, mirrors `Form_Filler`'s structure): `generate_draft()` (single Gemini call, JSON `{subject, body}`), tools — `resolve_recipient_tool` (checks `ContactGroup` dict, then "@" heuristic, then falls back to blocking `ask_user_text`-style question), `draft_email_tool`, `confirm_send_tool` (blocks via `CONFIRM_SEND::to|||subject|||body`, returns `"approved"`/`"rejected"`/edited text), `send_email_tool` (only ever called after confirm), `list_unread_tool`, `get_thread_tool` (fetches a **whole thread** — all messages both directions, not just one side, since thread-aware replies need full context).
- Frontend `CommandsSection.tsx`: `CONFIRM_SEND::` detection + draft display + Send/Cancel buttons, wired to the **same** generic `/commands/{task_id}/answer` endpoint used for text answers (no separate endpoint needed — `submit_answer`/`register_question` don't care which tool is waiting, purely keyed by `task_id`). An earlier duplicate/broken "email address" special-case UI path was identified and removed (redundant with the generic `ASKING_USER::` handler; also pointed at a nonexistent `/answer/email` endpoint).

**Open bug, actively being debugged right now:**
- Command tested: "send an email to my son for congratulating him for selection in IIT Bombay."
- Backend terminal (`verbose=True`) shows the agent correctly reasoning through `update_status` → `resolve_recipient_tool("my son")` and then sits frozen (expected — `event.wait()` blocking correctly).
- **But the WebSocket never delivers anything past "Task under processing"** to the frontend — confirmed via Chrome DevTools Network → WS Messages tab, checked twice while the task was still live/frozen, only ever shows the original 2 early messages.
- Direct DB check (`sqlite3`, `SELECT status FROM commandsAndStatuses ORDER BY task_id DESC LIMIT 1`) while task is frozen returns **`('null',)`** — the `status` column has been overwritten to JSON `null`, not even an empty list.
- **Leading hypothesis, not yet confirmed**: the `Commands` SQLAlchemy model's `status` column may still be declared as `Column(SQLEnum(StatusTask), index=True)` (its original type from early in Module 1) rather than having actually been migrated to `Column(JSON, default=list)` to match the "status as growing activity list" design that's been used in code ever since. If so, assigning a Python list to an Enum-typed column could be causing a silent serialization failure that collapses to `null`.
- **Next action**: user needs to open `app/models_db/Commands.py` and paste the exact current `status = Column(...)` line to confirm or rule out this hypothesis. This is exactly where the conversation left off.

## Known simplifications / honest caveats (worth mentioning to an interviewer)
- Radio/checkbox groups aren't pre-grouped by the field detector by `name` — deferred to the mapper.
- Label detection is heuristic, not guaranteed correct — vision fallback (unbuilt) is meant to catch what it misses.
- Single browser session at a time, no concurrent session manager.
- `_pending_answers` registry is in-memory, single-process — would need Redis or similar if scaled beyond one backend worker.
- Chrome profile clone is a full copy (slow, includes cache/junk) — trimming to just `Cookies`/`Login Data`/`Preferences` was deferred ("we'll fasten it later").
- SQLite + sync SQLAlchemy throughout — acceptable at this scale, flagged as a place to revisit if the event loop starts blocking noticeably under load.
