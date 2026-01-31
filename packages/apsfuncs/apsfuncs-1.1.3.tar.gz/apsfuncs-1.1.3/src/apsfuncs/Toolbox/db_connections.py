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
        # bb.logger.info("Database connection failed: " + str(e))
        print("Database connection failed: " + str(e))
        return None