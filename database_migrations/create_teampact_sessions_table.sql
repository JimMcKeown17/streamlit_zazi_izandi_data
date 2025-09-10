-- Migration: Create teampact_nmb_sessions table
-- Description: Creates table to store TeamPact session data from API
-- Date: 2025-09-09

-- Create teampact_nmb_sessions table
CREATE TABLE IF NOT EXISTS teampact_nmb_sessions (
    -- Primary key and metadata
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data_refresh_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Original API identifiers (from CSV)
    attendance_id BIGINT,
    session_id BIGINT,
    participant_id BIGINT,
    user_id BIGINT,
    class_id BIGINT,
    program_id BIGINT,
    org_id BIGINT,
    
    -- Participant information
    participant_name VARCHAR(255),
    participant_firstname VARCHAR(255),
    participant_lastname VARCHAR(255),
    participant_gender INTEGER, -- 0=male, 1=female based on data
    
    -- Attendance information
    attendance_status VARCHAR(50),
    roll_call_pre_status VARCHAR(50),
    roll_call_post_status VARCHAR(50),
    is_flagged BOOLEAN,
    flag_reason TEXT,
    
    -- Session timing
    session_started_at TIMESTAMP WITH TIME ZONE,
    session_ended_at TIMESTAMP WITH TIME ZONE,
    check_in_time TIMESTAMP WITH TIME ZONE,
    total_duration_minutes DECIMAL(10,2),
    session_duration_seconds INTEGER,
    
    -- Class/Program information
    class_name VARCHAR(255),
    program_name VARCHAR(255),
    organisation_name VARCHAR(255),
    
    -- User/Teacher information
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    user_gender INTEGER,
    
    -- Session content and metrics
    session_text TEXT,
    attended_percentage DECIMAL(5,2),
    participant_total INTEGER,
    attended_total INTEGER,
    attended_male_total INTEGER,
    attended_female_total INTEGER,
    attended_male_percentage DECIMAL(5,2),
    attended_female_percentage DECIMAL(5,2),
    
    -- Location data
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Curriculum/Letters data
    letters_taught TEXT, -- Comma-separated list
    session_tag_ids TEXT, -- Comma-separated list
    session_tag_group_ids TEXT, -- Comma-separated list
    num_letters_taught INTEGER,
    
    -- Additional session metadata
    mobile_app_id VARCHAR(255),
    batch_id VARCHAR(255),
    rollcall_pre_present_count INTEGER,
    rollcall_post_present_count INTEGER,
    
    -- Class details
    class_description TEXT,
    target_attended_percentage VARCHAR(50),
    target_attended_female_percentage VARCHAR(50),
    
    -- Program details
    program_description TEXT,
    program_is_archived BOOLEAN,
    
    -- Timestamps from API
    record_created_at TIMESTAMP WITH TIME ZONE,
    record_updated_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_user_name ON teampact_nmb_sessions(user_name);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_program_name ON teampact_nmb_sessions(program_name);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_session_started_at ON teampact_nmb_sessions(session_started_at);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_session_id ON teampact_nmb_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_refresh_timestamp ON teampact_nmb_sessions(data_refresh_timestamp);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_attendance_id ON teampact_nmb_sessions(attendance_id);

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_user_started_at ON teampact_nmb_sessions(user_name, session_started_at);
CREATE INDEX IF NOT EXISTS idx_teampact_nmb_sessions_program_started_at ON teampact_nmb_sessions(program_name, session_started_at);

-- Create unique constraint on attendance_id to prevent duplicates
ALTER TABLE teampact_nmb_sessions ADD CONSTRAINT unique_attendance_id UNIQUE (attendance_id);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_teampact_nmb_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_teampact_nmb_sessions_updated_at
    BEFORE UPDATE ON teampact_nmb_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_teampact_nmb_sessions_updated_at();

-- Add comment to table
COMMENT ON TABLE teampact_nmb_sessions IS 'Stores session attendance data fetched from TeamPact API';
COMMENT ON COLUMN teampact_nmb_sessions.data_refresh_timestamp IS 'Timestamp when this batch of data was fetched from API';
COMMENT ON COLUMN teampact_nmb_sessions.attendance_id IS 'Original attendance record ID from TeamPact API';
COMMENT ON COLUMN teampact_nmb_sessions.session_id IS 'Session ID from TeamPact API';
