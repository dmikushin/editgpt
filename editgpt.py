from gi.repository import GObject, Gedit, Gtk

class MyPlugin(GObject.Object, Gedit.WindowActivatable):
   __gtype_name__ = "MyPlugin"
   window = GObject.Property(type=Gedit.Window)

   def __init__(self):
       super().__init__()

   def do_activate(self):
       self._insert_menu()

   def do_deactivate(self):
       self._remove_menu()

   def do_update_state(self):
       pass

   def _insert_menu(self):
       action = Gtk.Action(name="OpenDialog", label="Open Dialog", tooltip="Open a dialog", stock_id=None)
       action.connect("activate", self.on_action_activate)
       action_group = Gtk.ActionGroup(name="MyPluginActions")
       action_group.add_action_with_accel(action, "<Ctrl>G")
       self.window.get_ui_manager().insert_action_group(action_group)
       self._action_group = action_group

   def _remove_menu(self):
       self.window.get_ui_manager().remove_action_group(self._action_group)

   def on_action_activate(self, action):
       dialog = Gtk.Dialog(title="My Dialog", transient_for=self.window, flags=0)
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

