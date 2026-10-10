PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','admin')),
 password_hash TEXT NOT NULL, department TEXT NOT NULL DEFAULT 'CSE', semester INTEGER NOT NULL DEFAULT 7
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), csrf TEXT NOT NULL,
 expires INTEGER NOT NULL, context TEXT NOT NULL DEFAULT '', agent_state TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS fees (
 id INTEGER PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), head TEXT NOT NULL,
 ledger TEXT NOT NULL, academic_year TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount>0),
 due_date TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','paid'))
);
CREATE INDEX IF NOT EXISTS idx_fees_owner ON fees(user_id,status);
CREATE TABLE IF NOT EXISTS payments (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), amount INTEGER NOT NULL CHECK(amount>0),
 status TEXT NOT NULL CHECK(status IN ('completed','failed','cancelled')), created_at TEXT NOT NULL,
 idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL, UNIQUE(user_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS payment_items (
 payment_id TEXT NOT NULL REFERENCES payments(id), fee_id INTEGER NOT NULL REFERENCES fees(id),
 amount INTEGER NOT NULL CHECK(amount>0), PRIMARY KEY(payment_id,fee_id)
);
CREATE TABLE IF NOT EXISTS settlements (
 fee_id INTEGER PRIMARY KEY REFERENCES fees(id), payment_id TEXT NOT NULL REFERENCES payments(id)
);
CREATE TABLE IF NOT EXISTS policies (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
 id INTEGER PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), question TEXT NOT NULL,
 answer TEXT NOT NULL, intent TEXT NOT NULL, source TEXT NOT NULL, score REAL NOT NULL, created_at TEXT NOT NULL,
 actions TEXT NOT NULL DEFAULT '[]', guide TEXT NOT NULL DEFAULT 'null', links TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL, created_at TEXT NOT NULL
);
