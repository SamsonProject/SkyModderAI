-- Add shared_load_orders table
CREATE TABLE IF NOT EXISTS shared_load_orders (
    id TEXT PRIMARY KEY,  -- Random URL-safe ID
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,  -- Links expire after 30 days
    game TEXT NOT NULL,
    game_version TEXT,
    masterlist_version TEXT,
    mod_list TEXT NOT NULL,  -- JSON array of mods
    analysis_results TEXT,   -- JSON of analysis results
    view_count INTEGER NOT NULL DEFAULT 0,
    last_viewed_at TIMESTAMP,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    user_email TEXT,  -- Optional: link to user who created it
    title TEXT,       -- Optional: user-provided title
    notes TEXT,       -- Optional: user-provided notes
    FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE SET NULL
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_shared_load_orders_id ON shared_load_orders(id);
CREATE INDEX IF NOT EXISTS idx_shared_load_orders_user_email ON shared_load_orders(user_email);
CREATE INDEX IF NOT EXISTS idx_shared_load_orders_expires ON shared_load_orders(expires_at);
