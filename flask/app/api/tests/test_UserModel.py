import unittest
import testing.postgresql
from sqlalchemy import create_engine
import psycopg2


class TestUserLogin(unittest.TestCase):


    # def __init__(self, postgresql, engine):
    #     self.postgresql = testing.postgresql.Postgresql(port=7654)  
    #     self.engine = create_engine(postgresql.url())


    def test_setUp(self):
        """
        Setup a testing psql database called users, takes id, username and email. 
        """
        self.postgresql = testing.postgresql.Postgresql(port=7654)  
        with self.postgresql as postgresql:
            engine = create_engine(postgresql.url())
            engine.execute("CREATE TABLE USERS (id INTEGER NOT NULL, name VARCHAR, email VARCHAR, PRIMARY KEY (id));")
            engine.execute("INSERT INTO USERS (id, name, email) VALUES (1, 'test_user', 'test@google.com')")
            result = engine.execute('SELECT * FROM USERS')

            # for _r in result:
            #     print(_r)

            self.postgresql.stop()

    
    def test_authenticate(self):
        """
        Return True if this email/password combo exists in the users database
        """

        self.postgresql = testing.postgresql.Postgresql(port=7654) 
        with self.postgresql as postgresql:
            engine = create_engine(postgresql.url())
            engine.execute("CREATE TABLE USERS (id INTEGER NOT NULL, name VARCHAR, email VARCHAR, PRIMARY KEY (id));")
            engine.execute("INSERT INTO USERS (id, name, email) VALUES (1, 'test_user', 'test@google.com')")
            result = engine.execute("SELECT EMAIL FROM USERS WHERE ID=1")
            print("result is:")
            for _r in result:
                print(_r)
                self.assertEqual(_r[0], 'test@google.com')

            self.postgresql.stop()
     

    def test_tearDown(self):
        """
        Stop using the test database.
        """
        self.postgresql = testing.postgresql.Postgresql(port=7654)  
        self.postgresql.stop()




if __name__ == '__main__':
    unittest.main()