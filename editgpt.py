from gi.repository import GObject, Gedit, Gio, Gtk, Gdk
from components.server import EditGPTServer
import os

# Create a global instance of EditGPTServer
try:
    editgpt_server = EditGPTServer()
except Exception as e:
    print(f"Failed tostart EditGPT server: {e}")

class EditGPTWindow(GObject.Object, Gedit.WindowActivatable):
    window = GObject.Property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.action = Gio.SimpleAction(name="editgpt")
        self.action.connect('activate', self.on_action_activate)
        self.window.add_action(self.action)

    def do_deactivate(self):
        self.window.remove_action("editgpt")

    def on_action_activate(self, action, parameter, user_data=None):
        builder = Gtk.Builder()
        script_dir = os.path.dirname(__file__)
        ui_file_path = os.path.join(script_dir, "editgpt.ui")
        builder.add_from_file(ui_file_path)

        dialog = builder.get_object("EditGPTDialog")
        dialog.set_transient_for(self.window)

        header_bar = Gtk.HeaderBar()
        header_bar.set_title("Edit with GPT")
        header_bar.set_show_close_button(True)
        dialog.set_titlebar(header_bar)

        parent_width = self.window.get_size()[0]
        dialog.set_default_size(parent_width // 3, -1)

        text_view = builder.get_object("text_view")
        text_buffer = text_view.get_buffer()

        # Load the last prompt
        last_prompt = editgpt_server.history.load_last_prompt()
        text_buffer.set_text(last_prompt)

        # Get the checkbox state
        generate_code_checkbox = builder.get_object("generate_code_checkbox")
        generate_code = generate_code_checkbox.get_active()

        # Connect key-press-event to handle Ctrl+Enter
        dialog.connect("key-press-event", self.on_key_press_event, dialog)

        dialog.show_all()
        response = dialog.run()

        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            document = self.window.get_active_document()
            if document:
                # Extract text from the Gtk.TextBuffer
                start_iter = text_buffer.get_start_iter()
                end_iter = text_buffer.get_end_iter()
                prompt_text = text_buffer.get_text(start_iter, end_iter, True)

                # Save the last prompt
                editgpt_server.history.save_prompt(prompt_text)

                if document.get_has_selection():
                    start_iter, end_iter = document.get_selection_bounds()
                else:
                    start_iter = document.get_start_iter()
                    end_iter = document.get_end_iter()

                # Add more settings
                prompt = {"text": prompt_text}
                if generate_code:
                    prompt['generate_only_code'] = True

                # Use the global EditGPTServer instance
                editgpt_server.jobs.dispatch_async_task(prompt, document, start_iter, end_iter)

    def on_key_press_event(self, widget, event, dialog):
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_Return:
            dialog.response(Gtk.ResponseType.OK)
            return True
        return False

class EditGPTPlugin(GObject.Object, Gedit.AppActivatable):
    __gtype_name__ = "EditGPTPlugin"
    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.app.set_accels_for_action("win.editgpt", [
            "<Control>R"
        ])

    def do_deactivate(self):
        self.app.set_accels_for_action("win.editgpt", [])

    def do_update_state(self):
        pass
