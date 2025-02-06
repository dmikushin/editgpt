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

    async def generate_text_async(self, prompt, input, document, start_offset):
        try:
            document_ref = weakref.ref(document)
            process = await asyncio.create_subprocess_exec(
                'sgpt', prompt,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Send the input string to the process
            process.stdin.write(input.encode())
            await process.stdin.drain()
            process.stdin.close()

            async def read_stream(stream, callback):
                while True:
                    line = await stream.read(1)  # Read one byte at a time
                    if line:
                        callback(line.decode())
                    else:
                        break

            def handle_stdout(token):
                nonlocal start_offset
                if document_ref() is not None:
                        GLib.idle_add(self.insert_text, document, start_offset, token)
                        start_offset += len(token)

            def handle_stderr(token):
                print(token)

            # Read stdout and stderr concurrently
            await asyncio.gather(
                read_stream(process.stdout, handle_stdout),
                read_stream(process.stderr, handle_stderr))
        except Exception as e:
            print(f"Failed to execute prompt: {e}")

    def insert_text(self, document, start_offset, token):
        document.begin_user_action()
        start_iter = document.get_iter_at_offset(start_offset)
        document.insert(start_iter, token)
        document.end_user_action()
        return False  # Stop the idle function

    def dispatch_async_task(self, prompt, input, document, start_offset):
        # Schedule the coroutine to run in the background
        asyncio.run_coroutine_threadsafe(
            self.generate_text_async(prompt, input, document, start_offset),
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
        text_buffer = text_view.get_buffer()

        dialog.show_all()
        response = dialog.run()

        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            document = self.window.get_active_document()
            if document:
                if document.get_has_selection():
                    start_iter, end_iter = document.get_selection_bounds()
                else:
                    start_iter = document.get_start_iter()
                    end_iter = document.get_end_iter()

                document_text = document.get_text(start_iter, end_iter, True)

                start_offset = start_iter.get_offset()

                document.begin_user_action()
                document.delete(start_iter, end_iter)
                document.end_user_action()

                # Extract text from the Gtk.TextBuffer
                start_iter = text_buffer.get_start_iter()
                end_iter = text_buffer.get_end_iter()
                prompt_text = text_buffer.get_text(start_iter, end_iter, True)

                # Use the global EditGPTServer instance
                edit_gpt_server.dispatch_async_task(prompt_text, document_text, document, start_offset)

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
