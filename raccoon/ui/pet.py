import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib
import cairo


class GizmoPet(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.pet_width = 220
        self.pet_height = 164
        self.sprite_path = "assets/gizmo.png"

        self._bob_offset = 0
        self._bob_direction = 1

        self.setup_window()
        self.load_sprite()
        self.setup_canvas()
        self.apply_transparency()
        self.enable_drag()
        self.start_bob()

    # ── window ────────────────────────────────────────────────────────────────

    def setup_window(self):
        self.set_decorated(False)
        self.set_focusable(False)
        self.set_default_size(self.pet_width, self.pet_height)
        self.set_resizable(False)
        self.connect("close-request", self.on_close)

    def apply_transparency(self):
        css = b"window { background: transparent; }"
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_close(self, widget):
        self.get_application().quit()

    # ── sprite ────────────────────────────────────────────────────────────────

    def load_sprite(self):
        self.sprite = cairo.ImageSurface.create_from_png(self.sprite_path)
        self.sprite_w = self.sprite.get_width()
        self.sprite_h = self.sprite.get_height()

    # ── canvas ────────────────────────────────────────────────────────────────

    def setup_canvas(self):
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(self.pet_width, self.pet_height)
        self.canvas.set_draw_func(self.draw)
        self.set_child(self.canvas)

    def draw(self, area, cr, width, height):
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()

        scale_x = self.pet_width / self.sprite_w
        scale_y = self.pet_height / self.sprite_h
        cr.scale(scale_x, scale_y)

        bob_scaled = self._bob_offset / scale_y
        cr.set_source_surface(self.sprite, 0, bob_scaled)
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.paint()

    # ── drag ─────────────────────────────────────────────────────────────────

    def enable_drag(self):
        click = Gtk.GestureClick.new()
        click.connect("pressed", self.on_pressed)
        self.canvas.add_controller(click)

    def on_pressed(self, gesture, n_press, x, y):
        # get the underlying GDK surface and tell compositor to move it
        surface = self.get_surface()
        if surface:
            toplevel = surface.get_toplevel() if hasattr(surface, 'get_toplevel') else surface
            if hasattr(toplevel, 'begin_move'):
                # GTK4 Wayland way — hand movement to compositor
                seat = Gdk.Display.get_default().get_default_seat()
                device = seat.get_pointer()
                toplevel.begin_move(device, 1, int(x), int(y), 0)

    # ── state methods (wake.py calls these later) ─────────────────────────────

    def set_listening(self):
        print("🦝 Gizmo is listening...")

    def set_idle(self):
        print("🦝 Gizmo is idle...")

    # ── bob animation ─────────────────────────────────────────────────────────

    def start_bob(self):
        GLib.timeout_add(80, self._bob_step)

    def _bob_step(self):
        self._bob_offset += self._bob_direction
        if self._bob_offset >= 4 or self._bob_offset <= 0:
            self._bob_direction *= -1
        self.canvas.queue_draw()
        return True


class GizmoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.gizmo.pet")

    def do_activate(self):
        self.window = GizmoPet()
        self.window.set_application(self)
        self.window.present()


if __name__ == "__main__":
    app = GizmoApp()
    app.run()
