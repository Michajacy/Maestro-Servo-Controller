import tkinter as tk
from tkinter import ttk, messagebox
import logging
from hardware import MockMaestroController
from domain import ServoManager

#UI constants
MAIN_WIN_GEO = "400x500"
MAIN_WIN_TITLE = "Maestro App"
MAIN_WIN_INPUT_AREA_WIDTH = 15
SERWO_WIN_W = 250
SERWO_WIN_H = 150
PAD_XS = 2
PAD_S = 5
PAD_M = 10
PAD_L = 15
W_ENTRY = 12
W_SLIDER = 200
COLOR_SELECTED = "#97B7F8"
COLOR_DEFAULT = "#FFFFFF"

#Servo default

SERVO_DEF_NAME = "New Servo"
SERVO_DEF_STEP = 50
SERVO_DEF_MIN = 1000
SERVO_DEF_MAX = 2000

class ServoWindow(tk.Toplevel):
    "floating window to menage single servo"

    def __init__(self, parent, servo, manager) -> None:
        super().__init__(parent)
        self.withdraw()
        self.parent = parent
        self.servo = servo
        self.manager = manager
        self.title(self.servo.name)

        self.geometry(f"{SERWO_WIN_W}x{SERWO_WIN_H}") 
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._build_ui()
        self._center_on_parent(SERWO_WIN_W, SERWO_WIN_H)


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
        btn_frame.pack(pady=PAD_L) 

        self.btn_left = ttk.Button(btn_frame, text="<-", command=self.step_left)
        self.btn_left.pack(side=tk.LEFT, padx=PAD_S) 

        self.btn_right = ttk.Button(btn_frame, text="->", command=self.step_right)
        self.btn_right.pack(side=tk.RIGHT, padx=PAD_S) 

        self.lbl_position = ttk.Label(self, text=f"Position: {self.servo.position} us")
        self.lbl_position.pack()

        self.slider = ttk.Scale(
            self, from_=self.servo.min_val, to=self.servo.max_val, orient=tk.HORIZONTAL, length=W_SLIDER
        ) 
        self.slider.set(self.servo.position)
        self.slider.config(command=self.on_slider_move)
        self.slider.pack(pady=PAD_S) 

    def on_slider_move(self, value) -> None:
        pos = int(float(value))
        self.lbl_position.config(text=f"Position: {pos} us")
        self.manager.set_servo_position(self.servo.channel, pos)

    def step_left(self) -> None:
        current = self.slider.get()
        min_val = self.servo.min_val
        step = self.servo.step
        new_pos = max(min_val, current - step) 
        self.slider.set(new_pos)

    def step_right(self) -> None:
        current = self.slider.get()
        max_val = self.servo.max_val
        step = self.servo.step
        new_pos = min(max_val, current + step) 
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

        self.title(MAIN_WIN_TITLE) 
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
        settings_group = ttk.LabelFrame(self, text="Servo settings")
        settings_group.pack(fill=tk.X, padx=PAD_M, pady=PAD_M)

        config_frame = ttk.Frame(settings_group)
        config_frame.pack(side=tk.LEFT, padx=PAD_M, pady=PAD_S)

        ttk.Label(config_frame, text="Name: ").grid(row=0, column=0, sticky=tk.W, pady=PAD_XS)
        ttk.Entry(config_frame, textvariable=self.name_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(row=0, column=1, padx=PAD_S, pady=PAD_XS)

        ttk.Label(config_frame, text="Jog Step (us):").grid(row=1, column=0, sticky=tk.W, pady=PAD_XS)
        ttk.Entry(config_frame, textvariable=self.step_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(row=1, column=1, padx=PAD_S, pady=PAD_XS)

        ttk.Label(config_frame, text="Min Pos:").grid(row=2, column=0, sticky=tk.W, pady=PAD_XS)
        ttk.Entry(config_frame, textvariable=self.min_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(row=2, column=1, padx=PAD_S, pady=PAD_XS)

        ttk.Label(config_frame, text="Max Pos:").grid(row=3, column=0, sticky=tk.W, pady=PAD_XS)
        ttk.Entry(config_frame, textvariable=self.max_var, width=MAIN_WIN_INPUT_AREA_WIDTH).grid(row=3, column=1, padx=PAD_S, pady=PAD_XS)

        btn_frame = ttk.Frame(settings_group)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=PAD_S, pady=PAD_S)

        btn_add = ttk.Button(btn_frame, text="Save Changes", command=self.update_servo)
        btn_add.pack(side=tk.BOTTOM, fill=tk.X, padx=PAD_S)

        btn_add = ttk.Button(btn_frame, text="+ Add servo", command=self.add_servo_ui)
        btn_add.pack(side=tk.BOTTOM, fill=tk.X, padx=PAD_S)

        list_group = ttk.LabelFrame(self, text="Active servos")
        list_group.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_S)

        self.list_frame = ttk.Frame(list_group)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_M, pady=PAD_S)


    def add_servo_ui(self) -> None:
        name = self.name_var.get()
        if not name:
            name = f"Servo {len(self.manager.servos) + 1}"

        new_servo = self.manager.add_servo(name)

        if new_servo is None:
            messagebox.showwarning("No free channels", "All channels occupied")
            return

        new_servo.step = self.step_var.get()
        new_servo.min_val = self.min_var.get()
        new_servo.max_val = self.max_var.get()
        self.manager._save_config()

        self._create_servo_row(new_servo)
        self.select_servo(new_servo.channel)


    def update_servo(self) -> None:
        if self.selected_channel is None:
            messagebox.showinfo("Info", "Select a servo from the list first.")
            return

        servo = self.manager.servos[self.selected_channel]
        servo.name = self.name_var.get()
        servo.step = self.step_var.get()
        servo.min_val = self.min_var.get()
        servo.max_val = self.max_var.get()
        
        self.row_widgets[self.selected_channel]['label'].config(text=servo.name)
        if self.selected_channel in self.servo_windows:
            self.servo_windows[self.selected_channel].title(servo.name)
            
        self.manager._save_config()
        messagebox.showinfo("Saved", f"Configuration for '{servo.name}' saved!")


    def _create_servo_row(self, servo) -> None:
        row_frame = tk.Frame(self.list_frame, relief=tk.SOLID, borderwidth=1, bg=COLOR_DEFAULT) 
        row_frame.pack(fill=tk.X, pady=2) 

        lbl = tk.Label(row_frame, text=servo.name, cursor="hand2", bg=COLOR_DEFAULT) 
        lbl.pack(side=tk.LEFT, padx=PAD_S, pady=PAD_S) 
        
        row_frame.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Button-1>", lambda event, ch=servo.channel: self.select_servo(ch))
        lbl.bind("<Double-1>", lambda event, ch=servo.channel: self.show_servo_window(ch))

        btn_del = ttk.Button(row_frame, text="X", width=3, command=lambda ch=servo.channel, frame=row_frame: self.delete_servo_ui(ch, frame))
        btn_del.pack(side=tk.RIGHT, padx=PAD_S, pady=PAD_S) 

        sw = ServoWindow(self, servo, self.manager)
        self.servo_windows[servo.channel] = sw
        self.row_widgets[servo.channel] = {'frame': row_frame, 'label': lbl}

    def select_servo(self, channel: int) -> None:
        self.selected_channel = channel
        
        for ch, widgets in self.row_widgets.items():
            color = COLOR_SELECTED if ch == channel else COLOR_DEFAULT
            widgets['frame'].config(bg=color)
            widgets['label'].config(bg=color)
            
        servo = self.manager.servos[channel]
        self.name_var.set(servo.name)
        self.step_var.set(servo.step)
        self.min_var.set(servo.min_val)
        self.max_var.set(servo.max_val)

    def _load_servos(self) -> None:
        for _, servo in self.manager.servos.items():
            self._create_servo_row(servo)

    def show_servo_window(self, channel: int) -> None:
        if channel in self.servo_windows:
            self.servo_windows[channel].show_window()

    def delete_servo_ui(self, channel: int, row_frame: tk.Frame) -> None:
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
    hardware = MockMaestroController()

    manager = ServoManager(hardware_interface=hardware, max_channels=24) #magic value

    app = MainWindow(manager)
    app.mainloop()