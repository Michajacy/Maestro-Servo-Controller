"""
UI Module for Maestro Servo Controller.
Handles the graphical user interface and user interactions.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import json
import os
from hardware import MockMaestroController, SerialMaestroController
from domain import ServoManager
import config


class ServoWindow(tk.Toplevel):
    """Floating window to manage a single servo."""

    def __init__(self, parent: tk.Tk, servo, manager: ServoManager) -> None:
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.servo = servo
        self.manager = manager
        self.title(self.servo.name)

        self.geometry(f"{config.SERVO_WIN_W}x{config.SERVO_WIN_H}")
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
        btn_frame.pack(pady=config.PAD_L)

        self.btn_left = ttk.Button(btn_frame, text=config.TXT_BTN_LEFT, command=self.step_left)
        self.btn_left.pack(side=tk.LEFT, padx=config.PAD_S)

        self.btn_right = ttk.Button(btn_frame, text=config.TXT_BTN_RIGHT, command=self.step_right)
        self.btn_right.pack(side=tk.RIGHT, padx=config.PAD_S)

        self.lbl_position = ttk.Label(self, text=config.TXT_LBL_POS.format(self.servo.position))
        self.lbl_position.pack()

        self.slider = ttk.Scale(
            self,
            from_=self.servo.min_val,
            to=self.servo.max_val,
            orient=tk.HORIZONTAL,
            length=config.SLIDER_W
        )
        self.slider.set(self.servo.position)
        self.slider.config(command=self.on_slider_move)
        self.slider.pack(pady=config.PAD_S)

    def refresh_limits(self) -> None:
        """Updates slider limits after changes in MainWindow"""
        self.slider.config(from_=self.servo.min_val, to=self.servo.max_val)

        if self.servo.position < self.servo.min_val:
            self.servo.position = self.servo.min_val
            self.slider.set(self.servo.position)
        elif self.servo.position > self.servo.max_val:
            self.servo.position = self.servo.max_val
            self.slider.set(self.servo.position)

        self.lbl_position.config(text=config.TXT_LBL_POS.format(self.servo.position))

    def on_slider_move(self, value: str) -> None:
        """Handles slider movement and updates hardware."""
        pos = int(float(value))
        self.lbl_position.config(text=config.TXT_LBL_POS.format(pos))
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
        self._center_on_parent(config.SERVO_WIN_W, config.SERVO_WIN_H)
        self.deiconify()
        self.lift()
        self.focus_force()

class MainWindow(tk.Tk):
    """Main application window for managing multiple servos."""

    def __init__(self, manager: ServoManager) -> None:
        super().__init__()
        self.manager = manager
        self.servo_windows = {}

        self.title(config.TXT_APP_TITLE)
        self.geometry(config.MAIN_WIN_GEO)

        self.selected_channel = None
        self.row_widgets = {}

        self.name_var = tk.StringVar(value=config.SERVO_DEF_NAME)
        self.step_var = tk.IntVar(value=config.SERVO_DEF_STEP)
        self.min_var = tk.IntVar(value=config.SERVO_DEF_MIN)
        self.max_var = tk.IntVar(value=config.SERVO_DEF_MAX)

        self.hw_var = tk.StringVar(value=self.manager.hw_mode)

        self._build_ui()
        self._load_servos()

    def _build_ui(self) -> None:
        """Constructs the main layout and property manager."""
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=config.PAD_M, pady=(config.PAD_M, 0))

        ttk.Label(top_frame, text=config.COMBO_TXT).pack(side=tk.LEFT)
        hw_cb = ttk.Combobox(
            top_frame,
            textvariable=self.hw_var,
            values=config.COMBO_VALUES,
            state=config.COMBO_STATE,
            width=config.COMBO_W
        )
        hw_cb.pack(side=tk.LEFT, padx=config.PAD_S)
        hw_cb.bind("<<ComboboxSelected>>", self.on_hw_changed)

        settings_group = ttk.LabelFrame(self, text=config.TXT_GROUP_SETTINGS)
        settings_group.pack(fill=tk.X, padx=config.PAD_M, pady=config.PAD_M)

        config_frame = ttk.Frame(settings_group)
        config_frame.pack(side=tk.LEFT, padx=config.PAD_M, pady=config.PAD_S)

        ttk.Label(config_frame, text=config.TXT_LBL_NAME).grid(
            row=0, column=0, sticky=tk.W, pady=config.PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.name_var,
                  width=config.MAIN_WIN_INPUT_AREA_WIDTH).grid(
                      row=0, column=1, padx=config.PAD_S, pady=config.PAD_XS)

        ttk.Label(config_frame, text=config.TXT_LBL_STEP).grid(
            row=1, column=0, sticky=tk.W, pady=config.PAD_XS)

        ttk.Entry(config_frame, textvariable=self.step_var,
                  width=config.MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=1, column=1, padx=config.PAD_S, pady=config.PAD_XS)

        ttk.Label(config_frame, text=config.TXT_LBL_MIN).grid(
            row=2, column=0, sticky=tk.W, pady=config.PAD_XS
        )
        ttk.Entry(config_frame, textvariable=self.min_var,
                  width=config.MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=2, column=1, padx=config.PAD_S, pady=config.PAD_XS)

        ttk.Label(config_frame, text=config.TXT_LBL_MAX).grid(
            row=3, column=0, sticky=tk.W, pady=config.PAD_XS)

        ttk.Entry(config_frame, textvariable=self.max_var,
                  width=config.MAIN_WIN_INPUT_AREA_WIDTH).grid(
            row=3, column=1, padx=config.PAD_S, pady=config.PAD_XS)

        btn_frame = ttk.Frame(settings_group)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=config.PAD_S, pady=config.PAD_S)

        btn_add = ttk.Button(btn_frame, text=config.TXT_BTN_ADD, command=self.add_servo_ui)
        btn_add.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        btn_update = ttk.Button(btn_frame, text=config.TXT_BTN_SAVE, command=self.update_servo)
        btn_update.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        list_group = ttk.LabelFrame(self, text=config.TXT_GROUP_LIST)
        list_group.pack(fill=tk.BOTH, expand=True, padx=config.PAD_M, pady=config.PAD_S)

        self.canvas = tk.Canvas(list_group, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_group, orient=tk.VERTICAL, command=self.canvas.yview)

        self.list_frame = tk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_frame_id = self.canvas.create_window((0, 0),
                                                         window=self.list_frame, anchor="nw")

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

    def _validate_servo_inputs(self) -> bool:
        """Validates numeric inputs. Returns True if valid, False otherwise."""
        try:
            step = self.step_var.get()
            min_val = self.min_var.get()
            max_val = self.max_var.get()
        except tk.TclError:
            messagebox.showerror(config.MSG_ERR_VAL_TITLE, config.MSG_ERR_VAL_INT, parent=self)
            return False

        if step <= 0:
            messagebox.showerror(config.MSG_ERR_VAL_TITLE, config.MSG_ERR_VAL_STEP, parent=self)
            return False

        if min_val < 0 or max_val < 0:
            messagebox.showerror(config.MSG_ERR_VAL_TITLE, config.MSG_ERR_VAL_NEG, parent=self)
            return False

        if min_val >= max_val:
            messagebox.showerror(config.MSG_ERR_VAL_TITLE, config.MSG_ERR_VAL_MINMAX, parent=self)
            return False

        if max_val > 10000:
            messagebox.showerror(config.MSG_ERR_VAL_TITLE, config.MSG_ERR_VAL_LARGE, parent=self)
            return False

        return True

    def on_hw_changed(self, _) -> None:
        """Handles switching between physical Serial port and Virtual Mock."""
        new_mode = self.hw_var.get()
        try:
            if new_mode == "Serial":
                new_hw = SerialMaestroController()
            else:
                new_hw = MockMaestroController()
            self.manager.set_hardware(new_hw, new_mode)
        except ImportError:
            messagebox.showerror("Error", "pyserial module is not installed.", parent=self)
            self.hw_var.set("Mock")
            self.manager.set_hardware(MockMaestroController(), "Mock")

    def add_servo_ui(self) -> None:
        """Handles adding a new servo based on UI form data."""
        name = self.name_var.get()
        if not name:
            name = f"{config.SERVO_DEF_NAME} {len(self.manager.servos) + 1}"

        new_servo = self.manager.add_servo(name)

        if new_servo is None:
            messagebox.showwarning(config.MSG_WARN_TITLE, config.MSG_WARN_TEXT, parent=self)
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
            messagebox.showinfo(config.MSG_INFO_TITLE, config.MSG_INFO_SELECT, parent=self)
            return

        if not self._validate_servo_inputs():
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
            win = self.servo_windows[self.selected_channel]
            win.title(servo.name)
            win.refresh_limits()

        # pylint: disable=protected-access
        self.manager._save_config()
        messagebox.showinfo(config.MSG_SAVE_TITLE,
                            config.MSG_SAVE_TEXT.format(servo.name), parent=self)

    def _create_servo_row(self, servo) -> None:
        """Creates a visual row for a servo in the list."""
        row_frame = tk.Frame(self.list_frame, relief=tk.SOLID,
                             borderwidth=1, bg=config.COLOR_DEFAULT)
        row_frame.pack(fill=tk.X, pady=2)

        lbl = tk.Label(row_frame, text=servo.name, cursor="hand2", bg=config.COLOR_DEFAULT)
        lbl.pack(side=tk.LEFT, padx=config.PAD_S, pady=config.PAD_S)

        row_frame.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Double-1>", lambda event, ch=servo.channel: self.show_servo_window(ch))

        btn_del = ttk.Button(
            row_frame,
            text=config.TXT_BTN_DEL,
            width=3,
            command=lambda ch=servo.channel, frame=row_frame: self.delete_servo_ui(ch, frame)
        )
        btn_del.pack(side=tk.RIGHT, padx=config.PAD_S, pady=config.PAD_S)

        servo_win = ServoWindow(self, servo, self.manager)
        self.servo_windows[servo.channel] = servo_win
        self.row_widgets[servo.channel] = {'frame': row_frame, 'label': lbl}

    def select_servo(self, channel: int) -> None:
        """Highlights the selected servo and loads its data into the form."""
        self.selected_channel = channel

        for ch_id, widgets in self.row_widgets.items():
            color = config.COLOR_SELECTED if ch_id == channel else config.COLOR_DEFAULT
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

def _get_initial_hardware_mode() -> str:
    """Pre-reads JSON configuration to determine the saved hardware mode."""
    config_file = "servos_config.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("settings", {}).get("hw_mode", "Mock")
            except (json.JSONDecodeError, ValueError):
                pass
    return "Mock"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    initial_mode = _get_initial_hardware_mode()

    try:
        hw = SerialMaestroController() if initial_mode == "Serial" else MockMaestroController()
    except ImportError:
        hw = MockMaestroController()
        initial_mode = "Mock"

    servo_manager = ServoManager(hardware_interface=hw, hw_mode=initial_mode,
                                 max_channels=config.MAX_CHANNELS)

    app = MainWindow(servo_manager)
    app.mainloop()
