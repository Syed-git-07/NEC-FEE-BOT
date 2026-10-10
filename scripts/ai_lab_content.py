"""26-page AI lab report plan matching the supplied seven-chapter reference."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
E=json.loads((ROOT/'output/ai_lab_assets/agent_evaluation.json').read_text())
PAGES=[]
def page(ch,title,*blocks):PAGES.append({'chapter':ch,'title':title,'blocks':blocks})
def p(t):return ('p',t)
def h(t):return ('h',t)
def b(t):return ('bullet',t)
def code(file,needle,n):
    lines=(ROOT/file).read_text().splitlines();start=next(i for i,l in enumerate(lines) if needle in l)
    return ('code','\n'.join(lines[start:start+n]))
def literal(t):return ('code',t)
def table(head,rows):return ('table',(head,rows))
def figure(name,caption,height=240):return ('figure',(name,caption,height))
def diagram(name,caption):return ('diagram',(name,caption))

page(1,'INTRODUCTION',
p('College fee portals contain assigned fees, due dates, payment attempts and receipts, but students often need to visit several screens to complete one task. A student may know what they want to do without knowing the portal terminology or where the relevant control is located. Questions such as "How much do I owe?" and requests such as "Help me pay tuition" require different responses: the first needs account information, while the second needs a guided workflow.'),
p('This micro project presents NEC Fee Assist, an AI-based student fee assistance and task navigation system. It combines an authenticated student/admin portal, an offline language engine and a bounded task agent. The assistant can answer account questions, retrieve maintained fee policies, open relevant portal pages, select the requested pending fees, find completed-payment receipts and guide users through the next steps.'),
h('The Gap:'),
p('A question-answer chatbot can return useful text but still leave the student searching for the correct screen. A purely scripted command list also handles only a narrow set of phrases. At the same time, giving unrestricted financial authority to natural language input would make mistakes difficult to control. The need is therefore for an assistant that recognizes task requests, takes permitted interface actions and keeps financial confirmation in the normal portal workflow.'),
h('The Goal:'),
p('The primary objective is to build an accessible, explainable AI assistant that connects language understanding with practical portal tasks. The system uses a learned multinomial Naive Bayes task classifier trained from labelled examples, TF-IDF cosine evidence, authenticated account retrieval and a fixed registry of interface tools. Key functionalities include:'),
b('Student and administrator sign-in with separate roles and account-scoped records.'),
b('Source-grounded answers for balances, fee deadlines, payment history and maintained policies.'))

page(None,'',
b('Automatic navigation to permitted portal pages from natural language task requests.'),
b('Preparation of a category-specific payment by selecting owned pending fees for review.'),
b('A persistent assistant panel that remains available on the destination page.'),
b('Session-scoped task guidance, continuation and cancellation, with fresh checks of payment state.'),
b('Protected receipt links for completed simulated payments and guided administrator workflows.'),
p('The implementation is developed using Python, SQLite, HTML, CSS and JavaScript. The learned task model is implemented directly with sparse feature counts, Laplace smoothing and log likelihoods. Policy search uses unigram/bigram TF-IDF and cosine similarity. The assistant operates locally without an external language-model service or API key.'),
h('Project Scope:'),
p('The project is an independent academic demonstration. Its SQLite database, illustrative fee amounts and simulated payment outcomes are separate from the official college ERP and the production NEC fee portal. No money is transferred. The assistant prepares and guides tasks; the student completes a payment only through the existing demo payment confirmation form. Administrator changes likewise use the normal page forms.'),
h('AI Contribution:'),
p('The task classifier learns word and phrase likelihoods from 80 labelled examples across 12 classes, including a class for information questions. It does not consist only of one rule for every task phrase. Request detection and role checks constrain when a learned prediction may become an action. TF-IDF evidence and a class-separation threshold allow the planner to abstain from unsupported commands.'),
p('The project demonstrates language representation, probabilistic classification, retrieval, task planning, tool validation and evaluation in one workflow. It is a bounded classical AI agent rather than a generative large language model. Its vocabulary and tool set are deliberately limited and its measurements are reported as local development diagnostics.'))

page(2,'PROBLEM STATEMENT',
p('The core problem is the absence of a conversational layer that helps students both understand fee information and reach the controls needed to complete a task. A conventional portal displays records but expects the student to understand its menu structure. A text-only assistant may explain the next step without taking the student to the appropriate page or preparing the relevant fee selection.'),
p('This deficiency manifests in several critical areas:'),
b('Fragmented Navigation: Students must move between overview, pending fees, transaction history and profile pages to resolve related questions and tasks.'),
b('Variation in Language: Requests such as "Open my profile", "Take me to account details" and "Could you navigate to my profile?" should identify the same destination without a separate exact-match command for each sentence.'),
b('Account Grounding: Balances, due dates and receipt availability must come from the signed-in account rather than from generic policy text or a guessed answer.'),
b('Task Continuity: A useful assistant must retain the current task, explain what comes next and check whether the selected fees are still unpaid before continuing.'),
b('Authorization and Financial Control: A student request must not open administrator functions, access another student\'s records or bypass payment confirmation.'),
p('The proposed solution is an offline AI-assisted fee portal with a learned task classifier and a controlled execution layer. The assistant selects from predefined interface tools, applies the authenticated role and owner checks, and provides a clear fallback when it cannot support a request. The application retains ordinary confirmation forms for payments and administrator changes, while the conversational layer handles navigation, selection and guidance.'))

page(3,'MODULE DESCRIPTION',
p('NEC Fee Assist is structured into seven key modules. Together they convert a signed-in user\'s question or task request into a grounded answer or an authorized interface action.'),
b('Authentication and Access Control Module: Uses salted PBKDF2 password hashes, expiring server-side sessions, HttpOnly/SameSite cookies, CSRF validation and separate student/admin roles. The server derives the actor from the session.'),
b('Student Fee Management Module: Displays fee allocations, amounts and due dates, supports pending-fee selection and records completed, failed or cancelled simulated payments. Receipt access is restricted to the owner or an administrator.'),
b('NLP Answer and Policy Retrieval Module: Resolves account intents and fee categories, reads owned structured records and ranks maintained policy documents with unigram/bigram TF-IDF and cosine similarity.'),
b('Learned Task Understanding Module: Trains a multinomial Naive Bayes classifier from labelled utterances, computes class log likelihoods and uses cosine evidence plus a separation threshold before accepting an interface task.'),
b('Agent Planning and Tool Control Module: Produces only allowed navigation, fee-selection and selection-clear actions. It verifies roles and account data, prepares workflow steps and keeps task state within the authenticated session.'),
b('Conversational Interface and Auto-Navigation Module: Presents answers, source labels, task steps and receipt links. It opens the selected page, keeps the assistant visible and independently validates received action types and fee identifiers.'),
b('Administration and Evaluation Module: Provides student creation, fee allotment, ledger export, policy maintenance and audit records, together with isolated automated tests, browser checks and authored diagnostic evaluation.'))

page(None,'',
h('Architectural Foundation:'),
p('The browser communicates with a Python HTTP service using authenticated JSON endpoints. Application services enforce the session, role and account boundary before reading or changing records. The language engine and task agent run in the same local Python process, while SQLite stores account, fee, policy and conversation data. This modular structure permits the task model or retrieval logic to be changed without rewriting the portal screens.'),
h('Functional Modules:'),
table(['Project file','Responsibility'],[
['app/server.py','HTTP routes, cookie handling, host/origin validation, request bounds and CSRF checks.'],
['app/service.py','Authentication, authorized fee services, chatbot orchestration, agent state and receipt access.'],
['app/nlp.py','Tokenization, unigram/bigram features, TF-IDF ranking, account intents and fee categories.'],
['app/agent.py','Labelled training examples, learned task classification, bounded plans and role-scoped tools.'],
['app/schema.sql','Relational schema, ownership keys, constraints and stored conversation/action fields.'],
['app/static/app.js','Portal pages, assistant panel, automatic page changes and independent action validation.'],
['app/static/style.css','Responsive portal and assistant layout.'],
['tests/test_project.py','Temporary-database service, HTTP, payment and agent regression checks.'],
['scripts/evaluate_ai_agent.py','Authored task and safety diagnostic with measured results.']]),
h('Operational Flow:'),
p('The user signs in and opens Fee assistant from the navigation or the floating launcher. The user submits a question or task. The server reloads the current session and account records, then chooses the task-planning path or the ordinary account/policy answer path.'))

page(None,'',
p('For a task request, the agent predicts a task class and checks its relevance before constructing an allowed action list. "Help me pay tuition" produces navigation to Pending fees and a selection containing only the signed-in student\'s unpaid tuition allocations. The returned guide explains review, payment confirmation and receipt access. The browser executes the permitted interface actions and retains the assistant alongside the destination page.'),
p('For a question, the answer service reads the appropriate account records or retrieves the highest-ranked maintained policy. Account questions never use text similarity to invent a balance or due date. The response includes its source, and the exchange is recorded in conversation history.'),
p('When the user asks for the next step, the server reads the task from the current session. A payment guide rechecks whether its fees remain unpaid. If they have already been settled, the assistant opens Transaction history instead of selecting them again. Cancellation clears the task state and the browser fee selection.'),
diagram('pipeline','Figure 3.1: End-to-end question and task execution pipeline.'),
p('All financial and administrator writes remain ordinary authenticated form submissions. Neither model predictions nor stored history can execute a payment. Reopening conversation history displays prior actions as data without replaying them.'))

page(4,'ARCHITECTURE DIAGRAM',
h('4.1 Overview:'),
p('The architecture separates presentation, the authenticated HTTP boundary, language understanding, bounded task planning and persistent data. The browser remains responsible for interface navigation, while the server controls the identity, permitted destinations and owned fee identifiers supplied to each plan. The model cannot construct arbitrary URLs, SQL or executable scripts.'),
h('4.2 Architectural Diagram:'),
diagram('architecture','Figure 4.1: Layered architecture of NEC Fee Assist.'),
h('4.3 Layer Descriptions'),
h('4.3.1 User Interface Layer'),
b('Component: Responsive HTML, CSS and JavaScript student/admin portal.'),
b('Functionality: Overview, fees, history, profile, administrator pages and a persistent assistant panel.'),
b('Purpose: Connect natural language assistance with visible portal controls.'))

page(None,'',
h('4.3.2 Application Layer'),
b('Component: Python HTTP routes and application services.'),
b('Functionality: Authentication, session and CSRF checks, role/ownership validation, request limits, account retrieval, payment simulation and protected output downloads.'),
b('Purpose: Provide the controlled boundary between language requests and fee records.'),
h('4.3.3 AI and NLP Processing Layer'),
b('Component: app/agent.py and app/nlp.py using Python sparse dictionaries, counters, regular expressions and mathematical functions.'),
b('Functionality: Feature extraction, learned multinomial Naive Bayes classification, cosine evidence, account-intent resolution and maintained-policy retrieval.'),
b('Purpose: Choose a supported task or answer source without treating unrestricted text as an executable instruction.'),
h('4.3.4 Agent Tool and Dialogue Layer'),
b('Component: Role-scoped planner, server-side session task state and browser action executor.'),
b('Functionality: Allowed page navigation, owned fee selection, task continuation, cancellation, guide steps and receipt discovery. The client validates actions again before applying them.'),
b('Purpose: Translate an accepted prediction into a small, reviewable interface plan.'),
h('4.3.5 Data and Infrastructure Layer'),
b('Component: Independent SQLite database, local runtime directory and loopback-only evaluation server.'),
b('Functionality: Persists users, sessions, fees, simulated payments, settlements, policies, conversation records and audit events. Additive migrations preserve existing project data.'),
b('Purpose: Supply consistent, account-scoped facts and reproducible laboratory execution.'))

page(None,'',
h('4.4 Data Flow'),
b('1. The browser signs in and receives a server session cookie; subsequent requests use the authenticated account.'),
b('2. The user submits a question or task through the assistant. The server validates its type and maximum length.'),
b('3. The server refreshes session identity, task state, owned fees and payment records. Request wording is checked before learned task classification.'),
b('4. A supported task is converted to allowed navigation and selection actions after role and owner checks. Otherwise, the account/policy answer service handles the question.'),
b('5. The response carries an answer, source, relevance score, optional actions, guide and protected receipt links. The browser refreshes account data and validates the action list.'),
b('6. The page opens automatically and requested unpaid fees are selected. The user completes any financial or administrator change in its normal form.'),
b('7. The conversation and agent task event are stored. A later next-step request rechecks current state; cancellation clears the active task.'),
h('4.5 Key Design Decisions'),
b('Learned Understanding with Bounded Tools: The model predicts from examples, while a fixed tool registry controls what can happen.'),
b('Account Grounding: Amounts, deadlines and receipts originate from authorized database records.'),
b('User Confirmation: Selecting fees prepares a payment; the existing form remains the confirmation boundary.'),
b('Independent Client Validation: Unknown actions, external destinations and invalid fee identifiers are ignored.'),
b('Transparent Limits: Unsupported requests fall back; the project does not claim unrestricted language understanding or official ERP integration.'))

page(5,'CODING & IMPLEMENTATION',
h('5.1 Introduction'),
p('The implementation uses Python for the HTTP service, account operations, learned agent and retrieval engine. The browser interface uses HTML, CSS and JavaScript, and SQLite stores the independent demonstration dataset. ReportLab generates protected demonstration receipts. The core AI calculation requires no external machine-learning service.'),
h('5.2 Coding'),
p('The following extracts show the main implementation boundaries. The source screenshots in Sections 5.5 and 5.6 show these files in the project source viewer.'),
h('5.2.1 Session and Request Security (server.py):'),
p('After sign-in, every API request resolves the server session. State-changing requests require the session CSRF token. Receipt retrieval remains an authorized endpoint even when the agent provides its link.'),
code('app/server.py','token=self.token()',12),
h('5.2.2 Password and Session Storage (service.py):'),
p('Passwords use salted PBKDF2-HMAC-SHA256 with 600,000 iterations. Only session-token hashes are stored. Cookies are HttpOnly and SameSite=Strict. The local server binds to loopback; production hosting requires a separate HTTPS deployment.'),
code('app/service.py','def password_hash(',5))

page(None,'',
h('5.2.3 Database and Additive Migration (service.py):'),
p('SQLite foreign keys are enabled for each connection. Agent task state and serialized action/guide fields are added when absent, preserving existing student records, fees and payment attempts. New installations declare the same fields in schema.sql.'),
code('app/service.py','for table,column,definition',7),
h('5.2.4 Text Features and TF-IDF (nlp.py):'),
p('The language engine lowercases input, extracts alphanumeric tokens, removes common stop words and constructs unigram/bigram counts. Policy documents and intent examples are ranked with normalized sparse TF-IDF vectors.'),
code('app/nlp.py','def features(',4),
literal('tf(t,d) = 1 + ln(count(t,d))\nidf(t) = ln((N + 1) / (df(t) + 1)) + 1\nw(t,d) = tf(t,d) * idf(t)\ncosine(q,d) = dot(L2_normalize(q), L2_normalize(d))'),
p('Policy answers use the selected maintained document only when its cosine score reaches 0.16. The account exemplar route uses a separate 0.28 threshold. These values are implementation settings, not calibrated confidence probabilities. Payment-mode terms can be expanded to the maintained payment-methods topic, improving retrieval while retaining the stored policy as the answer source.'))

page(None,'',
h('5.2.5 Learned Task Classification (agent.py):'),
p('The task model is fitted from 80 labelled training examples across 12 classes: fees, history, profile, dashboard, pay, receipt, allotment, students, ledger, policies, audit and answer. Sparse word/phrase counts estimate a multinomial Naive Bayes likelihood with Laplace smoothing and uniform class priors.'),
literal('count(t,c) = feature occurrences in examples of class c\nP(t | c) = (count(t,c) + 1) / (total(c) + |V|)\nscore(c,q) = sum(count(t,q) * ln(P(t | c)))\npredicted class = argmax_c score(c,q)'),
code('app/agent.py','bag=nlp.features(question)',14),
p('The request detector separates task wording from ordinary information questions. The learned class is accepted only when its matching-example cosine evidence reaches 0.18 and its mean log-score margin reaches 0.035. The answer class and unsupported requests do not execute an interface tool.'),
p('The model is deterministic and explainable. Its counts are learned from examples rather than hand-written separately for every command. It remains a small lexical classifier: unfamiliar wording and tasks outside the available portal can still require a fallback. The model does not generate free-form code or arbitrary tool arguments.'))

page(None,'',
h('5.2.6 Bounded Planning and Fee Preparation (agent.py):'),
p('A payment task first requires a student role. The planner recognizes the fee category and selects only currently pending allocations from the authenticated account. The resulting actions open Pending fees and populate its checkboxes; they do not submit the payment form.'),
code('app/agent.py',"if task=='pay':",12),
h('5.2.7 Browser Action Validation (app.js):'),
p('The browser permits only known page identifiers for the current role. Fee identifiers must be safe integers present in the refreshed pending-fee list. Unknown action types have no execution branch. Stored conversation history is rendered without applying its prior action list.'),
h('5.3 API Endpoints'),
table(['Method','Endpoint','Access','Purpose'],[
['POST','/api/login','Public','Authenticate and create a session.'],
['GET','/api/dashboard','Session','Current authorized account/portal records.'],
['POST','/api/chat','Session + CSRF','Question answering or bounded task planning.'],
['GET','/api/chat/history','Session','Owned conversation and guide history.']]))

page(None,'',
table(['Method','Endpoint','Access','Purpose'],[
['POST','/api/logout','Session + CSRF','Revoke the current session.'],
['POST','/api/payment','Student + CSRF','Confirm a simulated payment attempt.'],
['GET','/api/receipt/:id','Owner/admin','Download a completed-payment PDF.'],
['POST','/api/admin/fee','Admin + CSRF','Assign an illustrative fee.'],
['POST','/api/admin/student','Admin + CSRF','Create a student account.'],
['POST','/api/admin/policy','Admin + CSRF','Maintain the policy knowledge base.'],
['GET','/api/admin/export','Admin','Download the fee ledger CSV.']]),
h('5.4 Agent Actions and Task State'),
table(['Action or state','Behavior'],[
['navigate','Open an allowed portal page; no external URL is accepted.'],
['select_fees','Select owned pending allocations for review.'],
['clear_selection','Clear the browser selection when the task is cancelled.'],
['Payment guide','Keep selected fee IDs in the current session; recheck before continuing.'],
['Receipt discovery','Return only completed owned payments; the download endpoint checks access again.'],
['Administrator guide','Open a permitted form and show its workflow steps.'],
['Conversation history','Persist answers, action data, links and guides without replaying actions.']]),
p('The assistant does not expose a tool for arbitrary SQL, script execution, external navigation, payment submission or administrator record changes. The user completes those changes through the authenticated portal controls. A request naming another student\'s register number is not used as a tool argument for student-account actions.'))

page(None,'',
h('5.5 Code Structure'),
literal('NEC FEE BOT/\n  app/\n    server.py         HTTP routes and security\n    service.py        Authorized account and agent services\n    agent.py          Learned task model and bounded plans\n    nlp.py            Features, account intents and TF-IDF\n    schema.sql        SQLite schema and constraints\n    static/           HTML, CSS, JavaScript and college assets\n  tests/              Service, HTTP and agent regression tests\n  scripts/            Evaluation, capture and report generation\n  data/               Independent local runtime data\n  requirements.txt\n  run.ps1'),
h('5.6 Code Screenshots:'),
p('The following screenshots display the actual project files and source extracts in the source code viewer.'),
h('(i) Project Files and Database Schema'),
figure('code_folder','Figure 5.1: Project file tree and current SQLite schema.',230))

page(None,'',
h('(ii) HTTP Routes and Security Checks (server.py)'),
figure('code_server','Figure 5.2: Current authenticated HTTP and receipt routes.',205),
h('(iii) Learned Task Model and Browser Tools'),
figure('code_model','Figure 5.3: Learned task prediction, evidence and acceptance thresholds.',245),
p('The task model is in app/agent.py. The client tool executor in app/static/app.js separately validates page and fee identifiers before applying the returned actions.'))

page(None,'',
h('5.7 Implementation Details:'),
b('Environment Setup: Install Python, create a virtual environment and install requirements.txt. The offline model uses Python standard-library mathematics and feature counters; ReportLab is required for PDF receipts.'),
literal('python -m venv .venv\n.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n.venv\\Scripts\\python.exe -m app.server'),
b('Running the Application: Open http://127.0.0.1:8765. On first start, the local demonstration generates random student/admin passwords in data/demo_credentials.json. Existing accounts and fee data are preserved on later starts.'),
b('Agent Operation: Ask a question or request a task. For example, "Could you navigate to my profile?" opens the profile, while "Help me pay tuition" opens Pending fees and selects the owned unpaid tuition allocation. The assistant remains available on the destination page.'),
b('Task Confirmation: Review selected fees and use Proceed to demo payment. The ordinary payment dialog controls the final outcome. Administrator guides similarly stop at the normal form controls.'),
b('Testing: The automated suite contains 43 passing regression tests. The updated browser capture verifies navigation, selection, confirmation, receipt download, role denial, administrator guidance and mobile layout against an isolated temporary dataset.'),
literal('.venv\\Scripts\\python.exe -m unittest discover -s tests -v\nnode --check app/static/app.js\n.venv\\Scripts\\python.exe scripts/evaluate_ai_agent.py'),
p('The browser captures and diagnostic evaluation use separate temporary databases. They do not settle fees or change accounts in the user\'s regular demonstration database. Runtime credentials and database files are excluded from the source package.'))

page(6,'OUTPUT SCREENSHOTS',
p('The following screenshots show the updated working application with an isolated academic demonstration dataset.'),
figure('01_login','Figure 6.1: Student and administrator sign-in page.',230),
figure('02_dashboard','Figure 6.2: Student overview with assigned and pending fees.',230))

page(None,'',
figure('03_auto_profile','Figure 6.3: Agent automatically opens My profile from a paraphrased request.',265),
figure('04_payment_agent','Figure 6.4: Agent opens Pending fees and selects tuition for review.',265))

page(None,'',
figure('06_receipt_agent','Figure 6.5: Agent finds the latest completed-payment receipt.',265),
figure('08_admin_guide','Figure 6.6: Administrator fee-allotment navigation and task guidance.',265))

page(None,'',
h('6.1 Model Evaluation Results'),
p('The learned task model was checked using 40 authored development requests covering navigation, payment preparation, receipt discovery, information answers, role denial, blocked instructions and cancellation. The phrases are absent verbatim from the 80 training examples, but the diagnostic set was reused during development. It is not an independently collected or untouched test set.'),
table(['Metric','Measured value','Remarks'],[
['Training examples / classes',f"{E['training_examples']} / {E['training_labels']}",'Labelled task and information utterances.'],
['Diagnostic requests / correct',f"{E['requests']} / {E['correct']}",'Local development diagnostic.'],
['Outcome accuracy',f"{E['accuracy']*100:.2f}%",'Final tool or answer outcome.'],
['Macro precision',f"{E['macro_precision']*100:.2f}%",'Mean across observed outcome labels.'],
['Macro recall',f"{E['macro_recall']*100:.2f}%",'Mean across observed outcome labels.'],
['Macro F1-score',f"{E['macro_f1']:.4f}",'Class-balanced diagnostic summary.'],
['Regression suite','43 passed','Temporary-database service and HTTP checks.'],
['Browser workflows','7 passed','Actual student/admin interface verification.']]),
h('Interpretation and Limits'),
p('All 40 diagnostic outcomes matched their expected result in the current build. This result demonstrates those specific authored cases, not 100% general accuracy. The limited vocabulary, small training set and repeated development use can make the diagnostic optimistic. Generalization requires independently labelled student requests, separate validation-only threshold tuning and an untouched test set.'),
p('ROC-AUC and binary false-positive/false-negative rates are not reported because the evaluation combines multiple task and answer outcomes rather than a binary calibrated probability model. Similarity scores remain relevance evidence, not a percentage guarantee of correctness.'))

page(7,'CONCLUSION',
h('7.1 Summary of the Project:'),
p('NEC Fee Assist has been implemented as an AI-assisted fee portal that connects natural language questions and task requests with authenticated account information and visible portal workflows. Its learned task classifier, TF-IDF retrieval engine, bounded planner and responsive browser interface work together to produce useful answers and controlled actions.'),
p('The assistant now goes beyond a text-only question-answer workflow. It can open relevant pages, select a requested fee category, retain task guidance across navigation, continue or cancel a task and find a protected receipt. The student remains responsible for confirming a simulated payment in the normal form.'),
h('Key achievements include:'),
b('A learned multinomial Naive Bayes task model trained from 80 labelled examples across 12 classes.'),
b('Grounded account answers and maintained-policy retrieval with explicit sources and fallback behavior.'),
b('Automatic page navigation and owned pending-fee selection through a fixed interface tool registry.'),
b('Persistent task guidance, session-scoped continuation and cancellation with state rechecks.'),
b('Role and ownership enforcement, independent browser validation and protected receipt access.'),
b('43 passing regression tests, seven browser workflow checks and a documented 40-request development diagnostic.'),
h('7.2 Contributions to the Field'),
p('The project demonstrates how a small classical AI model can be combined with task tools without granting unrestricted authority to language input. It provides practical laboratory exposure to feature representation, probabilistic learning, retrieval, planning, validation and evidence-based evaluation within an everyday student workflow.'))

page(None,'',
h('7.3 Limitations and Future Work'),
b('Language Coverage: The current model is lexical and English-only. Unfamiliar wording, spelling errors and multi-intent requests can produce an abstention or incorrect task prediction. Larger, independently labelled request datasets are needed.'),
b('Evaluation Independence: The authored diagnostic is reused during development. Future work should separate training, validation and untouched testing, and measure false tool activations as well as correct task completion.'),
b('Semantic Understanding: Semantic embeddings or an optional language model could broaden paraphrase handling. Any replacement must retain the same allow-listed tools, role checks and confirmation boundaries.'),
b('Dialogue Planning: Current task state supports narrow payment, receipt and administrator guides. Richer workflows need explicit progress observations, recovery paths and additional evaluation.'),
b('Production Infrastructure: The loopback Python HTTP server, local SQLite dataset and demonstration accounts are laboratory components. Production use requires approved identity integration, HTTPS, a suitable application server, backups and account lifecycle controls.'),
b('Real Payments: The application simulates payment outcomes. Real gateway orders, provider confirmation, reconciliation and operational controls must be implemented separately before accepting money.'),
h('7.4 Impact'),
b('Reduces menu searching by connecting a natural language request to its destination page.'),
b('Helps students prepare fee tasks while keeping confirmation visible and controlled.'),
b('Demonstrates how learned intent selection can be combined with grounded data and constrained tools.'),
b('Provides a reproducible educational example of AI-assisted task execution and responsible evaluation.'))

page(None,'',
h('7.5 Final Remarks'),
p('The project shows that a fee assistant can help users act as well as answer their questions. By combining a learned task classifier with a bounded planner, authorized account retrieval and direct interface navigation, NEC Fee Assist links conversational intent to practical portal workflows. Its explicit tool set and confirmation boundaries keep the behavior inspectable and its limits clear. Further language evaluation and production integration can build on this working academic foundation.'),
('final_rubric',None))

assert len(PAGES)==24

