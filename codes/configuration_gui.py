import tkinter as tk
import os
import subprocess
from tkinter import *
from tkinter import ttk
import tkinter.filedialog as fd
from tkinter import messagebox

# import converters
import shutil
from datetime import datetime
import customtkinter as ctk
import subprocess
from pathlib import Path
import ast
from glob import glob
import sys
from contextlib import contextmanager
from time import time
from typing import Dict, List
from PIL import Image, ImageTk
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.preserve_implicit = True
yaml.boolean_representation = ["false", "true"]
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# work in progress code, not finished, credits will be added at a later date.
def run(command, desc=None, errdesc=None, custom_env=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(
        command, shell=True, env=os.environ if custom_env is None else custom_env
    )
    return result


def run_quiet(command, desc=None, errdesc=None, custom_env=None):
    if desc is not None:
        print(desc)

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=os.environ if custom_env is None else custom_env,
    )

    if result.returncode != 0:
        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """

    def __init__(self, widget, text="widget info"):
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        # parent of the widget
        # hack to get the master of the app

        self.parent = widget.winfo_toplevel()
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 50
        y += self.widget.winfo_rooty() + 50
        # creates a toplevel window
        self.tw = ctk.CTkToplevel(self.widget)
        # self.tw.wm_attributes("-topmost", 1)
        # self.parent.wm_attributes("-topmost", 0)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        # top most

        label = ctk.CTkLabel(
            self.tw, text=self.text, justify="left", wraplength=self.wraplength
        )
        label.pack(padx=10, pady=10)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            latest_git_hash = (
                subprocess.check_output(
                    [
                        "git",
                        "ls-remote",
                        "https://github.com/152334H/DL-Art-School.git",
                        "master",
                    ],
                    cwd=Path(__file__).resolve().parent,
                )
                .strip()
                .decode()[0:7]
            )
            # check if configs folder exists
            print("Latest git hash: " + latest_git_hash)
        except:
            pass
        if not os.path.exists("configs"):
            os.makedirs("configs")

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.geometry(f"{700}x{620}")
        # self.stableTune_icon =PhotoImage(master=self,file = "resources/DLAS_icon.png")
        # self.iconphoto(False, self.stableTune_icon)
        self.dark_mode_var = "#1e2124"
        self.dark_purple_mode_var = "#1B0F1B"
        self.dark_mode_title_var = "#7289da"
        self.dark_mode_button_pressed_var = "#BB91B6"
        self.dark_mode_button_var = "#8ea0e1"
        self.dark_mode_text_var = "#c6c7c8"
        self.title("DLAS")
        self.configure(cursor="left_ptr")
        # resizable window
        self.resizable(True, True)
        self.create_default_variables()
        # check if DLAS.cfg exists
        if not os.path.exists("DLAS_hash.cfg"):
            # create DLAS.cfg and write the latest git hash
            with open("DLAS_hash.cfg", "w") as f:
                f.write(latest_git_hash)
        else:
            # read DLAS.cfg
            with open("DLAS_hash.cfg", "r") as f:
                old_git_hash = f.read()
            try:
                # check if the latest git hash is the same as the one in DLAS.cfg
                if latest_git_hash != old_git_hash:
                    # if not the same, delete the old DLAS.cfg and create a new one with the latest git hash
                    self.update_available = True
            except:
                self.update_available = False
        self.sidebar_frame = ctk.CTkFrame(self, width=100, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, sticky="nsew")
        # image logo
        # empty label
        self.empty_label = ctk.CTkLabel(self.sidebar_frame, text="")
        self.empty_label.grid(row=0, column=0, padx=0, pady=5, sticky="n")
        self.logo_image = ctk.CTkImage(dark_image=self.icon, size=(100, 100))
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, image=self.logo_image, text=""
        )
        self.logo_label.grid(row=1, column=0, padx=0, pady=0, sticky="n")
        self.logo_label_text = ctk.CTkLabel(
            self.sidebar_frame, text="DLAS", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label_text.grid(row=2, column=0, padx=0, pady=20)

        self.sidebar_button_0 = ctk.CTkButton(
            self.sidebar_frame, text="Load Config", command=self.load_config
        )
        self.sidebar_button_0.configure(fg_color="transparent")
        self.sidebar_button_0.grid(row=3, column=0, padx=20, pady=5)
        self.sidebar_button_1 = ctk.CTkButton(
            self.sidebar_frame,
            text="Common Settings",
            command=self.general_nav_button_event,
        )
        self.sidebar_button_1.grid(row=4, column=0, padx=20, pady=5)
        self.sidebar_button_2 = ctk.CTkButton(
            self.sidebar_frame,
            text="Advanced Settings",
            command=self.training_nav_button_event,
        )
        self.sidebar_button_2.grid(row=5, column=0, padx=20, pady=5)
        self.sidebar_button_3 = ctk.CTkButton(
            self.sidebar_frame,
            text="Auto Settings",
            command=self.calculate_training_parameters,
        )
        self.sidebar_button_3.configure(fg_color="transparent")
        self.sidebar_button_3.grid(row=6, column=0, padx=20, pady=5)

        if self.update_available:
            self.sidebar_button_11 = ctk.CTkButton(
                self.sidebar_frame,
                text="Update Available",
                fg_color="red",
                hover_color="darkred",
                command=self.update_DLAS,
            )
            self.sidebar_button_11.grid(row=7, column=0, padx=20, pady=5)

        self.sidebar_button_12 = ctk.CTkButton(
            self.sidebar_frame,
            text="Start Training!",
            command=lambda: self.process_inputs(export=False),
        )
        # self.sidebar_button_12.bind("<Button-3>", self.create_right_click_menu_export)
        self.sidebar_button_12.grid(row=14, column=0, padx=20, pady=5)
        self.side_playground_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Playground",
            command=self.playground_nav_button_event,
        )
        self.side_playground_button.grid(row=15, column=0, padx=20, pady=5)
        self.general_frame = ctk.CTkFrame(
            self, width=140, corner_radius=0, fg_color="transparent"
        )
        self.general_frame.grid_columnconfigure(0, weight=10)
        self.general_frame_subframe = ctk.CTkScrollableFrame(
            self.general_frame, width=150, height=500, corner_radius=20
        )
        self.general_frame_subframe.grid(
            row=2, column=0, sticky="nsew", padx=20, pady=20
        )
        self.create_general_settings_widgets()
        self.apply_general_style_to_widgets(self.general_frame_subframe)
        self.advanced_settings_frame = ctk.CTkFrame(
            self, width=400, corner_radius=0, fg_color="transparent"
        )
        self.advanced_settings_frame.grid_columnconfigure(0, weight=1)
        self.advanced_settings_frame_subframe = ctk.CTkFrame(
            self.advanced_settings_frame, width=400, corner_radius=20
        )
        self.advanced_settings_frame_subframe.grid_columnconfigure(0, weight=1)
        self.advanced_settings_frame_subframe.grid_columnconfigure(1, weight=1)
        self.advanced_settings_frame_subframe.grid(
            row=2, column=0, sticky="nsew", padx=20, pady=20
        )
        self.create_advanced_settings_widgets()
        self.apply_general_style_to_widgets(self.advanced_settings_frame_subframe)
        self.override_training_style_widgets()
        self.playground_frame = ctk.CTkFrame(
            self, width=400, corner_radius=0, fg_color="transparent"
        )
        self.playground_frame.grid_columnconfigure(0, weight=1)
        self.playground_frame_subframe = ctk.CTkFrame(
            self.playground_frame, width=400, corner_radius=20
        )
        self.playground_frame_subframe.grid_columnconfigure(0, weight=1)
        self.playground_frame_subframe.grid_columnconfigure(1, weight=1)
        self.playground_frame_subframe.grid(
            row=2, column=0, sticky="nsew", padx=20, pady=20
        )
        self.create_playground_widgets()
        self.apply_general_style_to_widgets(self.playground_frame_subframe)

        self.select_frame_by_name("general")
        self.update()

        if os.path.exists("./experiments/DLAS_last_run.yaml"):
            try:
                self.load_config(file_name="./experiments/DLAS_last_run.yaml")
            except Exception as e:
                print(e)
                pass
        else:
            pass

    def create_default_variables(self):
        self.base_config_path = "./codes/utils/BASE_gpt.yaml"
        self.icon_path = "./codes/utils/UI_icon.png"
        # load icon and resize to 32x32
        self.icon = Image.open(self.icon_path)
        # self.icon = self.icon.resize((32, 32), Image.ANTIALIAS)
        # self.icon = ImageTk.PhotoImage(self.icon)

        with open(self.base_config_path, "r") as stream:
            self.base_config = yaml.load(stream)
        # common variables first
        self.project_name = ""
        self.gpu_ids = "[0]"
        self.enable_checkpointing = True
        self.use_fp16 = False
        self.use_wandb = False
        self.use_tb_logger = True

        # common dataset variables
        self.train_batch_size = 128
        self.valid_batch_size = 128
        self.path_to_lj_dataset = ""

        # common training variables
        self.iterations_number = 50000
        self.warmup_steps = -1
        self.gradient_accumlation = 4
        self.learning_rate = "1e-5"
        self.learning_rate_steps = "[100, 200, 280, 360]"
        self.ema_model_save = False
        self.save_states = True
        self.training_seed = 1337

        # common logger variables
        self.print_status_frequency = 100
        self.save_checkpoint_frequency = 500
        self.visual_debug_rate = 500

        # advanced common variables
        self.model = "extensibletrainer"
        self.scale = 1
        self.start_step = -1

        # advanced common dataset variables
        self.train_num_workers = 8
        self.valid_num_workers = 1
        self.path_to_ar_model = "../experiments/autoregressive.pth"
        # self.path_to_dvae_model = '../experiments/dvae.pth'
        # configurator variables
        self.update_available = False
        # check if there's a tortoise-tts-fast folder in the current directory
        # playground variables
        self.playground_api = None
        self.playground_model_path = (
            self.find_latest_generated_model()
            if os.path.exists("tortoise-tts-fast")
            else ""
        )
        self.playground_seed = ""
        self.playground_text = ""
        self.playground_voice_dir = ""
        self.playground_compare = False
        self.playground_candidates = 3
        self.playground_use_training_data = True

    def find_latest_generated_model(self):
        model_path = "./experiments"
        # sort the directories by date
        dirs = sorted(
            os.listdir(model_path),
            key=lambda x: os.path.getmtime(os.path.join(model_path, x)),
        )
        # reverse the list so that the latest is first
        dirs.reverse()
        for dir in dirs:
            # if is dir
            if os.path.isdir(os.path.join(model_path, dir)):
                if "archived" not in dir:
                    # check if there are files under the model directory
                    if len(os.listdir(os.path.join(model_path, dir, "models"))) > 0:
                        # sort the files by date
                        files = sorted(
                            os.listdir(os.path.join(model_path, dir, "models")),
                            key=lambda x: os.path.getmtime(
                                os.path.join(model_path, dir, "models", x)
                            ),
                        )
                        # reverse the list so that the latest is first
                        files.reverse()
                        for file in files:
                            if not file.startswith("0_"):
                                if "ema" not in file.lower():
                                    return os.path.join(model_path, dir, "models", file)
        return ""
        return None

    def install_tortoise(self):
        os.mkdir("results")
        run(
            "git clone https://github.com/152334H/tortoise-tts-fast",
            desc="Cloning Tortoise TTS Fast",
        )
        run(
            "python -m pip install -e tortoise-tts-fast/.",
            desc="Installing Tortoise TTS Fast",
        )

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.sidebar_button_1.configure(
            fg_color=("gray75", "gray25") if name == "general" else "transparent"
        )
        self.sidebar_button_2.configure(
            fg_color=("gray75", "gray25") if name == "training" else "transparent"
        )

        # show selected frame
        if name == "general":
            self.general_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.general_frame.grid_forget()
        if name == "training":
            self.advanced_settings_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.advanced_settings_frame.grid_forget()
        if name == "playground":
            # check if tortoise-tts-fast exists
            if os.path.exists("./tortoise-tts-fast"):
                self.playground_frame.grid(row=0, column=1, sticky="nsew")
                if self.playground_api is None:
                    if self.playground_model_path != "":
                        self.playground_api = self.start_tts_api(
                            self.playground_model_path_entry
                        )
            else:
                # yes no messagebox
                if messagebox.askyesno(
                    "Tortoise TTS Fast not found",
                    "Tortoise TTS Fast is required in order to do inference. Do you want me to set it up?",
                ):
                    # download tortoise-tts-fast
                    self.install_tortoise()
                    # show messagebox
                    messagebox.showinfo(
                        "Tortoise TTS Fast installed",
                        "Tortoise TTS Fast has been installed. Please restart the application, if there were errors, delete the tortoise-tts-fast folder and try again.",
                    )
                    self.destroy()
                    self.quit()
                else:
                    self.playground_frame.grid_forget()
        else:
            self.playground_frame.grid_forget()

    def general_nav_button_event(self):
        self.select_frame_by_name("general")

    def training_nav_button_event(self):
        self.select_frame_by_name("training")

    def playground_nav_button_event(self):
        self.select_frame_by_name("playground")

    # create a right click menu for entry widgets
    def create_right_click_menu(self, event):
        # create a menu
        self.menu = Menu(self.master, tearoff=0)
        self.menu.config(font=("Segoe UI", 15))

        # set dark colors for the menu
        self.menu.configure(
            bg="#2d2d2d",
            fg="#ffffff",
            activebackground="#2d2d2d",
            activeforeground="#ffffff",
        )
        # add commands to the menu
        self.menu.add_command(
            label="Cut", command=lambda: self.focus_get().event_generate("<<Cut>>")
        )
        self.menu.add_command(
            label="Copy", command=lambda: self.focus_get().event_generate("<<Copy>>")
        )
        self.menu.add_command(
            label="Paste", command=lambda: self.focus_get().event_generate("<<Paste>>")
        )
        self.menu.add_command(
            label="Select All",
            command=lambda: self.focus_get().event_generate("<<SelectAll>>"),
        )
        # display the menu
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.menu.grab_release()

    def create_right_click_menu_export(self, event):
        # create a menu
        self.menu = Menu(self.master, tearoff=0)
        # set menu size and font size
        self.menu.config(font=("Segoe UI", 15))

        # set dark colors for the menu
        self.menu.configure(
            bg="#2d2d2d",
            fg="#ffffff",
            activebackground="#2d2d2d",
            activeforeground="#ffffff",
        )
        # add commands to the menu
        self.menu.add_command(
            label="Export Trainer Command for Windows",
            command=lambda: self.process_inputs(export="Win"),
        )
        self.menu.add_command(
            label="Copy Trainer Command for Linux",
            command=lambda: self.process_inputs(export="LinuxCMD"),
        )
        # display the menu
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.menu.grab_release()

    def create_left_click_menu_config(self, event):
        # create a menu
        self.menu = Menu(self.master, tearoff=0)
        # set menu size and font size
        self.menu.config(font=("Segoe UI", 15))

        # set dark colors for the menu
        self.menu.configure(
            bg="#2d2d2d",
            fg="#ffffff",
            activebackground="#2d2d2d",
            activeforeground="#ffffff",
        )
        # add commands to the menu
        self.menu.add_command(label="Load Config", command=self.load_config)
        self.menu.add_command(label="Save Config", command=self.save_config)
        # display the menu
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self.menu.grab_release()

    def override_training_style_widgets(self):
        for i in self.advanced_settings_frame_subframe.children.values():
            if "ctkbutton" in str(i):
                i.grid(padx=5, pady=5, sticky="w")
            if "ctkoptionmenu" in str(i):
                i.grid(padx=10, pady=5, sticky="w")
            if "ctkentry" in str(i):
                i.configure(width=160)
                i.grid(padx=10, pady=5, sticky="w")
                i.bind("<Button-3>", self.create_right_click_menu)
            if "ctkswitch" in str(i):
                i.configure(text="")
                i.grid(padx=10, pady=5, sticky="")
            if "ctklabel" in str(i):
                i.grid(padx=10, pady=5, sticky="w")

    def apply_general_style_to_widgets(self, frame):
        for i in frame.children.values():
            if "ctkbutton" in str(i):
                i.grid(padx=10, pady=10, sticky="w")
            if "ctkoptionmenu" in str(i):
                i.grid(padx=10, pady=10, sticky="w")
            if "ctkentry" in str(i):
                i.configure(width=160)
                i.grid(padx=10, pady=5, sticky="w")
                i.bind("<Button-3>", self.create_right_click_menu)
            if "ctkswitch" in str(i):
                i.configure(text="")
                i.grid(padx=10, pady=10, sticky="")
            if "ctklabel" in str(i):
                i.grid(padx=10, sticky="w")

    def grid_train_settings(self):
        # define grid row and column
        self.advanced_settings_frame_subframe.grid_columnconfigure(0, weight=2)
        self.advanced_settings_frame_subframe.grid_columnconfigure(1, weight=1)
        self.advanced_settings_frame_subframe.grid_columnconfigure(2, weight=2)
        self.advanced_settings_frame_subframe.grid_columnconfigure(3, weight=1)

        rows = 12
        columns = 4
        widgets = self.advanced_settings_frame_subframe.children.values()
        # organize widgets in grid
        curRow = 0
        curColumn = 0
        # make widgets a list
        widgets = list(widgets)[1:]
        # find ctkcanvas in widgets and remove it
        for i in widgets:
            if "ctkcanvas" in str(i):
                widgets.remove(i)
        # create pairs of widgets
        pairs = []
        for i in range(0, len(widgets), 2):
            pairs.append([widgets[i], widgets[i + 1]])
        for p in pairs:
            p[0].grid(row=curRow, column=curColumn, sticky="w", padx=1, pady=1)
            p[1].grid(row=curRow, column=curColumn + 1, sticky="w", padx=1, pady=1)
            curRow += 1
            if curRow == rows:
                curRow = 0
                curColumn += 2

    def create_general_settings_widgets(self):
        self.general_frame_title = ctk.CTkLabel(
            self.general_frame,
            text="Common Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.general_frame_title.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        # self.tip_label = ctk.CTkLabel(self.general_frame, text="Tip: Hover over settings for information",  font=ctk.CTkFont(size=14))
        # self.tip_label.grid(row=1, column=0, sticky="nsew")

        # create project name label
        self.project_name_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Project Name"
        )
        project_name_label_ttp = CreateToolTip(
            self.project_name_label,
            "The name of the project. This will be used to name the output folder.",
        )
        self.project_name_label.grid(row=1, column=0, sticky="nsew")
        self.project_name_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.project_name_entry.grid(row=1, column=1, sticky="nsew")
        self.project_name_entry.insert(0, self.project_name)
        # create gpu ids label
        self.gpu_ids_label = ctk.CTkLabel(self.general_frame_subframe, text="GPU IDs")
        gpu_ids_label_ttp = CreateToolTip(self.gpu_ids_label, "The GPU IDs to use.")
        self.gpu_ids_label.grid(row=2, column=0, sticky="nsew")
        self.gpu_ids_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.gpu_ids_entry.grid(row=2, column=1, sticky="nsew")
        self.gpu_ids_entry.insert(0, self.gpu_ids)
        # create enable checkpointing label
        self.enable_checkpointing_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Enable Gradient Checkpointing"
        )
        enable_checkpointing_label_ttp = CreateToolTip(
            self.enable_checkpointing_label,
            "RAM saving technique. If enabled, the model will be trained using gradient checkpointing.",
        )
        self.enable_checkpointing_label.grid(row=3, column=0, sticky="nsew")
        # create enable checkpointing checkbox
        self.enable_checkpointing_var = tk.IntVar()
        self.enable_checkpointing_checkbox = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.enable_checkpointing_var
        )
        self.enable_checkpointing_checkbox.grid(row=3, column=1, sticky="nsew")
        self.enable_checkpointing_var.set(self.enable_checkpointing)
        # create use fp16 checkbox
        self.use_fp16_label = ctk.CTkLabel(self.general_frame_subframe, text="Use FP16")
        use_fp16_label_ttp = CreateToolTip(
            self.use_fp16_label,
            "Use FP16. If enabled, the model will be trained using FP16.",
        )
        self.use_fp16_label.grid(row=4, column=0, sticky="nsew")
        # create use fp16 checkbox
        self.use_fp16_var = tk.IntVar()
        self.use_fp16_checkbox = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.use_fp16_var
        )
        self.use_fp16_checkbox.grid(row=4, column=1, sticky="nsew")
        self.use_fp16_var.set(self.use_fp16)
        # create use wandb checkbox
        self.use_wandb_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Use WandB"
        )
        use_wandb_label_ttp = CreateToolTip(
            self.use_wandb_label,
            "Use WandB. If enabled, the model will be logged to WandB.",
        )
        self.use_wandb_label.grid(row=5, column=0, sticky="nsew")
        # create use wandb checkbox
        self.use_wandb_var = tk.IntVar()
        self.use_wandb_checkbox = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.use_wandb_var
        )
        self.use_wandb_checkbox.grid(row=5, column=1, sticky="nsew")
        self.use_wandb_var.set(self.use_wandb)
        # create use tb logger checkbox
        self.use_tb_logger_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Use TB Logger"
        )
        use_tb_logger_label_ttp = CreateToolTip(
            self.use_tb_logger_label,
            "Use TB Logger. If enabled, the model will be logged to TensorBoard.",
        )
        self.use_tb_logger_label.grid(row=6, column=0, sticky="nsew")
        # create use tb logger checkbox
        self.use_tb_logger_var = tk.IntVar()
        self.use_tb_logger_checkbox = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.use_tb_logger_var
        )
        self.use_tb_logger_checkbox.grid(row=6, column=1, sticky="nsew")
        self.use_tb_logger_var.set(self.use_tb_logger)

        # create a label in the middle: "Data"
        self.data_label = ctk.CTkLabel(
            self.general_frame_subframe,
            text="Data Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.data_label.grid(row=7, column=0, sticky="nsew", pady=10)
        # create dataset path label and entry
        self.dataset_path_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Dataset Path"
        )
        dataset_path_label_ttp = CreateToolTip(
            self.dataset_path_label, "The path to the dataset to use."
        )
        self.dataset_path_label.grid(row=8, column=0, sticky="nsew")
        self.dataset_path_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.dataset_path_entry.grid(row=8, column=1, sticky="nsew")
        self.dataset_path_entry.insert(0, self.path_to_lj_dataset)
        self.dataset_path_entry.bind(
            "<FocusOut>",
            lambda event: self.check_dataset_folder(self.dataset_path_entry),
        )

        # create a button to select the dataset path next to the entry
        self.dataset_path_button = ctk.CTkButton(
            self.general_frame_subframe,
            width=10,
            text="...",
            command=lambda: self.browse_for_path_focus(
                self.dataset_path_entry, "folder"
            ),
        )
        self.dataset_path_button.grid(row=8, column=2, sticky="nsew")

        # create train batch size label and entry
        self.train_batch_size_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Train Batch Size"
        )
        train_batch_size_label_ttp = CreateToolTip(
            self.train_batch_size_label,
            "The batch size to use for training, must not be more than the number of training samples.",
        )
        self.train_batch_size_label.grid(row=9, column=0, sticky="nsew")
        self.train_batch_size_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.train_batch_size_entry.grid(row=9, column=1, sticky="nsew")
        self.train_batch_size_entry.insert(0, self.train_batch_size)
        # add a button to trigger calculation of the batch size
        # self.train_batch_size_button = ctk.CTkButton(self.general_frame_subframe,width=10, text="A", command=lambda: self.calculate_training_parameters(self.train_batch_size_entry))
        # self.train_batch_size_button.grid(row=9, column=2, sticky="nsew")
        # create a validation batch size label and entry
        self.val_batch_size_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Validation Batch Size"
        )
        val_batch_size_label_ttp = CreateToolTip(
            self.val_batch_size_label,
            "The batch size to use for validation, must not be more than the number of validation samples.",
        )
        self.val_batch_size_label.grid(row=10, column=0, sticky="nsew")
        self.val_batch_size_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.val_batch_size_entry.grid(row=10, column=1, sticky="nsew")
        self.val_batch_size_entry.insert(0, self.valid_batch_size)
        # add a button to trigger calculation of the batch size
        # self.val_batch_size_button = ctk.CTkButton(self.general_frame_subframe,width=10, text="A", command=lambda: self.calculate_batch_sizes(self.val_batch_size_entry))
        # self.val_batch_size_button.grid(row=10, column=2, sticky="nsew")
        # create a training bold label
        self.training_label = ctk.CTkLabel(
            self.general_frame_subframe,
            text="Training Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.training_label.grid(row=11, column=0, sticky="nsew", pady=10)
        # create steps label and entry
        self.steps_label = ctk.CTkLabel(self.general_frame_subframe, text="Steps")
        steps_label_ttp = CreateToolTip(
            self.steps_label, "The number of steps to train for."
        )
        self.steps_label.grid(row=12, column=0, sticky="nsew")
        self.steps_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.steps_entry.grid(row=12, column=1, sticky="nsew")
        self.steps_entry.insert(0, self.iterations_number)
        # create warmup steps label and entry
        self.warmup_steps_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Warmup Steps"
        )
        warmup_steps_label_ttp = CreateToolTip(
            self.warmup_steps_label, "The number of warmup steps to use."
        )
        self.warmup_steps_label.grid(row=13, column=0, sticky="nsew")
        self.warmup_steps_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.warmup_steps_entry.grid(row=13, column=1, sticky="nsew")
        self.warmup_steps_entry.insert(0, self.warmup_steps)
        # create gradient accumulation steps label and entry
        self.gradient_accumulation_steps_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Gradient Accumulation Steps"
        )
        gradient_accumulation_steps_label_ttp = CreateToolTip(
            self.gradient_accumulation_steps_label,
            "The number of gradient accumulation steps to use.",
        )
        self.gradient_accumulation_steps_label.grid(row=14, column=0, sticky="nsew")
        self.gradient_accumulation_steps_entry = ctk.CTkEntry(
            self.general_frame_subframe
        )
        self.gradient_accumulation_steps_entry.grid(row=14, column=1, sticky="nsew")
        self.gradient_accumulation_steps_entry.insert(0, self.gradient_accumlation)
        # create learning rate label and entry
        self.learning_rate_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Learning Rate"
        )
        learning_rate_label_ttp = CreateToolTip(
            self.learning_rate_label, "The learning rate to use."
        )
        self.learning_rate_label.grid(row=15, column=0, sticky="nsew")
        self.learning_rate_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.learning_rate_entry.grid(row=15, column=1, sticky="nsew")
        self.learning_rate_entry.insert(0, self.learning_rate)
        # create learning rate steps
        self.learning_rate_steps_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Learning Rate Stepping"
        )
        learning_rate_steps_label_ttp = CreateToolTip(
            self.learning_rate_steps_label, "The learning rate stepping behaviour."
        )
        self.learning_rate_steps_label.grid(row=16, column=0, sticky="nsew")
        self.learning_rate_steps_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.learning_rate_steps_entry.grid(row=16, column=1, sticky="nsew")
        self.learning_rate_steps_entry.insert(0, self.learning_rate_steps)
        # create a switch to enable/disable EMA model save
        self.ema_model_save_var = tk.IntVar()
        self.ema_model_save_var.set(self.ema_model_save)
        self.ema_model_save_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Save EMA Model"
        )
        ema_model_save_label_ttp = CreateToolTip(
            self.ema_model_save_label,
            "Whether to save the EMA model. EMA models aren't used for GPT training",
        )
        self.ema_model_save_label.grid(row=17, column=0, sticky="nsew")
        self.ema_model_save_switch = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.ema_model_save_var
        )
        self.ema_model_save_switch.grid(row=17, column=1, sticky="nsew")
        # create a switch to enable/disable state saving
        self.save_state_var = tk.IntVar()
        self.save_state_var.set(self.save_states)
        self.save_state_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Save States"
        )
        save_state_label_ttp = CreateToolTip(
            self.save_state_label,
            "Whether to save the state of the training, disabling this means you won't be able to resume from this training session.",
        )
        self.save_state_label.grid(row=18, column=0, sticky="nsew")
        self.save_state_switch = ctk.CTkSwitch(
            self.general_frame_subframe, variable=self.save_state_var
        )
        self.save_state_switch.grid(row=18, column=1, sticky="nsew")
        # create a label and entry for training seed
        self.training_seed_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Training Seed"
        )
        training_seed_label_ttp = CreateToolTip(
            self.training_seed_label, "The seed to use for training."
        )
        self.training_seed_label.grid(row=19, column=0, sticky="nsew")
        self.training_seed_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.training_seed_entry.grid(row=19, column=1, sticky="nsew")
        self.training_seed_entry.insert(0, self.training_seed)

        self.logger_label = ctk.CTkLabel(
            self.general_frame_subframe,
            text="Logger Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logger_label.grid(row=20, column=0, sticky="nsew", pady=10)
        # create print status frequency label and entry
        self.print_status_frequency_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Print Status Frequency"
        )
        print_status_frequency_label_ttp = CreateToolTip(
            self.print_status_frequency_label,
            "The frequency to print the status of the training.",
        )
        self.print_status_frequency_label.grid(row=21, column=0, sticky="nsew")
        self.print_status_frequency_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.print_status_frequency_entry.grid(row=21, column=1, sticky="nsew")
        self.print_status_frequency_entry.insert(0, self.print_status_frequency)
        # create save frequency label and entry
        self.save_frequency_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Save Checkpoint Frequency"
        )
        save_frequency_label_ttp = CreateToolTip(
            self.save_frequency_label, "The frequency to save the model."
        )
        self.save_frequency_label.grid(row=22, column=0, sticky="nsew")
        self.save_frequency_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.save_frequency_entry.grid(row=22, column=1, sticky="nsew")
        self.save_frequency_entry.insert(0, self.save_checkpoint_frequency)
        # create visual debug frequency label and entry
        self.visual_debug_rate_label = ctk.CTkLabel(
            self.general_frame_subframe, text="Visual Debug Frequency"
        )
        visual_debug_rate_label_ttp = CreateToolTip(
            self.visual_debug_rate_label,
            "The frequency to save the visual debug images.",
        )
        self.visual_debug_rate_label.grid(row=23, column=0, sticky="nsew")
        self.visual_debug_rate_entry = ctk.CTkEntry(self.general_frame_subframe)
        self.visual_debug_rate_entry.grid(row=23, column=1, sticky="nsew")
        self.visual_debug_rate_entry.insert(0, self.visual_debug_rate)

    def start_tts_api(self, path):
        # self.playground_model_path_entry.configure(state='disabled')
        # check if TextToSpeech is already loaded
        sys.path.append("./tortoise-tts-fast/tortoise")
        from api import TextToSpeech
        from inference import save_gen_with_voicefix
        from tortoise.utils.audio import load_required_audio, check_audio

        if path == None or path == "":
            self.playground_api = TextToSpeech(
                high_vram=True,
                kv_cache=True,
                ar_checkpoint=None,
            )
            return
        if path.get() == "" or ".pth" not in path.get():
            print("No model selected, make sure you have a pth file selected.")
            return
        else:
            self.playground_api = TextToSpeech(
                high_vram=True,
                kv_cache=True,
                ar_checkpoint=path.get() if path != None else None,
            )

    def check_dataset_folder(self, dataset_path):
        # list files in dataset path
        try:
            files = os.listdir(dataset_path.get())
        except:
            return
        wavs = True
        train = True
        Valid = True
        # check if wavs folder exists
        if "wavs" not in files:
            wavs = False
        # check if train.txt exists
        if "train.txt" not in files:
            train = False
        # check if valid.txt exists
        if "valid.txt" not in files:
            if "val.txt" not in files:
                Valid = False
            else:
                os.rename("val.txt", "valid.txt")
        # if any of the above are false, return false
        if wavs == False or train == False or Valid == False:
            # show error message
            messagebox.showerror(
                "Error",
                "Dataset folder is not valid, please check the documentation for more info.",
            )
            dataset_path.delete(0, tk.END)

    def browse_for_path_focus(self, entry_box, type="file"):
        # get the path from the user
        if type == "file":
            path = fd.askopenfilename()
        else:
            path = fd.askdirectory()
        # set the path to the entry box
        # delete entry box text
        entry_box.focus_set()
        entry_box.delete(0, tk.END)
        entry_box.insert(0, path)
        self.focus_set()

    def toggle_runpod_mode(self):
        toggle = self.cloud_mode_var.get()
        # flip self.toggle
        if toggle == True:
            toggle = False
            self.sidebar_button_12.configure(text="Export for Cloud!")
        else:
            toggle = True
            self.sidebar_button_12.configure(text="Start Training!")

    def create_advanced_settings_widgets(self):
        self.advanced_settings_frame_title = ctk.CTkLabel(
            self.advanced_settings_frame,
            text="Advanced Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.advanced_settings_frame_title.grid(row=0, column=0, padx=20, pady=20)

        # create label and entry to model type
        self.model_type_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Model Type"
        )
        model_type_label_ttp = CreateToolTip(
            self.model_type_label, "The model type you're training."
        )
        self.model_type_label.grid(row=0, column=0, sticky="nsew")
        # create entry to model type
        self.model_type_entry = ctk.CTkEntry(self.advanced_settings_frame_subframe)
        self.model_type_entry.grid(row=0, column=1, sticky="nsew")
        self.model_type_entry.insert(0, self.model)
        # create scale label and entry
        self.scale_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Scale"
        )
        scale_label_ttp = CreateToolTip(self.scale_label, "The scale of the model.")
        self.scale_label.grid(row=1, column=0, sticky="nsew")
        self.scale_entry = ctk.CTkEntry(self.advanced_settings_frame_subframe)
        self.scale_entry.grid(row=1, column=1, sticky="nsew")
        self.scale_entry.insert(0, self.scale)
        # create start step label and entry
        self.start_step_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Start Step"
        )
        start_step_label_ttp = CreateToolTip(
            self.start_step_label, "The step to start training from."
        )
        self.start_step_label.grid(row=2, column=0, sticky="nsew")
        self.start_step_entry = ctk.CTkEntry(self.advanced_settings_frame_subframe)
        self.start_step_entry.grid(row=2, column=1, sticky="nsew")
        self.start_step_entry.insert(0, self.start_step)
        # create bold title dataset
        self.dataset_title = ctk.CTkLabel(
            self.advanced_settings_frame_subframe,
            text="Dataset",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.dataset_title.grid(row=3, column=0, sticky="nsew")
        # create training workers label and entry
        self.training_workers_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Training Workers"
        )
        training_workers_label_ttp = CreateToolTip(
            self.training_workers_label, "The number of workers to use for training."
        )
        self.training_workers_label.grid(row=4, column=0, sticky="nsew")
        self.training_workers_entry = ctk.CTkEntry(
            self.advanced_settings_frame_subframe
        )
        self.training_workers_entry.grid(row=4, column=1, sticky="nsew")
        self.training_workers_entry.insert(0, self.train_num_workers)
        # create validation workers label and entry
        self.validation_workers_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Validation Workers"
        )
        validation_workers_label_ttp = CreateToolTip(
            self.validation_workers_label,
            "The number of workers to use for validation.",
        )
        self.validation_workers_label.grid(row=5, column=0, sticky="nsew")
        self.validation_workers_entry = ctk.CTkEntry(
            self.advanced_settings_frame_subframe
        )
        self.validation_workers_entry.grid(row=5, column=1, sticky="nsew")
        self.validation_workers_entry.insert(0, self.valid_num_workers)
        # create path to ar model
        self.ar_model_path_label = ctk.CTkLabel(
            self.advanced_settings_frame_subframe, text="Path to AR Model"
        )
        ar_model_path_label_ttp = CreateToolTip(
            self.ar_model_path_label, "The path to the AR model."
        )
        self.ar_model_path_label.grid(row=6, column=0, sticky="nsew")
        self.ar_model_path_entry = ctk.CTkEntry(self.advanced_settings_frame_subframe)
        self.ar_model_path_entry.grid(row=6, column=1, sticky="nsew")
        self.ar_model_path_entry.insert(0, self.path_to_ar_model)
        # create path to dvae model

    def create_playground_widgets(self):
        self.playground_frame_title = ctk.CTkLabel(
            self.playground_frame,
            text="Model Playground",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.playground_frame_title.grid(row=0, column=0, padx=20, pady=20)
        # create a label
        # self.playground_label = ctk.CTkLabel(self.playground_frame_subframe, text="Enter a model path to load the model to memory", font=ctk.CTkFont(size=15, weight="bold"))
        # self.playground_label.grid(row=0, sticky="n",columnspan=3)
        # create empty label

        # create label and entry and button to model path
        self.playground_model_path_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="AR Model Path"
        )
        playground_model_path_label_ttp = CreateToolTip(
            self.playground_model_path_label, "The path to the AR model."
        )
        self.playground_model_path_label.grid(row=1, column=0, sticky="nsew")
        self.playground_model_path_entry = ctk.CTkEntry(
            self.playground_frame_subframe, width=100
        )
        self.playground_model_path_entry.grid(row=1, column=1, sticky="nsew")
        self.playground_model_path_entry.insert(0, self.playground_model_path)
        self.playground_model_path_entry.bind(
            "<FocusOut>",
            lambda event: self.start_tts_api(self.playground_model_path_entry),
        )

        self.playground_model_path_button = ctk.CTkButton(
            self.playground_frame_subframe,
            width=10,
            text="...",
            command=lambda: self.browse_for_path_focus(
                self.playground_model_path_entry, "file"
            ),
        )
        self.playground_model_path_button.grid(row=1, column=2, sticky="nsew")
        # create text box for text input
        self.playground_text_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Text"
        )
        playground_text_label_ttp = CreateToolTip(
            self.playground_text_label, "The text to use for the model."
        )
        self.playground_text_label.grid(row=2, column=0, sticky="nsew")
        self.playground_text_entry = ctk.CTkEntry(
            self.playground_frame_subframe, width=100
        )
        self.playground_text_entry.grid(row=2, column=1, sticky="nsew")
        self.playground_text_entry.insert(0, self.playground_text)

        # create label and entry for seed
        self.playground_seed_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Seed"
        )
        playground_seed_label_ttp = CreateToolTip(
            self.playground_seed_label, "The seed to use for the model."
        )
        self.playground_seed_label.grid(row=3, column=0, sticky="nsew")
        self.playground_seed_entry = ctk.CTkEntry(self.playground_frame_subframe)
        self.playground_seed_entry.grid(row=3, column=1, sticky="nsew")
        self.playground_seed_entry.insert(0, self.playground_seed)
        # create quality selection
        self.playground_quality_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Quality Preset"
        )
        playground_quality_label_ttp = CreateToolTip(
            self.playground_quality_label, "The quality of the model."
        )
        self.playground_quality_label.grid(row=4, column=0, sticky="nsew")
        self.playground_quality_entry = ctk.CTkOptionMenu(
            self.playground_frame_subframe,
            values=["ultra_fast", "very_fast", "fast", "standard", "high_quality"],
        )
        self.playground_quality_entry.grid(row=4, column=1, sticky="nsew")
        # create amount of canidates to generate label and entry
        self.playground_candidates_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Candidates"
        )
        playground_candidates_label_ttp = CreateToolTip(
            self.playground_candidates_label, "The amount of candidates to generate."
        )
        self.playground_candidates_label.grid(row=5, column=0, sticky="nsew")
        self.playground_candidates_entry = ctk.CTkEntry(self.playground_frame_subframe)
        self.playground_candidates_entry.grid(row=5, column=1, sticky="nsew")
        self.playground_candidates_entry.insert(0, self.playground_candidates)
        # create compare to original switch
        self.playground_compare_to_original_var = tk.IntVar()
        self.playground_compare_to_original_var.set(self.playground_compare)
        # label
        self.playground_compare_to_original_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Compare to Original"
        )
        playground_compare_to_original_label_ttp = CreateToolTip(
            self.playground_compare_to_original_label,
            "Will generate a comparison between the original and the finetuned model",
        )
        self.playground_compare_to_original_label.grid(row=6, column=0, sticky="nsew")
        # ctk switch
        self.playground_compare_to_original_switch = ctk.CTkSwitch(
            self.playground_frame_subframe,
            variable=self.playground_compare_to_original_var,
        )
        self.playground_compare_to_original_switch.grid(row=6, column=1, sticky="nsew")

        # create use training data switch
        self.playground_use_training_data_var = tk.IntVar()
        self.playground_use_training_data_var.set(self.playground_use_training_data)
        # label
        self.playground_use_training_data_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Use Training Data as Voice"
        )
        playground_use_training_data_label_ttp = CreateToolTip(
            self.playground_use_training_data_label,
            "Whether to use training data or not.",
        )
        self.playground_use_training_data_label.grid(row=7, column=0, sticky="nsew")
        # ctk switch
        self.playground_use_training_data_switch = ctk.CTkSwitch(
            self.playground_frame_subframe,
            variable=self.playground_use_training_data_var,
            command=self.enable_voice_dir,
        )
        self.playground_use_training_data_switch.grid(row=7, column=1, sticky="nsew")

        # create voice directory label and entry
        self.playground_voice_dir_label = ctk.CTkLabel(
            self.playground_frame_subframe, text="Voice Directory", state="disabled"
        )
        playground_voice_dir_label_ttp = CreateToolTip(
            self.playground_voice_dir_label, "The directory of the voice."
        )
        self.playground_voice_dir_label.grid(row=8, column=0, sticky="nsew")
        self.playground_voice_dir_entry = ctk.CTkEntry(
            self.playground_frame_subframe, width=100, state="disabled"
        )
        self.playground_voice_dir_entry.grid(row=8, column=1, sticky="nsew")
        self.playground_voice_dir_entry.insert(0, self.playground_voice_dir)
        # create generate button
        self.playground_generate_button = ctk.CTkButton(
            self.playground_frame_subframe,
            text="Generate",
            command=lambda: self.generate_playground(),
        )
        self.playground_generate_button.grid(row=10, column=0, sticky="nsew")

    def enable_voice_dir(self):
        if self.playground_use_training_data_var.get() != 1:
            self.playground_voice_dir_label.configure(state="normal")
            self.playground_voice_dir_entry.configure(state="normal")
        else:
            self.playground_voice_dir_label.configure(state="disabled")
            self.playground_voice_dir_entry.configure(state="disabled")

    def generate_playground(self):
        import torch
        from tortoise.inference import save_gen_with_voicefix
        from tortoise.utils.audio import load_required_audio, check_audio

        def get_voices(voice_dir):
            voices: Dict[str, List[str]] = {}
            subj = voice_dir
            sub = os.path.basename(subj)
            if os.path.isdir(subj):
                voices[sub] = (
                    list(glob(f"{subj}/*.wav"))
                    + list(glob(f"{subj}/*.mp3"))
                    + list(glob(f"{subj}/*.pth"))
                )
            return voices

        @contextmanager
        def timeit(desc=""):
            start = time()
            yield
            print(f"{desc} took {time() - start:.2f} seconds")

        def process_playground(original=False):
            # try and find the dataset path from the model path
            # current model path
            model_path = self.playground_model_path_entry.get()
            # if ends with pth
            if model_path.endswith(".pth"):
                # get the full path to the parent directory
                train_path = os.path.dirname(os.path.dirname(model_path))
                # list files in train path
                files = os.listdir(train_path)
                # find the yaml file
                for file in files:
                    if file.endswith(".yaml"):
                        # get the full path to the yaml file
                        yaml_path = os.path.join(train_path, file)
                        # open the yaml file
                        with open(yaml_path, "r") as stream:
                            # load the yaml file
                            data_loaded = yaml.load(stream)
                            # get the dataset path
                            voice_dir = data_loaded["datasets"]["train"][
                                "path"
                            ].replace("train.txt", "wavs")
                            if original == False:
                                k = data_loaded["name"]
                            else:
                                k = "original_" + data_loaded["name"]
                            if self.playground_use_training_data_var.get() == 0:
                                voice_dir = self.playground_voice_dir_entry.get()
                                if original == False:
                                    k = os.path.basename(voice_dir)
                                else:
                                    k = "original_" + os.path.basename(voice_dir)
                            if not os.path.isdir(voice_dir):
                                messagebox.showerror(
                                    "Error", "Could not find training data directory."
                                )
                                return
                            break
            voice_samples = None
            conditioning_latents = None
            # k = os.path.basename(voice_dir)
            # if is a directory, use all voices in it
            if os.path.isdir(voice_dir):
                voices = get_voices(voice_dir)
                paths = voices[os.path.basename(voice_dir)]
                if len(paths) == 1 and paths[0].endswith(".pth"):
                    voice_samples = None
                    conditioning_latents = torch.load(paths[0])
                else:
                    conds = []
                    for cond_path in paths:
                        c = load_required_audio(cond_path)
                        conds.append(c)
                    voice_samples = conds
                    conditioning_latents = None
            with timeit(f"Generating candidates)"):
                gen, dbg_state = self.playground_api.tts_with_preset(
                    self.playground_text_entry.get(),
                    k=int(self.playground_candidates_entry.get()),
                    voice_samples=voice_samples,
                    conditioning_latents=conditioning_latents,
                    preset=self.playground_quality_entry.get(),
                    use_deterministic_seed=int(self.playground_seed_entry.get())
                    if self.playground_seed_entry.get() != ""
                    else None,
                    return_deterministic_state=True,
                    # cvvp_amount=args.cvvp_amount,
                    # half=args.half,
                    # original_tortoise=args.original_tortoise,
                )

            if isinstance(gen, list):
                for j, g in enumerate(gen):
                    save_gen_with_voicefix(
                        g,
                        os.path.join("results", f"{k}_{j}.wav"),
                        voicefixer=False,  # disabled for now as the quality is not good
                    )
            else:
                save_gen_with_voicefix(
                    gen,
                    os.path.join("results", f"{k}_{k}.wav"),
                    voicefixer=False,  # disabled for now as the quality is not good
                )

        if self.playground_api == None:
            self.start_tts_api(self.playground_model_path_entry)
        if self.playground_compare_to_original_var.get() == 1:
            # run twice, once with original and once with new
            # original
            print("Generating from finetuned model")
            process_playground()
            print("Generating from original model")
            self.start_tts_api(None)
            process_playground(original=True)
            print("Reloading finetuned model")
            self.start_tts_api(self.playground_model_path_entry)
        else:
            process_playground()

    def txt_file_lines(self, p: str) -> int:
        return len(Path(p).read_text(encoding="utf-8").strip().split("\n"))

    def calculate_training_parameters(self):
        def div_spillover(n: int, bs: int) -> int:  # returns new batch size
            epoch_steps, remain = divmod(n, bs)
            if epoch_steps * 2 > bs:
                return bs  # don't bother optimising this stuff if epoch_steps are high
            if not remain:
                return bs  # unlikely but still

            if (
                remain * 2 < bs
            ):  # "easier" to get rid of remainder -- should increase bs
                target_bs = n // epoch_steps
            else:  # easier to increase epoch_steps by 1 -- decrease bs
                target_bs = n // (epoch_steps + 1)
            assert n % target_bs < epoch_steps + 2  # should be very few extra
            return target_bs

        try:
            training_samples = self.txt_file_lines(
                self.dataset_path_entry.get() + "/train.txt"
            )
            val_samples = self.txt_file_lines(
                self.dataset_path_entry.get() + "/valid.txt"
            )
        except:
            # show error message
            messagebox.showerror(
                "Error",
                "Could not find dataset files. Please check the path and try again.",
            )
            return
        if training_samples < int(self.train_batch_size_entry.get()):
            print(
                "WARNING: dataset is smaller than a single batch. This will almost certainly perform poorly. Trying anyway"
            )
            train_bs = training_samples
        else:
            train_bs = div_spillover(
                training_samples, int(self.train_batch_size_entry.get())
            )
        if val_samples < int(self.val_batch_size_entry.get()):
            val_bs = val_samples
        else:
            val_bs = div_spillover(val_samples, int(self.val_batch_size_entry.get()))
        steps_per_epoch = training_samples // train_bs
        first_decay = ast.literal_eval(self.learning_rate_steps_entry.get())[0]
        lr_decay_epochs = [
            first_decay,
            first_decay * 2,
            first_decay * 14 // 5,
            first_decay * 18 // 5,
        ]
        lr_decay_steps = str([steps_per_epoch * e for e in lr_decay_epochs])
        print_freq = min(100, max(20, steps_per_epoch))
        val_freq = save_checkpoint_freq = print_freq * 3
        self.train_batch_size_entry.delete(0, tk.END)
        self.train_batch_size_entry.insert(0, str(train_bs))
        self.val_batch_size_entry.delete(0, tk.END)
        self.val_batch_size_entry.insert(0, str(val_bs))
        # self.steps_entry.delete(0, tk.END)
        # self.steps_entry.insert(0, str(steps_per_epoch))
        self.learning_rate_steps_entry.delete(0, tk.END)
        self.learning_rate_steps_entry.insert(0, str(lr_decay_steps))
        # self.print_status_frequency_entry.delete(0, tk.END) #disabled for now as it's annoying
        # self.print_status_frequency_entry.insert(0, str(print_freq)) #disabled for now as it's annoying
        # self.save_frequency_entry.delete(0, tk.END) #disabled for now as it's annoying
        # self.save_frequency_entry.insert(0, str(val_freq)) #disabled for now as it's annoying

    def update_DLAS(self):
        new_version = (
            subprocess.check_output(
                [
                    "git",
                    "ls-remote",
                    "https://github.com/152334H/DL-Art-School.git",
                    "master",
                ],
                cwd=Path(__file__).resolve().parent,
            )
            .strip()
            .decode()[0:7]
        )
        with open("DLAS_hash.cfg", "w") as f:
            f.write(new_version)
        subprocess.run(["git", "stash"], cwd=Path(__file__).resolve().parent)
        subprocess.run(["git", "pull"], cwd=Path(__file__).resolve().parent)
        print("pulled")
        # restart the app
        restart(self)

    def packageForCloud(self):
        # future work
        # check if there's an export folder in the cwd and if not create one
        if not os.path.exists("exports"):
            os.mkdir("exports")
        exportDir = self.export_name
        if not os.path.exists("exports" + os.sep + exportDir):
            os.mkdir("exports" + os.sep + exportDir)
        else:
            # remove the old export folder
            shutil.rmtree("exports" + os.sep + exportDir)
            os.mkdir("exports" + os.sep + exportDir)
        self.full_export_path = "exports" + os.sep + exportDir
        os.mkdir(self.full_export_path + os.sep + "output")
        os.mkdir(self.full_export_path + os.sep + "datasets")

        # check if self.model_path is a directory
        if os.path.isdir(self.model_path):
            # get the directory name
            model_name = os.path.basename(self.model_path)
            # check if model_name can be an int
            try:
                model_name = int(model_name)
                # get the parent directory name
                model_name = os.path.basename(os.path.dirname(self.model_path))
            except:
                pass
            # create a folder in the export folder with the model name
            if not os.path.exists(
                self.full_export_path + os.sep + "input_model" + os.sep + model_name
            ):
                os.mkdir(
                    self.full_export_path + os.sep + "input_model" + os.sep + model_name
                )
            # copy the model to the export folder
            shutil.copytree(
                self.model_path,
                self.full_export_path
                + os.sep
                + "input_model"
                + os.sep
                + model_name
                + os.sep,
                dirs_exist_ok=True,
            )
            self.model_path = "input_model" + "/" + model_name
        if os.path.isdir(self.vae_path):
            # get the directory name
            vae_name = os.path.basename(self.vae_path)
            # create a folder in the export folder with the model name
            if not os.path.exists(
                self.full_export_path + os.sep + "input_vae_model" + os.sep + vae_name
            ):
                os.mkdir(
                    self.full_export_path
                    + os.sep
                    + "input_vae_model"
                    + os.sep
                    + vae_name
                )
            # copy the model to the export folder
            shutil.copytree(
                self.vae_path,
                self.full_export_path
                + os.sep
                + "input_vae_model"
                + os.sep
                + vae_name
                + os.sep
                + vae_name,
                dirs_exist_ok=True,
            )
            self.vae_path = "input_vae_model" + "/" + vae_name
        if self.output_path == "":
            self.output_path = "output"
        else:
            # get the dirname
            output_name = os.path.basename(self.output_path)
            # create a folder in the export folder with the model name
            if not os.path.exists(
                self.full_export_path + os.sep + "output" + os.sep + output_name
            ):
                os.mkdir(
                    self.full_export_path + os.sep + "output" + os.sep + output_name
                )
            self.output_path = "output" + "/" + output_name
        # loop through the concepts and add them to the export folder
        concept_counter = 0
        new_concepts = []
        for concept in self.concepts:
            concept_counter += 1
            concept_data_dir = os.path.basename(concept["instance_data_dir"])
            # concept is a dict
            # get the concept name
            concept_name = concept["instance_prompt"]
            # if concept_name is ''
            if concept_name == "":
                concept_name = "concept_" + str(concept_counter)

            # create a folder in the export/datasets folder with the concept name
            # if not os.path.exists(self.full_export_path + os.sep + 'datasets'+ os.sep + concept_name):
            #    os.mkdir(self.full_export_path + os.sep + 'datasets'+ os.sep + concept_name)
            # copy the concept to the export folder
            shutil.copytree(
                concept["instance_data_dir"],
                self.full_export_path + os.sep + "datasets" + os.sep + concept_data_dir,
                dirs_exist_ok=True,
            )
            concept_class_name = concept["class_prompt"]
            if concept_class_name == "":
                # if class_data_dir is ''
                if concept["class_data_dir"] != "":
                    concept_class_name = "class_" + str(concept_counter)
                    # create a folder in the export/datasets folder with the concept name
                    if not os.path.exists(
                        self.full_export_path
                        + os.sep
                        + "datasets"
                        + os.sep
                        + concept_class_name
                    ):
                        os.mkdir(
                            self.full_export_path
                            + os.sep
                            + "datasets"
                            + os.sep
                            + concept_class_name
                        )
                    # copy the concept to the export folder
                    shutil.copytree(
                        concept["class_data_dir"],
                        self.full_export_path
                        + os.sep
                        + "datasets"
                        + os.sep
                        + concept_class_name
                        + os.sep,
                        dirs_exist_ok=True,
                    )
            else:
                if concept["class_data_dir"] != "":
                    # create a folder in the export/datasets folder with the concept name
                    if not os.path.exists(
                        self.full_export_path
                        + os.sep
                        + "datasets"
                        + os.sep
                        + concept_class_name
                    ):
                        os.mkdir(
                            self.full_export_path
                            + os.sep
                            + "datasets"
                            + os.sep
                            + concept_class_name
                        )
                    # copy the concept to the export folder
                    shutil.copytree(
                        concept["class_data_dir"],
                        self.full_export_path
                        + os.sep
                        + "datasets"
                        + os.sep
                        + concept_class_name
                        + os.sep,
                        dirs_exist_ok=True,
                    )
            # create a new concept dict
            new_concept = {}
            new_concept["instance_prompt"] = concept_name
            new_concept["instance_data_dir"] = "datasets" + "/" + concept_data_dir
            new_concept["class_prompt"] = concept_class_name
            new_concept["class_data_dir"] = (
                "datasets" + "/" + concept_class_name
                if concept_class_name != ""
                else ""
            )
            new_concept["do_not_balance"] = concept["do_not_balance"]
            new_concept["use_sub_dirs"] = concept["use_sub_dirs"]
            new_concepts.append(new_concept)
        # make scripts folder
        self.save_concept_to_json(
            filename=self.full_export_path + os.sep + "stabletune_concept_list.json",
            preMadeConcepts=new_concepts,
        )
        if not os.path.exists(self.full_export_path + os.sep + "scripts"):
            os.mkdir(self.full_export_path + os.sep + "scripts")
        # copy the scripts/trainer.py the scripts folder
        shutil.copy(
            "scripts" + os.sep + "trainer.py",
            self.full_export_path + os.sep + "scripts" + os.sep + "trainer.py",
        )
        # copy trainer_utils.py to the scripts folder
        shutil.copy(
            "scripts" + os.sep + "trainer_util.py",
            self.full_export_path + os.sep + "scripts" + os.sep + "trainer_util.py",
        )
        # copy converters.py to the scripts folder
        shutil.copy(
            "scripts" + os.sep + "converters.py",
            self.full_export_path + os.sep + "scripts" + os.sep + "converters.py",
        )
        # copy model_util.py to the scripts folder
        shutil.copy(
            "scripts" + os.sep + "model_util.py",
            self.full_export_path + os.sep + "scripts" + os.sep + "model_util.py",
        )
        # copy clip_seg to the scripts folder
        shutil.copy(
            "scripts" + os.sep + "clip_segmentation.py",
            self.full_export_path
            + os.sep
            + "scripts"
            + os.sep
            + "clip_segmentation.py",
        )

    def load_config(self, file_name=None):
        # load the configure file
        # ask the user for a file name
        if file_name == None:
            file_name = fd.askopenfilename(
                title="Select file", filetypes=(("yaml files", "*.*"),)
            )
        if file_name == "":
            return
        # load the configure file
        with open(file_name, "r") as f:
            configure = yaml.load(f)

        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, configure["name"])
        self.gpu_ids_entry.delete(0, tk.END)
        self.gpu_ids_entry.insert(0, str(configure["gpu_ids"]))
        self.enable_checkpointing_var.set(configure["checkpointing_enabled"])
        self.use_fp16_var.set(configure["fp16"])
        self.use_wandb_var.set(configure["wandb"])
        self.use_tb_logger_var.set(configure["use_tb_logger"])
        self.dataset_path_entry.delete(0, tk.END)
        self.dataset_path_entry.insert(
            0, configure["datasets"]["train"]["path"].replace("train.txt", "")
        )
        self.train_batch_size_entry.delete(0, tk.END)
        self.train_batch_size_entry.insert(
            0, str(configure["datasets"]["train"]["batch_size"])
        )
        self.val_batch_size_entry.delete(0, tk.END)
        self.val_batch_size_entry.insert(
            0, str(configure["datasets"]["val"]["batch_size"])
        )
        self.steps_entry.delete(0, tk.END)
        self.steps_entry.insert(0, str(configure["train"]["niter"]))
        self.warmup_steps_entry.delete(0, tk.END)
        self.warmup_steps_entry.insert(0, str(configure["train"]["warmup_iter"]))
        self.gradient_accumulation_steps_entry.delete(0, tk.END)
        self.gradient_accumulation_steps_entry.insert(
            0, str(configure["train"]["mega_batch_factor"])
        )
        self.learning_rate_entry.delete(0, tk.END)
        self.learning_rate_entry.insert(
            0, str(configure["steps"]["gpt_train"]["optimizer_params"]["lr"])
        )
        self.learning_rate_steps_entry.delete(0, tk.END)
        self.learning_rate_steps_entry.insert(
            0, str(configure["train"]["gen_lr_steps"])
        )
        self.print_status_frequency_entry.delete(0, tk.END)
        self.print_status_frequency_entry.insert(
            0, str(configure["logger"]["print_freq"])
        )
        self.save_frequency_entry.delete(0, tk.END)
        self.save_frequency_entry.insert(
            0, str(configure["logger"]["save_checkpoint_freq"])
        )
        self.visual_debug_rate_entry.delete(0, tk.END)
        self.visual_debug_rate_entry.insert(
            0, str(configure["logger"]["visual_debug_rate"])
        )

        self.model_type_entry.delete(0, tk.END)
        self.model_type_entry.insert(0, configure["model"])
        self.scale_entry.delete(0, tk.END)
        self.scale_entry.insert(0, str(configure["scale"]))
        self.start_step_entry.delete(0, tk.END)
        self.start_step_entry.insert(0, str(configure["start_step"]))
        self.training_workers_entry.delete(0, tk.END)
        self.training_workers_entry.insert(
            0, str(configure["datasets"]["train"]["n_workers"])
        )
        self.validation_workers_entry.delete(0, tk.END)
        self.validation_workers_entry.insert(
            0, str(configure["datasets"]["val"]["n_workers"])
        )
        self.ar_model_path_entry.delete(0, tk.END)
        self.ar_model_path_entry.insert(0, configure["path"]["pretrain_model_gpt"])
        # self.dvae_model_path_entry.delete(0, tk.END)
        # self.dvae_model_path_entry.insert(0, configure["path"]["pretrain_model_dvae"])
        self.update()

    def process_inputs(self, export=None):
        training_samples = self.txt_file_lines(
            self.dataset_path_entry.get() + "/train.txt"
        )
        val_samples = self.txt_file_lines(self.dataset_path_entry.get() + "/valid.txt")
        # collect and process all the inputs
        self.project_name = self.project_name_entry.get().replace(" ", "_")
        self.gpu_ids = ast.literal_eval(self.gpu_ids_entry.get())
        self.enable_checkpointing_var = bool(self.enable_checkpointing_var.get())
        self.use_fp16 = bool(self.use_fp16_var.get())
        self.use_wandb = bool(self.use_wandb_var.get())
        self.use_tb_logger = bool(self.use_tb_logger_var.get())
        self.train_batch_size = int(self.train_batch_size_entry.get())
        if self.train_batch_size > training_samples:
            self.train_batch_size = training_samples
            print(
                "Warning: train batch size is larger than the number of training samples. Setting train batch size to the number of training samples."
            )
        self.valid_batch_size = int(self.val_batch_size_entry.get())
        if self.valid_batch_size > val_samples:
            self.valid_batch_size = val_samples
            print(
                "Warning: validation batch size is larger than the number of validation samples. Setting validation batch size to the number of validation samples."
            )
        self.path_to_lj_dataset = self.dataset_path_entry.get()
        self.path_to_train = os.path.join(self.path_to_lj_dataset, "train.txt")
        self.path_to_valid = os.path.join(self.path_to_lj_dataset, "valid.txt")
        self.iterations_number = int(self.steps_entry.get())
        self.warmup_steps = int(self.warmup_steps_entry.get())
        self.gradient_accumlation_steps = int(
            self.gradient_accumulation_steps_entry.get()
        )
        if (
            self.gradient_accumlation_steps > self.train_batch_size
            or self.gradient_accumlation_steps > training_samples
            or self.gradient_accumlation_steps > val_samples
        ):
            # find the smallest number that is a divisor of the batch size and the number of samples
            self.gradient_accumlation_steps = 1
            print(
                "Warning: gradient accumulation steps is larger than the number of training samples or validation samples or train batch size. Setting gradient accumulation steps to 1."
            )
        self.learning_rate = self.learning_rate_entry.get()
        self.learning_rate_steps = ast.literal_eval(
            self.learning_rate_steps_entry.get()
        )
        self.print_status_frequency = int(self.print_status_frequency_entry.get())
        self.save_frequency = int(self.save_frequency_entry.get())
        self.visual_debug_rate = int(self.visual_debug_rate_entry.get())
        self.model = self.model_type_entry.get()
        self.scale = int(self.scale_entry.get())
        self.start_step = int(self.start_step_entry.get())
        self.train_num_workers = int(self.training_workers_entry.get())
        self.valid_num_workers = int(self.validation_workers_entry.get())
        self.path_to_ar_model = self.ar_model_path_entry.get()
        self.manual_seed = int(self.training_seed_entry.get())
        self.ema_enabled = bool(self.ema_model_save_var.get())
        self.save_states = bool(self.save_state_var.get())
        # self.path_to_dvae_model = self.dvae_model_path_entry.get()

        self.base_config["name"] = self.project_name
        self.base_config["gpu_ids"] = "gpu_ids_val"
        self.base_config["checkpointing_enabled"] = self.enable_checkpointing_var
        self.base_config["fp16"] = self.use_fp16
        self.base_config["wandb"] = self.use_wandb
        self.base_config["use_tb_logger"] = self.use_tb_logger

        # dataset settings
        self.base_config["datasets"]["train"]["name"] = self.project_name
        self.base_config["datasets"]["train"]["path"] = self.path_to_train
        self.base_config["datasets"]["train"]["batch_size"] = self.train_batch_size
        self.base_config["datasets"]["train"]["n_workers"] = self.train_num_workers
        self.base_config["datasets"]["val"]["name"] = self.project_name
        self.base_config["datasets"]["val"]["path"] = self.path_to_valid
        self.base_config["datasets"]["val"]["batch_size"] = self.valid_batch_size
        self.base_config["datasets"]["val"]["n_workers"] = self.valid_num_workers

        # path settings
        self.base_config["path"]["pretrain_model_gpt"] = self.path_to_ar_model
        # train settings
        self.base_config["train"]["niter"] = self.iterations_number
        self.base_config["train"]["warmup_iter"] = self.warmup_steps
        self.base_config["train"]["mega_batch_factor"] = self.gradient_accumlation_steps
        self.base_config["steps"]["gpt_train"]["optimizer_params"][
            "lr"
        ] = "learning_rate_val"
        self.base_config["train"]["gen_lr_steps"] = "multi_step_lr_steps_val"
        self.base_config["train"]["ema_enabled"] = self.ema_enabled
        self.base_config["train"]["manual_seed"] = self.manual_seed
        # logger settings
        self.base_config["logger"]["print_freq"] = self.print_status_frequency
        self.base_config["logger"]["save_checkpoint_freq"] = self.save_frequency
        self.base_config["logger"]["visual_debug_rate"] = self.visual_debug_rate
        self.base_config["logger"]["disable_state_saving"] = (
            True if self.save_states == False else False
        )
        # fix yaml
        with open("experiments/" + self.project_name + "_config.yaml", "w") as f:
            yaml.dump(self.base_config, f)
        # fix yaml bullshit, rumel is not saving float and array values correctly
        with open("experiments/" + self.project_name + "_config.yaml", "r") as f:
            data = f.read()
            data = data.replace("lr: ", "lr: !!float ")
            data = data.replace("learning_rate_val", str(self.learning_rate))
            data = data.replace("weight_decay: ", "weight_decay: !!float ")
            data = data.replace("gpu_ids_val", str(self.gpu_ids))
            data = data.replace(
                "multi_step_lr_steps_val", str(self.learning_rate_steps)
            )
            # write the fixed yaml to the config file
            with open("experiments/" + self.project_name + "_config.yaml", "w") as f:
                f.write(data)
            with open("experiments/" + "DLAS_last_run.yaml", "w") as f:
                f.write(data)
        # mode = 'normal'
        export == False
        # leaving this for future cloud expor

        """
        if self.cloud_mode == False and export == None:
            #check if output path exists
            if os.path.exists(self.output_path) == True:
                #check if output path is empty
                if len(os.listdir(self.output_path)) > 0:
                    #show a messagebox asking if the user wants to overwrite the output path
                    overwrite = messagebox.askyesno("Overwrite Output Path", "The output path is not empty. Do you want to overwrite it?")
                    if overwrite == False:
                        return
                    else:
                        #delete the contents of the output path but the logs or 0 directory
                        for file in os.listdir(self.output_path):
                            if file != 'logs' and file != '0':
                                if os.path.isdir(self.output_path + '/' + file) == True:
                                    shutil.rmtree(self.output_path + '/' + file)
                                else:
                                    os.remove(self.output_path + '/' + file)

                        
        if self.cloud_mode == True or export == 'LinuxCMD':
            if export == 'LinuxCMD':
                mode = 'LinuxCMD'
            export='Linux'
            #create a sessionName for the cloud based on the output path name and the time
            #format time and date to %month%day%hour%minute
            now = datetime.now()
            dt_string = now.strftime("%m-%d-%H-%M")
            self.export_name = self.output_path.split('/')[-1].split('\\')[-1] + '_' + dt_string
            self.packageForCloud()
        """

        if export == False:
            # save the bat file
            # batBase = ''
            # with open("scripts/train.bat", "w", encoding="utf-8") as f:
            #    f.write(batBase)
            # close the window
            self.destroy()
            # run the bat file
            self.quit()
            # change the working directory to the codes directory
            os.chdir("codes")
            run(
                "python train.py -opt ../experiments/"
                + self.project_name
                + "_config.yaml"
            )
            # if exit code is 0, then the training was successful
            os.system("pause")
        """
            #restart the app
        elif export == 'win':
            with open("train.bat", "w", encoding="utf-8") as f:
                f.write(batBase)
            #show message
            messagebox.showinfo("Export", "Exported to train.bat")
        elif mode == 'LinuxCMD':
            #copy batBase to clipboard
            trainer_index = batBase.find('trainer.py')+11
            batStart = batBase[:trainer_index]
            batCommands = batBase[trainer_index:]
            #split on -- and remove the first element
            batCommands = batCommands.split('--')
            batBase = batStart+' \\\n'
            for command in batCommands[1:]:
                #add the -- back
                if command != batCommands[-1]:
                    command = '  --'+command+'\\'+'\n'
                else:
                    command = '  --'+command
                batBase += command
            pyperclip.copy('!'+batBase)
            shutil.rmtree(self.full_export_path)
            messagebox.showinfo("Export", "Copied new training command to clipboard.")
            return
        elif export == 'Linux' and self.cloud_mode == True:
            notebook = 'resources/DLAS_notebook.ipynb'
            #load the notebook as a dictionary
            with open(notebook) as f:
                nb = json.load(f)
            #get the last cell
            #find the cell with the source that contains changeMe
            #format batBase so it won't be one line
            #find index in batBase of the trainer.py
            trainer_index = batBase.find('trainer.py')+11
            batStart = batBase[:trainer_index]
            batCommands = batBase[trainer_index:]
            #split on -- and remove the first element
            batCommands = batCommands.split('--')
            batBase = batStart+' \\\n'
            for command in batCommands[1:]:
                #add the -- back
                if command != batCommands[-1]:
                    command = '  --'+command+'\\'+'\n'
                else:
                    command = '  --'+command
                batBase += command
            for i in range(len(nb['cells'])):
                if 'changeMe' in nb['cells'][i]['source']:
                    code_cell = nb['cells'][i]
                    index = i
                    code_cell['source'] = '!'+batBase
                    #replace the last cell with the new one
                    nb['cells'][index] = code_cell
                    break
            
            #save the notebook to the export folder
            shutil.copy('requirements.txt', self.full_export_path)
            #zip up everything in export without the folder itself
            shutil.make_archive('payload', 'zip', self.full_export_path)
            #move the zip file to the export folder
            shutil.move('payload.zip', self.full_export_path)
            #save the notebook to the export folder
            with open(self.full_export_path+os.sep+'DLAS_notebook.ipynb', 'w') as f:
                json.dump(nb, f)
            #delete everything in the export folder except the zip file and the notebook
            for file in os.listdir(self.full_export_path):
                if file.endswith('.zip') or file.endswith('.ipynb'):
                    continue
                else:
                    #if it's a folder, delete it
                    if os.path.isdir(self.full_export_path+os.sep+file):
                        shutil.rmtree(self.full_export_path+os.sep+file)
                    #if it's a file, delete it
                    else:
                        os.remove(self.full_export_path+os.sep+file)
            #show message
            messagebox.showinfo("Success", f"Your cloud\linux payload is ready to go!\nSaved to: {self.full_export_path}\n\nUpload the files and run the notebook to start training.")
        """


def restart(instance):
    instance.destroy()
    app = App()
    app.mainloop()


app = App()
app.mainloop()
