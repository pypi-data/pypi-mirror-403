import psycopg

from apsfuncs.Toolbox.GlobalTools import BlackBoard

# Establish a connection to the PostgreSQL database
def get_db_connection(host, port, database, user):
    # Set up link to black board for logger
    bb = BlackBoard.instance()
    try:
        connection = psycopg.connect(
            host=host,
            port=port,
            dbname=database,
            user=user,
            connect_timeout=5
        )
        return connection
    except Exception as e:
        bb.logger.error("Database connection failed: " + str(e))
        return None
    
# Function to ensure a username and program name are valid in the database, return the ids for subsequent use
def get_user_program_ids(conn, username, program_name):
    with conn.cursor() as cur:
        # Insert user if not exists
        cur.execute("""
            INSERT INTO users (username)
            VALUES (%s)
            ON CONFLICT (username) DO NOTHING
            RETURNING id
        """, (username,))
        user_row = cur.fetchone()
        if user_row:
            user_id = user_row[0]
        else:
            # User exists, get id
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_id = cur.fetchone()[0]

        # Insert program if not exists
        cur.execute("""
            INSERT INTO programs (program_name)
            VALUES (%s)
            ON CONFLICT (program_name) DO NOTHING
            RETURNING id
        """, (program_name,))
        program_row = cur.fetchone()
        if program_row:
            program_id = program_row[0]
        else:
            # Program exists, get id
            cur.execute("SELECT id FROM programs WHERE program_name = %s", (program_name,))
            program_id = cur.fetchone()[0]

        return user_id, program_id
    
# Function to write a crash report entry to the database
def write_crash_report_entry(conn, user_id, program_id, log_file_path, user_comments, version):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO crash_reports (user_id, program_id, log_file_path, user_comments, version_string)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, program_id, log_file_path, user_comments, version))
    conn.commit()

# Function to write a user feedback entry to the database
def write_user_feedback_entry(conn, user_id, program_id, feedback_file_path, version):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO user_feedback (user_id, program_id, feedback_file_path, version_string)
            VALUES (%s, %s, %s, %s)
        """, (user_id, program_id, feedback_file_path, version))
    conn.commit()