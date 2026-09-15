import tkinter as tk
from tkinter import ttk, messagebox
from hardware import MockMaestroController
from domain import ServoManager

class ServoWindow(tk.Toplevel):
    "floating window to menage single servo"

    def __init__(self, parent, servo, manager) -> None:
        super().__init__(parent)
        self.parent = parent
        self.servo = servo
        self.manager = manager
        self.title(self.servo.name)

        win_width = 250
        win_height = 150
        self.geometry(f"{win_width}x{win_height}") #imo poorly defined
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._build_ui()
        self._center_on_parent(win_width, win_height)

    def _center_on_parent(self, width: int, height: int) -> None:
        """Centers the child window over the parent window"""

        self.update_idletasks()

        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (width // 2)
        pos_y = parent_y + (parent_height // 2) - (height // 2)

        self.geometry(f"+{pos_x}+{pos_y}")

    def _build_ui(self) -> None:

        #frame for buttons L/R
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15) #poorly defined

        self.btn_left = ttk.Button(btn_frame, text="<-", command=self.step_left)
        self.btn_left.pack(side=tk.LEFT, padx=5) #poorly defined padding

        self.btn_right = ttk.Button(btn_frame, text="->", command=self.step_right)
        self.btn_right.pack(side=tk.RIGHT, padx=5) #poorly defined padding

        self.lbl_position = ttk.Label(self, text=f"Position: {self.servo.position} us")
        self.lbl_position.pack()

        self.slider = ttk.Scale(
            self, from_=self.servo.min_val, to=self.servo.max_val, orient=tk.HORIZONTAL, length=200, command=self.on_slider_move
        ) # magic values
        self.slider.set(self.servo.position)
        self.slider.pack(pady=5) #magic value

    def on_slider_move(self, value) -> None:
        pos = int(float(value))
        self.lbl_position.config(text=f"Position: {pos} us")
        self.manager.set_servo_position(self.servo.channel, pos)

    def step_left(self) -> None:
        current = self.slider.get()
        min_val = self.servo.min_val
        step = self.servo.step
        new_pos = max(min_val, current - step) #magic values
        self.slider.set(new_pos)

    def step_right(self) -> None:
        current = self.slider.get()
        max_val = self.servo.max_val
        step = self.servo.step
        new_pos = min(max_val, current + step) #magic values
        self.slider.set(new_pos)

    def hide_window(self) -> None:
        self.withdraw()

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()



class MainWindow(tk.Tk):

    def __init__(self, manager: ServoManager) -> None:
        super().__init__()
        self.manager = manager
        self.servo_windows = {}

        self.title("Maestro App") #poorly defined
        self.geometry("300x400") #poorly defined

        self.step_var = tk.IntVar(value=50)
        self.min_var = tk.IntVar(value=1000)
        self.max_var = tk.IntVar(value=2000)

        self._build_ui()
        self._load_servos()

    def _build_ui(self) -> None:
        settings_group = ttk.LabelFrame(self, text="Servo settings")
        settings_group.pack(fill=tk.X, padx=10, pady=10)

        config_frame = ttk.Frame(settings_group)
        config_frame.pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Label(config_frame, text="Jog Step (us):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.step_var, width=8).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(config_frame, text="Min Pos:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.min_var, width=8).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(config_frame, text="Max Pos:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(config_frame, textvariable=self.max_var, width=8).grid(row=2, column=1, padx=5, pady=2)

        btn_add = ttk.Button(settings_group, text="+ Add servo", command=self.add_servo_ui)
        btn_add.pack(side=tk.RIGHT, padx=10)

        list_group = ttk.LabelFrame(self, text="Active servos")
        list_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.list_frame = ttk.Frame(list_group)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)


    def add_servo_ui(self) -> None:
        count = len(self.manager.servos) + 1
        name = f"Servo {count} name"

        new_servo = self.manager.add_servo(name)

        if new_servo is None:
            messagebox.showwarning("No free channels", "All channesl occupied")
            return

        new_servo.step = self.step_var.get()
        new_servo.min_val = self.min_var.get()
        new_servo.max_val = self.max_var.get()
        self.manager._save_config()

        self._create_servo_row(new_servo)

    def _create_servo_row(self, servo) -> None:

        row_frame = ttk.Frame(self.list_frame, relief=tk.SOLID, borderwidth=1) #magic value
        row_frame.pack(fill=tk.X, pady=2) #magic value

        lbl = ttk.Label(row_frame, text=servo.name, cursor="hand2") #poorly defined
        lbl.pack(side=tk.LEFT, padx=5, pady=5) #magic values
        lbl.bind("<Double-1>", lambda event, ch=servo.channel: self.show_servo_window(ch))

        btn_del = ttk.Button(row_frame, text="X", width=3, command=lambda ch=servo.channel, frame=row_frame: self.delete_servo_ui(ch, frame))
        btn_del.pack(side=tk.RIGHT, padx=5, pady=5) #magic values

        sw = ServoWindow(self, servo, self.manager)
        self.servo_windows[servo.channel] = sw

    def _load_servos(self) -> None:
        for _, servo in self.manager.servos.items():
            self._create_servo_row(servo)


    def show_servo_window(self, channel: int) -> None:
        if channel in self.servo_windows:
            self.servo_windows[channel].show_window()


    def delete_servo_ui(self, channel: int, row_frame: ttk.Frame) -> None:
        self.manager.remove_servo(channel)

        if channel in self.servo_windows:
            self.servo_windows[channel].destroy()
            del self.servo_windows[channel]

        row_frame.destroy()



if __name__ == "__main__":
    hardware = MockMaestroController()

    manager = ServoManager(hardware_interface=hardware, max_channels=24) #magic value

    app = MainWindow(manager)
    app.mainloop()