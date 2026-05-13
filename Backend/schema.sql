DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS triage_summaries CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS staff_users CASCADE;



CREATE TABLE staff_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'doctor', 'nurse')),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial users for testing (These are already verified)
-- (Passwords will be handled by the Python seeding script)
INSERT INTO staff_users (username, hashed_password, role, is_verified) 
VALUES ('taha', 'placeholder', 'doctor', TRUE),
       ('haad', 'placeholder', 'nurse', TRUE),
       ('admin_user', 'placeholder', 'admin', TRUE)
ON CONFLICT (username) DO NOTHING;

-- 0. Flat Data Collection (The new requirement)
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_input TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1. Patients Table
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Chat Sessions Table
CREATE TABLE chat_sessions (
    session_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- 3. Messages Table
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    sender_type VARCHAR(10) CHECK (sender_type IN ('Human', 'AI')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- 4. Triage Summaries Table
CREATE TABLE triage_summaries (
    summary_id SERIAL PRIMARY KEY,
    session_id INT UNIQUE NOT NULL,
    chief_complaint TEXT,
    duration TEXT,
    severity TEXT,
    medical_history TEXT,
    is_critical BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_summary FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);


-- Index for extremely fast message retrieval for active chat sessions
CREATE INDEX idx_messages_session_id ON messages(session_id);

-- Index to quickly find all sessions belonging to a specific patient
CREATE INDEX idx_sessions_patient_id ON chat_sessions(patient_id);


-- Stored Procedure: Automatically close a chat session when a summary is generated
CREATE OR REPLACE FUNCTION finalize_triage_session()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the chat_session to inactive so no further messages go to it
    UPDATE chat_sessions
    SET is_active = FALSE
    WHERE session_id = NEW.session_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to execute the stored procedure AFTER an INSERT into triage_summaries
CREATE TRIGGER trigger_finalize_session
AFTER INSERT ON triage_summaries
FOR EACH ROW
EXECUTE FUNCTION finalize_triage_session();

-- TRIGGER 2: Automatically flag a session as CRITICAL based on keywords
CREATE OR REPLACE FUNCTION assess_critical_condition()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for critical keywords (Case-Insensitive)
    IF NEW.chief_complaint ~* '(chest pain|difficulty breathing|unconscious|bleeding|stroke|seizure|heart attack|suicide|poison)' THEN
        NEW.is_critical := TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_assess_triage
BEFORE INSERT ON triage_summaries
FOR EACH ROW
EXECUTE FUNCTION assess_critical_condition();



-- Create the Audit Log table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    action_type VARCHAR(20),
    record_id INT,
    old_value TEXT,
    new_value TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to log activity
CREATE OR REPLACE FUNCTION log_summary_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (table_name, action_type, record_id, new_value)
        VALUES ('triage_summaries', 'INSERT', NEW.summary_id, NEW.chief_complaint);
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, action_type, record_id, old_value, new_value)
        VALUES ('triage_summaries', 'UPDATE', NEW.summary_id, OLD.chief_complaint, NEW.chief_complaint);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_summary_audit
AFTER INSERT OR UPDATE ON triage_summaries
FOR EACH ROW
EXECUTE FUNCTION log_summary_activity();




-- Function to close old active sessions automatically
CREATE OR REPLACE FUNCTION clean_stale_sessions()
RETURNS TRIGGER AS $$
BEGIN
    -- If a new session is being created for a patient, 
    -- find any OTHER active sessions for that patient that are older than 2 hours and close them.
    UPDATE chat_sessions
    SET is_active = FALSE
    WHERE patient_id = NEW.patient_id
      AND is_active = TRUE
      AND created_at < NOW() - INTERVAL '2 hours';
      
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cleanup_old_sessions
BEFORE INSERT ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION clean_stale_sessions();



-- Returns weekly performance stats
CREATE OR REPLACE FUNCTION get_analytics_summary()
RETURNS TABLE(avg_triage_minutes FLOAT, total_sessions INT, critical_count INT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        AVG(EXTRACT(EPOCH FROM (s.created_at - c.created_at))/60)::FLOAT,
        COUNT(c.session_id)::INT,
        COUNT(CASE WHEN s.is_critical THEN 1 END)::INT
    FROM chat_sessions c
    JOIN triage_summaries s ON c.session_id = s.session_id
    WHERE c.created_at > NOW() - INTERVAL '7 days'
      AND (EXTRACT(EPOCH FROM (s.created_at - c.created_at))/60) < 120;
END; $$ LANGUAGE plpgsql;

-- Returns frequency distribution of common symptoms
CREATE OR REPLACE FUNCTION get_symptom_metrics()
RETURNS TABLE(symptom TEXT, occurrence_count INT) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Headache'::TEXT, COUNT(*)::INT FROM triage_summaries WHERE chief_complaint ~* 'headache'
    UNION ALL
    SELECT 'Fever'::TEXT, COUNT(*)::INT FROM triage_summaries WHERE chief_complaint ~* 'fever'
    UNION ALL
    SELECT 'Cough'::TEXT, COUNT(*)::INT FROM triage_summaries WHERE chief_complaint ~* 'cough'
    UNION ALL
    SELECT 'Pain'::TEXT, COUNT(*)::INT FROM triage_summaries WHERE chief_complaint ~* 'pain'
    UNION ALL
    SELECT 'Breathing Difficulty'::TEXT, COUNT(*)::INT FROM triage_summaries WHERE chief_complaint ~* 'breathing|breath';
END; $$ LANGUAGE plpgsql;

-- Enable RLS on sensitive tables
ALTER TABLE triage_summaries ENABLE ROW LEVEL SECURITY;

-- 1. Create a Policy: Only DOCTORS and ADMINS can see summaries
CREATE POLICY doctor_admin_view_summaries ON triage_summaries
    FOR SELECT
    USING (current_setting('app.current_user_role', true) IN ('doctor', 'admin'));

-- 2. Create a Policy: Only DOCTORS and ADMINS can insert/modify summaries
CREATE POLICY doctor_admin_modify_summaries ON triage_summaries
    FOR INSERT
    WITH CHECK (current_setting('app.current_user_role', true) IN ('doctor', 'admin'));

-- Note: Nurses cannot see summaries because no policy grants them SELECT access.
-- By default, RLS is 'deny all' unless a policy exists.
