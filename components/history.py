import os

class EditGPTHistory:
    def __init__(self):
        self.history_file = os.path.expanduser("~/.config/gedit/editgpt_last_prompt.txt")

    def save_prompt(self, prompt):
        with open(self.history_file, 'w') as file:
            file.write(prompt)

    def load_last_prompt(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as file:
                return file.read()
        return ""