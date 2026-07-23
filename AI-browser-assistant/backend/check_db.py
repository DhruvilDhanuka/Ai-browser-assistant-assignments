import sqlite3

con = sqlite3.connect("Users.db")
row = con.execute(
    "SELECT status FROM commandsAndStatuses ORDER BY task_id DESC LIMIT 1"
).fetchone()
print(row)
