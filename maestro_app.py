"""
UI Module for Maestro Servo Controller.
Handles the graphical user interface and user interactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from hardware import MockMaestroController
from domain import ServoManager

# UI Constants - Geometry & Styling
MAIN_WIN_GEO = "400x500"
SERVO_WIN_W = 250
SERVO_WIN_H = 150
MAIN_WIN_INPUT_AREA_WIDTH = 15
PAD_XS = 2
PAD_S = 5
PAD_M = 10
PAD_L = 15
W_SLIDER = 200
COLOR_SELECTED = "#97B7F8"
COLOR_DEFAULT = "#FFFFFF"

# UI Constants - Texts
TXT_APP_TITLE = "Maestro App"
TXT_GROUP_SETTINGS = "Servo settings"
TXT_GROUP_LIST = "Active servos"
TXT_LBL_NAME = "Name:"
TXT_LBL_STEP = "Jog Step (us):"
TXT_LBL_MIN = "Min Pos:"
TXT_LBL_MAX = "Max Pos:"
TXT_LBL_POS = "Position: {} us"
TXT_BTN_ADD = "+ Add servo"
TXT_BTN_SAVE = "Save Changes"
TXT_BTN_DEL = "X"
TXT_BTN_LEFT = "<-"
TXT_BTN_RIGHT = "->"

# UI Constants - Messages
MSG_WARN_TITLE = "No free channels"
MSG_WARN_TEXT = "All channels occupied."
MSG_INFO_TITLE = "Info"
MSG_INFO_SELECT = "Select a servo from the list first."
MSG_SAVE_TITLE = "Saved"
MSG_SAVE_TEXT = "Configuration for '{}' saved!"

# Servo Defaults
SERVO_DEF_NAME = "New Servo"
SERVO_DEF_STEP = 50
SERVO_DEF_MIN = 1000
SERVO_DEF_MAX = 2000


class ServoWindow(tk.Toplevel):
    """Floating window to manage a single servo."""

    def __init__(self, parent: tk.Tk, servo, manager: ServoManager) -> None:
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.servo = servo
        self.manager = manager
        self.title(self.servo.name)

        self.geometry(f"{SERVO_WIN_W}x{SERVO_WIN_H}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._build_ui()


    def _center_on_parent(self, width: int, height: int) -> None:
        """Centers the child window over the parent window."""
        self.update_idletasks()

        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (width // 2)
        pos_y = parent_y + (parent_height // 2) - (height // 2)

        self.geometry(f"+{pos_x}+{pos_y}")

    def _build_ui(self) -> None:
        """Constructs the UI elements for the servo window."""
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=PAD_L)

        self.btn_left = ttk.Button(btn_frame, text=TXT_BTN_LEFT, command=self.step_left)
        self.btn_left.pack(side=tk.LEFT, padx=PAD_S)

        self.btn_right = ttk.Button(btn_frame, text=TXT_BTN_RIGHT, command=self.step_right)
        self.btn_right.pack(side=tk.RIGHT, padx=PAD_S)

        self.lbl_position = ttk.Label(self, text=TXT_LBL_POS.format(self.servo.position))
        self.lbl_position.pack()

        self.slider = ttk.Scale(
            self,
            from_=self.servo.min_val,
            to=self.servo.max_val,
            orient=tk.HORIZONTAL,
            length=W_SLIDER
        )
        self.slider.set(self.servo.position)
        self.slider.config(command=self.on_slider_move)
        self.slider.pack(pady=PAD_S)

    def on_slider_move(self, value: str) -> None:
        """Handles slider movement and updates hardware."""
        pos = int(float(value))
        self.lbl_position.config(text=TXT_LBL_POS.format(pos))
        self.manager.set_servo_position(self.servo.channel, pos)

    def step_left(self) -> None:
        """Decreases servo position by the configured step."""
        current = self.slider.get()
        new_pos = max(self.servo.min_val, current - self.servo.step)
        self.slider.set(new_pos)

    def step_right(self) -> None:
        """Increases servo position by the configured step."""
        current = self.slider.get()
        new_pos = min(self.servo.max_val, current + self.servo.step)
        self.slider.set(new_pos)

    def hide_window(self) -> None:
        """Hides the window instead of destroying it."""
        self.withdraw()

    def show_window(self) -> None:
        """Brings the window back to the front."""
        self._center_on_parent(SERVO_WIN_W, SERVO_WIN_H)
        self.deiconify()
        self.lift()
        self.focus_force()


class MainWindow(tk.Tk):
    """Main application window for managing multiple servos."""

    def __init__(self, manager: ServoManager) -> None:
        super().__init__()
        self.manager = manager
        self.servo_windows = {}

        self.title(TXT_APP_TITLE)
        self.geometry(MAIN_WIN_GEO)

        self.selected_channel = None
        self.row_widgets = {}

        self.name_var = tk.StringVar(value=SERVO_DEF_NAME)
        self.step_var = tk.IntVar(value=SERVO_DEF_STEP)
        self.min_var = tk.IntVar(value=SERVO_DEF_MIN)
        self.max_var = tk.IntVar(value=SERVO_DEF_MAX)

        self._build_ui()
        self._load_servos()

    def _build_ui(self) -> None:
        """Constructs the main layout and property manager."""
        settings_group = ttk.LabelFrame(self, text=TXT_GROUP_SETTINGS)
        settings_group.pack(fill=tk.X, padx=PAD_M, pady=PAD_M)

        config_frame = ttk.Frame(settings_group)
        config_frame.pack(side=tk.LEFT, padx=PAD_M, pady=PAD_S)

        ttk.Label(config_frame, text=TXT_LBL_NAME).grid(
            row=0, column=0, sticky=tk.W, pady=PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.name_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=0, column=1, padx=PAD_S, pady=PAD_XS
        )

        ttk.Label(config_frame, text=TXT_LBL_STEP).grid(
            row=1, column=0, sticky=tk.W, pady=PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.step_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=1, column=1, padx=PAD_S, pady=PAD_XS
        )

        ttk.Label(config_frame, text=TXT_LBL_MIN).grid(
            row=2, column=0, sticky=tk.W, pady=PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.min_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=2, column=1, padx=PAD_S, pady=PAD_XS
        )

        ttk.Label(config_frame, text=TXT_LBL_MAX).grid(
            row=3, column=0, sticky=tk.W, pady=PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.max_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=3, column=1, padx=PAD_S, pady=PAD_XS
        )

        btn_frame = ttk.Frame(settings_group)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=PAD_S, pady=PAD_S)

        btn_add = ttk.Button(btn_frame, text=TXT_BTN_ADD, command=self.add_servo_ui)
        btn_add.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        btn_update = ttk.Button(btn_frame, text=TXT_BTN_SAVE, command=self.update_servo)
        btn_update.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        list_group = ttk.LabelFrame(self, text=TXT_GROUP_LIST)
        list_group.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_S)

        self.canvas = tk.Canvas(list_group, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_group, orient=tk.VERTICAL, command=self.canvas.yview)

        self.list_frame = tk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_frame_id, width=e.width)
        )

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event) -> None:
        """Handles mouse wheel scrolling inside the canvas."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_servo_ui(self) -> None:
        """Handles adding a new servo based on UI form data."""
        name = self.name_var.get()
        if not name:
            name = f"{SERVO_DEF_NAME} {len(self.manager.servos) + 1}"

        new_servo = self.manager.add_servo(name)

        if new_servo is None:
            messagebox.showwarning(MSG_WARN_TITLE, MSG_WARN_TEXT, parent=self)
            return

        new_servo.step = self.step_var.get()
        new_servo.min_val = self.min_var.get()
        new_servo.max_val = self.max_var.get()
        # pylint: disable=protected-access
        self.manager._save_config()

        self._create_servo_row(new_servo)
        self.select_servo(new_servo.channel)

    def update_servo(self) -> None:
        """Saves modifications made to the currently selected servo."""
        if self.selected_channel is None:
            messagebox.showinfo(MSG_INFO_TITLE, MSG_INFO_SELECT, parent=self)
            return

        base_name = self.name_var.get()
        existing_names = [s.name for ch_id, s in self.manager.servos.items() if ch_id !=
                          self.selected_channel]
        core_name = base_name
        counter = 1
        parts = base_name.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            core_name = parts[0]
            counter = int(parts[1])

        unique_name = base_name
        while unique_name in existing_names:
            unique_name = f"{core_name} {counter}"
            counter += 1

        servo = self.manager.servos[self.selected_channel]
        servo.name = unique_name
        servo.step = self.step_var.get()
        servo.min_val = self.min_var.get()
        servo.max_val = self.max_var.get()

        self.name_var.set(unique_name)

        self.row_widgets[self.selected_channel]['label'].config(text=servo.name)
        if self.selected_channel in self.servo_windows:
            self.servo_windows[self.selected_channel].title(servo.name)

        # pylint: disable=protected-access
        self.manager._save_config()
        messagebox.showinfo(MSG_SAVE_TITLE, MSG_SAVE_TEXT.format(servo.name), parent=self)

    def _create_servo_row(self, servo) -> None:
        """Creates a visual row for a servo in the list."""
        row_frame = tk.Frame(self.list_frame, relief=tk.SOLID, borderwidth=1, bg=COLOR_DEFAULT)
        row_frame.pack(fill=tk.X, pady=2)

        lbl = tk.Label(row_frame, text=servo.name, cursor="hand2", bg=COLOR_DEFAULT)
        lbl.pack(side=tk.LEFT, padx=PAD_S, pady=PAD_S)

        row_frame.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Double-1>", lambda event, ch=servo.channel: self.show_servo_window(ch))

        btn_del = ttk.Button(
            row_frame,
            text=TXT_BTN_DEL,
            width=3,
            command=lambda ch=servo.channel, frame=row_frame: self.delete_servo_ui(ch, frame)
        )
        btn_del.pack(side=tk.RIGHT, padx=PAD_S, pady=PAD_S)

        servo_win = ServoWindow(self, servo, self.manager)
        self.servo_windows[servo.channel] = servo_win
        self.row_widgets[servo.channel] = {'frame': row_frame, 'label': lbl}

    def select_servo(self, channel: int) -> None:
        """Highlights the selected servo and loads its data into the form."""
        self.selected_channel = channel

        for ch_id, widgets in self.row_widgets.items():
            color = COLOR_SELECTED if ch_id == channel else COLOR_DEFAULT
            widgets['frame'].config(bg=color)
            widgets['label'].config(bg=color)

        servo = self.manager.servos[channel]
        self.name_var.set(servo.name)
        self.step_var.set(servo.step)
        self.min_var.set(servo.min_val)
        self.max_var.set(servo.max_val)

    def _load_servos(self) -> None:
        """Loads previously saved servos from the manager."""
        for _, servo in self.manager.servos.items():
            self._create_servo_row(servo)

    def show_servo_window(self, channel: int) -> None:
        """Displays the popup window for the given servo channel."""
        if channel in self.servo_windows:
            self.servo_windows[channel].show_window()

    def delete_servo_ui(self, channel: int, row_frame: tk.Frame) -> None:
        """Removes a servo from the system and updates UI."""
        self.manager.remove_servo(channel)

        if channel in self.servo_windows:
            self.servo_windows[channel].destroy()
            del self.servo_windows[channel]

        if self.selected_channel == channel:
            self.selected_channel = None

        if channel in self.row_widgets:
            del self.row_widgets[channel]

        row_frame.destroy()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    hardware_mock = MockMaestroController()

    servo_manager = ServoManager(hardware_interface=hardware_mock, max_channels=24)

    app = MainWindow(servo_manager)
    app.mainloop()
