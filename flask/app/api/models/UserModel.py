"""
Module to handle user instances.

### Example Usage ###

import users
user = users.User()
user.create("john@google.com", "password")
user.update("john@google.com", password="new password", role=users.Role.admin)
print(user.role("john@google.com"))
> "admin"

### Database table ###
create table users (email varchar(255) not null primary key, password text, role varchar(20) not null)
"""

from . import _runSql, classproperty
import os, pandas, json
import psycopg2
from . import _runSql

# ----------------------------------------------------------
# Password hashing and verifying. From https://www.vitoshacademy.com/hashing-passwords-in-python/
# ----------------------------------------------------------

import hashlib, binascii, os
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password
    
# ----------------------------------------------------------
# Define a set of roles that users can be assigned to.
# ----------------------------------------------------------

class Role(object):
    @classproperty
    def user(self):
        return "user"

    @classproperty
    def admin(self):
        return "admin"

    @classproperty
    def annotator(self):
        return "annotator"

    @classproperty
    def uploader(self):
        return "uploader"


# ----------------------------------------------------------
# User class. Rather than working on a single user record, the class works mostly on the whole collection of records.
# ----------------------------------------------------------

class User(object):

    def __init__(self, email):
        self.email = email

    def exists(self, email):
        """Return true if user with this email already exists.
        """
        return len(_runSql("select * from users where email=%s", (email,)))>0

    def create(self, email, password, role=Role.user):
        """Create a new user. Returns 1 if successful.
        If email already exists, it doesn't create a new entry - just returns 0.
        """
        return 0 if self.exists(email) else _runSql("insert into users values (%s, %s, %s)", (email, hash_password(password), role), type="update")

    def role(self, email):
        """Return the role (string) this user holds in the database.
        Example:
        > user = User()
        > print(user.role("test@google.com")==user.Role.admin)
        """
        result = _runSql("select * from users where email=%s", (email,))
        if len(result)>0:
            return result[0][2]
        return None
    
    def allRoles(self):
        """Return all available roles as a list of strings.
        """
        return [Role.user, Role.annotator, Role.uploader, Role.admin]

    def authenticate(self, email, password):
        """Return True if this email/password combo exists in the users database
        """
        result = _runSql("select password from users where email=%s", (email,))
        return len(result)==1 and verify_password(result[0][0], password)

    def canAnnotate(self, email):
        """Return True if user with this email has annotator access, which means having one of the more previleged roles.
        """
        return self.role(email) in [Role.admin, Role.annotator, Role.uploader]

    def update(self, email, password, role):
        """Update the user with matching email with password and role. Blank or None password means no update of password is done.
        """
        if role not in self.allRoles():
            return 0
        if password is not None and password!="":
            return _runSql("update users set password=%s, role=%s where email=%s", (hash_password(password), role, email), type="update")
        else:
            return _runSql("update users set role=%s where email=%s", (role, email), type="update")

    def delete(self, email):
        """Delete user from database.
        """
        return _runSql("delete from users where email=%s", (email,), type="update")

    def userTable(self):
        """Return a pandas dataframe of all users.
        """
        import pandas
        result = _runSql("select * from users")
        return pandas.DataFrame(result, columns=["email", "password", "role"]).set_index("email")

# ----------------------------------------------------------
# Tests. eg: > nosetests -s dataportal/models/users.py:test_roles
# ----------------------------------------------------------
def test_user():
    # Create a new user, authenticate, check roles and delete
    user = User()
    assert user.create("test@google.com", "test")==1
    assert user.role("test@google.com")==Role.user
    assert user.authenticate("test@google.com", "test") is True
    assert user.canAnnotate("test@google.com") is False
    assert user.update("test@google.com", "", "annotator")==1
    assert user.canAnnotate("test@google.com") is True
    assert user.update("test@google.com", "new password", "annotator")==1
    assert user.authenticate("test@google.com", "test") is False
    assert user.authenticate("test@google.com", "new password") is True
    assert user.delete("test@google.com")==1

def test_userTable():
    print(User().userTable().head())

def test_other():
    user = User()
    print(_runSql("select * from users"))
