from gi.repository import GObject, Gedit, Gio, Gtk

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
        dialog = Gtk.Dialog(title="Edit with ChatGPT", transient_for=self.window, flags=0)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        box = dialog.get_content_area()
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        box.add(text_view)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            buffer = text_view.get_buffer()
            start_iter, end_iter = buffer.get_bounds()
            text = buffer.get_text(start_iter, end_iter, True)
            print("Text entered:", text)

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
