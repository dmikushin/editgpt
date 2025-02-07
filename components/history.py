import os
import sqlite3

class EditGPTHistory:
    def __init__(self):
        self._initialize_database()

    def _initialize_database(self):
        self.conn = sqlite3.connect(os.path.expanduser("~/.config/gedit/editgpt_history.db"))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                prompt TEXT
            )
        ''')
        self.conn.commit()

    def save_prompt(self, prompt):
        self.cursor.execute('INSERT INTO history (prompt) VALUES (?)', (prompt,))
        self.conn.commit()

    def close(self):
        self.conn.close()