def _runSql(sql, data=None, type="select", printSql=False):
    """Run sql statement.

    Example:
    > result = _runSql("select * from users where email=%s", (email,))
    > [('jarnyc@unimelb.edu.au', 'dofdlfjlejjce', 'admin')]

    data should be a tuple, even if one element.
    type should be one of {"select","update"}

    Returns a list of tuples corresponding to the columns of the selection if type=="select".
    If type=="update", returns the number of rows affected by the update.

    If printSql is True, then the actual sql being executed will be printed
    """
    postgres_username = app.config['POSTGRES_USERNAME'] 
    postgres_password = app.config["POSTGRES_PASSWORD"]
    postgres_database_name = app.config["POSTGRES_DATABASE_NAME"]
    postgres_host = app.config["POSTGRES_HOST"]
    postgres_port = app.config["POSTGRES_PORT"]
    postgres_uri = app.config["PSQL_URI"]
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    mongo_uri = app.config["MONGO_URI"]

    if printSql:  # To see the actual sql executed, use mogrify:
        print(cursor.mogrify(sql, data))
        