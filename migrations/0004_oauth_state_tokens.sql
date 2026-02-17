-- Create oauth_state_tokens table for persistent OAuth state management
-- This prevents CSRF attacks and handles server restarts during OAuth flow

CREATE TABLE IF NOT EXISTS oauth_state_tokens (
    token VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    provider VARCHAR(32) NOT NULL,
    redirect_url VARCHAR(512)
);

-- Create index on created_at for faster cleanup of expired tokens
CREATE INDEX IF NOT EXISTS idx_oauth_state_tokens_created_at ON oauth_state_tokens(created_at);

-- Add a comment for the table
COMMENT ON TABLE oauth_state_tokens IS 'Stores OAuth state tokens for CSRF protection and session management';

-- Add comments for columns
COMMENT ON COLUMN oauth_state_tokens.token IS 'The unique state token';
COMMENT ON COLUMN oauth_state_tokens.created_at IS 'When the token was created';
COMMENT ON COLUMN oauth_state_tokens.provider IS 'OAuth provider (e.g., google, github)';
COMMENT ON COLUMN oauth_state_tokens.redirect_url IS 'Optional redirect URL to return to after OAuth flow';

-- Create a function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM oauth_state_tokens 
    WHERE created_at < (NOW() - INTERVAL '10 minutes');
END;
$$ LANGUAGE plpgsql;

-- Create a comment for the function
COMMENT ON FUNCTION cleanup_expired_oauth_tokens() IS 'Cleans up OAuth state tokens older than 10 minutes';
