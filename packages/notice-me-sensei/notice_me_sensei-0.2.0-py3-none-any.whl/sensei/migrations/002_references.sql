-- References table for storing study materials metadata

CREATE TABLE IF NOT EXISTS "references" (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    authors TEXT,
    url TEXT,
    file_path TEXT,
    content_type TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- Full-text search virtual table for references
-- Uses FTS5 for efficient text search
CREATE VIRTUAL TABLE IF NOT EXISTS references_fts USING fts5(
    title, description, authors,
    content='references', content_rowid='rowid'
);

-- Triggers to keep FTS index in sync with references table
CREATE TRIGGER IF NOT EXISTS references_ai AFTER INSERT ON "references" BEGIN
    INSERT INTO references_fts(rowid, title, description, authors)
    VALUES (new.rowid, new.title, new.description, new.authors);
END;

CREATE TRIGGER IF NOT EXISTS references_ad AFTER DELETE ON "references" BEGIN
    INSERT INTO references_fts(references_fts, rowid, title, description, authors)
    VALUES ('delete', old.rowid, old.title, old.description, old.authors);
END;

CREATE TRIGGER IF NOT EXISTS references_au AFTER UPDATE ON "references" BEGIN
    INSERT INTO references_fts(references_fts, rowid, title, description, authors)
    VALUES ('delete', old.rowid, old.title, old.description, old.authors);
    INSERT INTO references_fts(rowid, title, description, authors)
    VALUES (new.rowid, new.title, new.description, new.authors);
END;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_references_content_type ON "references"(content_type);
CREATE INDEX IF NOT EXISTS idx_references_created_at ON "references"(created_at);
