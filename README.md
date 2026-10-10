# NEC Fee Assist

AI-based fee assistance and task navigation project for **SYED SUFYAN - 2403957610421048**.

This independent academic application uses Python, SQLite and a responsive browser interface. It runs locally with illustrative data and simulated payments. It does not connect to the official NEC ERP or a real payment provider.

## Run on Windows

Open PowerShell in the project folder and run:

```powershell
.\run.ps1
```

Or run the commands individually:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.server
```

Open **http://127.0.0.1:8765**. Stop with Ctrl+C. Use `--port 8766` for another port.

On first start, random passwords are generated locally. Read them in PowerShell:

```powershell
Get-Content -LiteralPath .\data\demo_credentials.json
```

Student ID: `2403957610421048`. Administrator ID: `admin`. Existing accounts, fees and payments are preserved. The archive excludes runtime credentials and databases; a new installation creates its own.

## AI assistant

Open **Fee assistant** from the navigation or the launcher on any page. Try:

- `How much are my pending fees?`
- `Could you navigate to my profile?`
- `Help me pay tuition`
- `Help me pay library and tuition`
- `Take me to payment history`
- `Download my receipt`
- `Next step` or `Cancel task`
- Administrator: `Help me assign fees`, `Open student directory`, `Open fee ledger`.

The assistant opens permitted pages automatically, selects relevant owned pending fees, finds protected receipts and supplies workflow steps. On desktop the assistant sits alongside the destination page; on mobile it uses a dismissible panel. Students confirm demo payments through the normal payment form. Administrator changes use the existing page forms.

Task understanding uses a learned multinomial Naive Bayes classifier trained from 80 labelled examples across 12 classes, with TF-IDF relevance evidence and abstention thresholds. Account questions use authorized records; policies use maintained text retrieval. The model is offline classical AI, with no cloud LLM or API key. Request detection and access-control rules constrain tool execution. Scores are relevance values, not correctness probabilities.

The tool registry permits internal navigation, owned pending-fee selection and selection clearing. It cannot execute arbitrary URLs, scripts, SQL, payments or administrator mutations. Task state is session-scoped; history is displayed without replaying its actions. The server and browser both validate actions.

## Portal features

- Student overview, fee selection, profile, transaction history and protected PDF receipts.
- Completed, failed and cancelled simulated payments with atomic settlement and idempotent retries.
- Administrator student creation, fee allotment, ledger CSV export, policy maintenance and audit records.
- Salted PBKDF2 password hashes, expiring HttpOnly/SameSite session cookies, CSRF, role/owner checks, request limits and origin validation.
- Additive database migration for agent state and conversation actions; existing fee/payment data is retained.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check app/static/app.js
.\.venv\Scripts\python.exe scripts/evaluate_ai_agent.py
```

The suite has **43 tests**, including navigation, account isolation, role restrictions, fee preparation, multiple fee categories, cancellation, receipt ownership, stale task state, injection requests and ordinary payment behavior. The authored 40-request development diagnostic currently matches all expected outcomes. It was reused during development and is not an independent accuracy benchmark.

Optional browser/report tooling:

```powershell
.\.venv\Scripts\python.exe -m pip install playwright pymupdf pillow
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/capture_ai_lab.py
.\.venv\Scripts\python.exe scripts/evaluate_ai_agent.py
.\.venv\Scripts\python.exe scripts/build_ai_lab_report.py
```

The capture script starts its own loopback server with an isolated temporary database and stops it after verification. It does not modify the regular project dataset. Source screenshots show actual project files in a source viewer. Report assets and personalized format templates allow regeneration without the friend's PDF. The report builder uses Windows Times New Roman fonts.

## Final AI lab report

`output/pdf/NEC_Fee_Assist_AI_Lab_Report_SYED_SUFYAN.pdf`

The 26-page report follows the supplied AI micro-project structure: cover, contents, seven chapters, all-page borders, Times New Roman text, architecture/pipeline diagrams, code and output screenshots, measured results and original assessment tables. Course instructor and marking fields remain unsigned, as in the reference.

## Scope

The loopback Python HTTP server is for laboratory evaluation. Production use needs approved identity/data integration, HTTPS, a production application server, backups and account lifecycle controls. Real gateway settlement is not implemented. The lexical model has limited English vocabulary and a bounded tool set; semantic models, multilingual support and broader dialogue planning are future work.
"# NEC-FEE-BOT" 
