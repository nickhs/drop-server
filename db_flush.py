import time
from core import db
from db_create import create_db


if __name__ == '__main__':
    print "This will destroy the database"
    print "Press CTRL+C immediately to abort this operation"
    time.sleep(5)
    print "Database drop started"
    db.drop_all()
    print "Databsae drop complete"
    create_db()
    print "Recreated database"
