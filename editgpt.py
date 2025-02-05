import asyncio
from gi.repository import GObject, Gedit, Gio, Gtk, GLib
import os
import threading
import weakref

class EditGPTServer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EditGPTServer, cls).__new__(cls)
            try:
                cls._instance.loop = asyncio.get_event_loop()
            except RuntimeError:
                cls._instance.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(cls._instance.loop)

            if not cls._instance.loop.is_running():
                threading.Thread(target=cls._instance.start_event_loop, args=(cls._instance.loop,), daemon=True).start()

        return cls._instance

    def start_event_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def generate_text_async(self, prompt, document, start):
        # Use a weak reference to the document to check if it's still open
        document_ref = weakref.ref(document)
        for token in ["Hello", " ", "world", "!"]:
            await asyncio.sleep(2)

            # Check if the document is still open
            if document_ref() is None:
                # Document is closed, cancelling task
                return

            GLib.idle_add(self.insert_text, prompt, document, start, token)

    def insert_text(self, prompt, document, start, token):
        document.begin_user_action()
        document.insert(start, token)
        document.end_user_action()
        start.forward_chars(len(token))
        return False  # Stop the idle function

    def dispatch_async_task(self, prompt, document, start):
        # Schedule the coroutine to run in the background
        asyncio.run_coroutine_threadsafe(
            self.generate_text_async(prompt, document, start),
            self.loop)

# Create a global instance of EditGPTServer
edit_gpt_server = EditGPTServer()

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
        prompt = text_view.get_buffer()

        dialog.show_all()
        response = dialog.run()

        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            document = self.window.get_active_document()
            if document:
                if document.get_has_selection():
                    start, end = document.get_selection_bounds()
                else:
                    start = document.get_start_iter()
                    end = document.get_end_iter()

                document.begin_user_action()
                document.delete(start, end)
                document.end_user_action()

                # Use the global EditGPTServer instance
                edit_gpt_server.dispatch_async_task(prompt, document, start)

class EditGPTPlugin(GObject.Object, Gedit.AppActivatable):
    __gtype_name__ = "EditGPTPlugin"
    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.app.set_accels_for_action("win.editgpt", [
            "<Control>G"
        ])

    def do_deactivate(self):
        self.app.set_accels_for_action("win.editgpt", [])

    def do_update_state(self):
        pass
