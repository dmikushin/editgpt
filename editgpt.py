from gi.repository import GObject, Gedit, Gio, Gtk
import os

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
        
        # Determine the path to the UI file
        script_dir = os.path.dirname(__file__)
        ui_file_path = os.path.join(script_dir, "editgpt.ui")
        
        # Load the UI file content
        builder.add_from_file(ui_file_path)

        dialog = builder.get_object("EditGPTDialog")
        dialog.set_transient_for(self.window)
        
        # Create a header bar and set the title
        header_bar = Gtk.HeaderBar()
        header_bar.set_title("Edit with GPT")
        header_bar.set_show_close_button(True)
        dialog.set_titlebar(header_bar)

        # Set the minimum width to 1/3 of the parent window's width
        parent_width = self.window.get_size()[0]
        dialog.set_default_size(parent_width // 3, -1)

        text_view = builder.get_object("text_view")

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            buffer = text_view.get_buffer()
            start_iter, end_iter = buffer.get_bounds()
            new_text = buffer.get_text(start_iter, end_iter, True)

            # Get the current document
            document = self.window.get_active_document()
            if document:
                # Get the current selection bounds
                if document.get_has_selection():
                    start, end = document.get_selection_bounds()
                else:
                    # Select the entire document if no selection
                    start = document.get_start_iter()
                    end = document.get_end_iter()

                # Replace the selected text with the new text
                document.begin_user_action()
                document.delete(start, end)
                document.insert(start, new_text)
                document.end_user_action()

        dialog.destroy()

class EditGPTPlugin(GObject.Object, Gedit.AppActivatable):
    __gtype_name__ = "EditGPTPlugin"
    app = GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.app.set_accels_for_action("win.editgpt", [
            "<Control>G"
        ])
        # self.menu_ext = self.extend_menu("tools-section")
        # item = Gio.MenuItem.new("EditGPT", "win.editgpt")
        # self.menu_ext.prepend_menu_item(item)

    def do_deactivate(self):
        self.app.set_accels_for_action("win.editgpt", [])
        # self.menu_ext = None

    def do_update_state(self):
        pass
