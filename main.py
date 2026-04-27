import customtkinter as ctk
from customtkinter import *
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import messagebox, filedialog, Menu
from datetime import datetime
from pathlib import Path
from thefuzz import fuzz
import xml.etree.ElementTree as ET
import json, os, threading, time, shutil, stat, ctypes, requests, winreg, vdf, sqlite3, subprocess, webbrowser, certifi

# ---------------- Variables and Basics ----------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_CERT_PATH = os.path.join(BASE_DIR, "data", "cacert.pem")
os.environ['REQUESTS_CA_BUNDLE'] = CUSTOM_CERT_PATH
os.environ['SSL_CERT_FILE'] = CUSTOM_CERT_PATH

COVERS_PATH = os.path.join(BASE_DIR, "assets", "covers")
ICONS_PATH = os.path.join(BASE_DIR, "assets", "icons")

TOP_BAR_LIGHT_ICON_PATH = os.path.join(ICONS_PATH, "icon_light.ico")
SEARCH_LIGHT_ICON_PATH = os.path.join(ICONS_PATH, "search_light.ico")
FILTER_LIGHT_ICON_PATH = os.path.join(ICONS_PATH, "sort_light.ico")
SETTINGS_LIGHT_IMAGE_PATH = os.path.join(ICONS_PATH, "settings_light.ico")
CLEAR_LIGHT_IMAGE_PATH = os.path.join(ICONS_PATH, "clean_light.ico")
CLEAR_CACHE_ICON_PATH = os.path.join(ICONS_PATH, "clean_light.ico")
GHOST_IMAGE_PATH = os.path.join(ICONS_PATH, "ghost.png")
ALL_GAMES_LIGHT_IMAGE_PATH = os.path.join(ICONS_PATH, "all_games_light.ico")
FAVOURITES_LIGHT_IMAGE_PATH = os.path.join(ICONS_PATH, "favourites_light.ico")
SETTINGS_ICON_PATH = os.path.join(ICONS_PATH, "settings_light.ico")
ADD_GAME_IMAGE_PATH = os.path.join(ICONS_PATH, "add_light.ico")
ADD_CATEGORY_LIGHT_PATH = os.path.join(ICONS_PATH, "category_light.ico")
EDIT_NAME_LIGHT_PATH = os.path.join(ICONS_PATH, "edit_name_light.ico")
ARROW_RIGHT_LIGHT_PATH = os.path.join(ICONS_PATH, "arrow_right_light.ico")
XBOX_LOGO_LIGHT_PATH = os.path.join(ICONS_PATH, "xbox_logo_light.ico")
GITHUB_ICON_PATH = os.path.join(ICONS_PATH, "github.ico")
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")
GAMES_DATA_PATH = os.path.join(BASE_DIR, "data", "games_data.json")

current_page = ""
current_list = []
search_list = []
games = {}
covers_cache = {}

bottom_bar_text = ""
games_frame_update = False
is_temp_frame = False
is_cache_cleaner_running = False
is_optimizing = False
is_settings_running = False
is_searching_for_names = False
time_mode = None
category_delete_btn = None
category_up_btn = None
category_down_btn = None
category_edit_btn = None
last_no_of_cards = 0

def fetch_new_token(client_id, client_secret):
    auth_url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    response = requests.post(auth_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return {
            "access_token": data["access_token"],
            "expires_in": data["expires_in"]
        }
    else:
        messagebox.showerror(title="Token Error", message=f"Error fetching token: {response.status_code} - {response.text}")
        return None

def igdb_access_token_check():
    expires_in = get_config("igdb_access_token_expires_in")[0]
    if int(expires_in) < int(time.time()):
        new_data = fetch_new_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)
        if new_data == None:
            messagebox.showerror(title="Connection Error", message="Check your internet connection")
            exit()
        with open(CONFIG_PATH, "r") as file:
            data = json.load(file)
            data["igdb_access_token"] = new_data["access_token"]
            expires_in = int(new_data["expires_in"])
            data["igdb_access_token_expires_in"] = f"{int(time.time()+(expires_in/2))}"
        with open(CONFIG_PATH, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

def change_dict_arrangement(lst, value, direction):
    dirn = str(direction).lower()
    try:
        idx = lst.index(value)
    except ValueError:
        raise ValueError(f"{value!r} not in list")

    if dirn == 'up':
        if idx > 0:
            lst[idx], lst[idx - 1] = lst[idx - 1], lst[idx]
            return lst
        return False
    elif dirn == 'down':
        if idx < len(lst) - 1:
            lst[idx], lst[idx + 1] = lst[idx + 1], lst[idx]
            return lst
        return False
    else:
        raise ValueError("direction must be 'up' or 'down'")

def get_config(*args):
    returns = []
    with open(CONFIG_PATH, "r") as file:
        data = json.load(file)
        for request in args:
            returns.append(data[request])
    return returns

def get_games_data(*args):
    returns = []
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
        for request in args:
            try:
                returns.append(data[request])
            except:
                pass
    return returns

def get_games_to_ram():
    global games
    games.clear()
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
    games = data['games']

def get_covers_to_ram():
    global covers_cache
    covers_cache.clear()
    data = get_games_data("games")[0]
    for game, value in data.items():
        imagePIL = Image.open(os.path.join(COVERS_PATH, value["cover"]))
        image_cropped = ImageOps.fit(imagePIL, (200, 270), centering=(0.5, 0.5))
        image = CTkImage(light_image=image_cropped, dark_image=image_cropped, size=(200, 270))
        covers_cache[game] = image
    image = CTkImage(light_image=Image.open(GHOST_IMAGE_PATH), dark_image=Image.open(GHOST_IMAGE_PATH), size=(120, 120))
    covers_cache["ghost_image"] = image
    image = CTkImage(light_image=Image.open(GITHUB_ICON_PATH), dark_image=Image.open(GITHUB_ICON_PATH), size=(20, 20))
    covers_cache["github"] = image

def remove_symbols(text):
    alphabet_and_numbers = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' '
    ]
    final_text = ""
    for i in text:
        if i in alphabet_and_numbers:
            final_text += i
    return final_text

def delete_from_games_data(text):
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
        data.pop(text)
        data["_arrangement"].remove(text)
    with open(GAMES_DATA_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def add_category_to_games_data(text):
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
        data[text] = []
        data['_arrangement'].append(text)
    with open(GAMES_DATA_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# ---------------- Time ----------------

def update_time():
    global time_mode
    while True:
        now = datetime.now()
        current_time = now.strftime("%I:%M %p") if time_mode == 0 else now.strftime("%H:%M")
        time_label.configure(text=current_time)
        time.sleep(0.5)

# ---------------- Cache Cleaner ----------------

def get_dir_size(path):
    total_size = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False):
                    total_size += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total_size += get_dir_size(entry.path) 
    except (PermissionError, FileNotFoundError):
        pass
    return total_size

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_size_data():
    temp_size = get_dir_size(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'))
    local_temp_size = get_dir_size(os.environ.get('TEMP'))
    prefetch_size = get_dir_size(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'))
    return (temp_size, local_temp_size, prefetch_size)

def wipe_folder_contents(cc_temp_size_label, cc_local_temp_size_label, cc_prefetch_size_label, total_size_label, clear):
    global is_optimizing
    folders = [
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
    ]
    for folder in folders:
        for folder in folders:
            if not folder or not os.path.exists(folder):
                continue
                
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:

                    os.chmod(file_path, stat.S_IWRITE)
                    
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                except Exception as e:
                    print(e)
    temp_size, local_temp_size, prefetch_size = get_size_data()
    temp_size = f"{temp_size*(10**-9):.3f}"
    local_temp_size = f"{local_temp_size*(10**-9):.3f}"
    prefetch_size = f"{prefetch_size*(10**-9):.3f}"
    cc_temp_size_label.configure(text=f"Size: {temp_size}GB")
    cc_local_temp_size_label.configure(text=f"Size: {local_temp_size}GB")
    cc_prefetch_size_label.configure(text=f"Size: {prefetch_size}GB")
    total_size_label.configure(text=f"Total Size: {(float(temp_size)+float(local_temp_size)+float(prefetch_size)):.3f}GB")
    is_optimizing = False
    clear.configure(text="Optimize", fg_color="#0FB900")
    clear.place(x=387, y=215)

def set_last_clean():
    with open(CONFIG_PATH, "r") as file:
        data = json.load(file)
        data["last_clean"] = int(time.time())
    with open(CONFIG_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        
def set_last_width_and_height(width, height):
    with open(CONFIG_PATH, "r") as file:
        data = json.load(file)
    data["last_width"] = width
    data["last_height"] = height
    with open(CONFIG_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def set_next_clean():
    with open(CONFIG_PATH, "r") as file:
        data = json.load(file)
        mode = data["auto_clean"]
        data["next_clean"] = int(time.time()) + (mode*60*60) if mode != "Never" else 0
    with open(CONFIG_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def optimize_func(cc_temp_size_label, cc_local_temp_size_label, cc_prefetch_size_label, total_size_label, clear):
    global is_optimizing
    if not is_optimizing:
        is_optimizing = True
        clear.configure(text="Optimizing", fg_color="#0DA100")
        clear.place(x=367, y=215)
        optimize = threading.Thread(target=wipe_folder_contents, args=(cc_temp_size_label, cc_local_temp_size_label, cc_prefetch_size_label, total_size_label, clear), daemon=True)
        optimize.start()
        set_last_clean()
        set_next_clean()

def set_next_scan():
    with open(CONFIG_PATH, "r") as file:
        mode = json.load(file)["scan_mode"]
        with open(CONFIG_PATH, "r") as file:
            data = json.load(file)
            data["scan_mode"] = mode
            if mode == "Never":
                data["next_scan"] = mode
            else:
                if mode == "daily":
                    mode = (int(time.time()) + 86400)
                elif mode == "weekly":
                    mode = (int(time.time()) + 604800)
                elif mode == "monthly":
                    mode = (int(time.time()) + 2592000)
                data["next_scan"] = mode
        with open(CONFIG_PATH, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

def auto_thread():
    while True:
        next_clean = get_config("next_clean")
        if next_clean != "Never":
            diff = next_clean[0] - int(time.time())
            if diff <= 0:
                auto_optimize()
                set_last_clean()
                set_next_clean()

        next_scan = get_config("next_scan")[0]
        if next_scan != "Never":
            diff = int(next_scan) - int(time.time())
            if diff <= 0:
                automatic_scan()
                set_next_scan()

        time.sleep(5*60)

def auto_bottom_bar_thread():
    global bottom_bar_text
    while True:
        if bottom_bar_text != "":
            for i in bottom_bar.winfo_children():
                i.destroy()
            scanning_text = CTkLabel(bottom_bar, 1, 1, text=f"• {bottom_bar_text}", font=("Ariel", 15))
            scanning_text.place(x=7, y=2)

        time.sleep(0.1)

def empty_bottom_bar():
    global bottom_bar_text
    bottom_bar_text = ""
    for i in bottom_bar.winfo_children():
        i.destroy()

def run_game(launcher, game_name):
    global bottom_bar_text
    bottom_bar_text = f"Starting {game_name}..."

    os.startfile(launcher)
    root.after(5000, empty_bottom_bar)

def run_clear_cache():
    global is_cache_cleaner_running
    if not is_cache_cleaner_running:
        def close_clear_cache():
            global is_cache_cleaner_running, is_optimizing
            is_optimizing = False
            is_cache_cleaner_running = False
            clear_cache_app.destroy()
        is_cache_cleaner_running = True
        temp_size, local_temp_size, prefetch_size = get_size_data()
        temp_size = f"{temp_size*(10**-9):.3f}"
        local_temp_size = f"{local_temp_size*(10**-9):.3f}"
        prefetch_size = f"{prefetch_size*(10**-9):.3f}"
        clear_cache_app = CTkToplevel(root)
        clear_cache_app.geometry("550x260")
        clear_cache_app.after(200, lambda: clear_cache_app.iconbitmap(CLEAR_CACHE_ICON_PATH))
        clear_cache_app.resizable(False, False)
        clear_cache_app.title("Cache Cleaner")
        clear_cache_app.minsize(width=500, height=260)
        ctk.set_appearance_mode("dark")
        clear_cache_app.attributes('-topmost', True)
        clear_cache_app.after(210, lambda: clear_cache_app.attributes('-topmost', False))
        clear_cache_app.focus_force()

        cc_temp_frame = CTkFrame(clear_cache_app, 530, 60)
        cc_temp_frame.place(x=10, y=10)
        cc_temp_inframe = CTkFrame(cc_temp_frame, 80, 50)
        cc_temp_inframe.place(x=5, y=5)
        cc_temp_major_label = CTkLabel(cc_temp_inframe, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text="Temp", font=("Ariel", 25))
        cc_temp_major_label.place(x=8, y=10)
        cc_temp_minor_label = CTkLabel(cc_temp_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Path: C:\Windows\Temp", font=("Ariel", 18))
        cc_temp_minor_label.place(x=90, y=7)
        cc_temp_size_label = CTkLabel(cc_temp_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Size: {temp_size}GB", font=("Ariel", 20))
        cc_temp_size_label.place(x=90, y=30)

        cc_local_temp_frame = CTkFrame(clear_cache_app, 530, 60)
        cc_local_temp_frame.place(x=10, y=80)
        cc_local_temp_inframe = CTkFrame(cc_local_temp_frame, 80, 50)
        cc_local_temp_inframe.place(x=5, y=5)
        cc_local_temp_major_label = CTkLabel(cc_local_temp_inframe, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text="Local\nTemp", font=("Ariel", 20), anchor="center")
        cc_local_temp_major_label.place(x=15, y=1)
        cc_local_temp_minor_label = CTkLabel(cc_local_temp_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Path: {os.environ.get('TEMP')}", font=("Ariel", 18))
        cc_local_temp_minor_label.place(x=90, y=7)
        cc_local_temp_size_label = CTkLabel(cc_local_temp_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Size: {local_temp_size}GB", font=("Ariel", 18))
        cc_local_temp_size_label.place(x=90, y=30)

        cc_prefetch_frame = CTkFrame(clear_cache_app, 530, 60)
        cc_prefetch_frame.place(x=10, y=150)
        cc_prefetch_inframe = CTkFrame(cc_prefetch_frame, 80, 50)
        cc_prefetch_inframe.place(x=5, y=5)
        cc_prefetch_major_label = CTkLabel(cc_prefetch_inframe, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text="Prefetch", font=("Ariel", 19))
        cc_prefetch_major_label.place(x=4, y=13)
        cc_prefetch_minor_label = CTkLabel(cc_prefetch_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Path: C:\Windows\Prefetch", font=("Ariel", 18))
        cc_prefetch_minor_label.place(x=90, y=7)
        cc_prefetch_size_label = CTkLabel(cc_prefetch_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Size: {prefetch_size}GB", font=("Ariel", 20))
        cc_prefetch_size_label.place(x=90, y=30)

        total_size_label = CTkLabel(clear_cache_app, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Total Size: {(float(temp_size)+float(local_temp_size)+float(prefetch_size)):.3f}GB", font=("Ariel", 25))
        total_size_label.place(x=13, y=222)

        clear_image_path = os.path.join(ICONS_PATH, "clean_light.ico")
        clear_image = CTkImage(Image.open(clear_image_path), size=(30, 30))
        clear = CTkButton(clear_cache_app, 10, 10, corner_radius=10, text="Optimize", fg_color="#0FB900", hover_color="#0DA100", text_color="#FFFFFF", image=clear_image, font=("Ariel", 25), compound="right")
        clear.bind("<Button-1>", command=lambda e: optimize_func(cc_temp_size_label, cc_local_temp_size_label, cc_prefetch_size_label, total_size_label, clear))
        clear.place(x=387, y=215)

        if not is_admin():
            global is_optimizing
            admin_required_frame = CTkFrame(clear_cache_app, 155, 40, 5, 0, fg_color="#000000")
            admin_required_frame.place(x=387, y=215)
            admin_required_label = CTkLabel(admin_required_frame, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#B30000", text=f"Administrator\nRequired", font=("Ariel", 17))
            admin_required_label.place(x=30, y=1)
            is_optimizing = True

        clear_cache_app.protocol("WM_DELETE_WINDOW", close_clear_cache)
        clear_cache_app.mainloop()

# ---------------- Settings ----------------

def set_time_mode_to_config(mode):
    with open(CONFIG_PATH, "r") as file:
        data = json.load(file)
        data["time_mode"] = mode
    with open(CONFIG_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def get_time_mode_from_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)["time_mode"]

def auto_optimize():
    folders = [
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
    ]
    for folder in folders:
        for folder in folders:
            if not folder or not os.path.exists(folder):
                continue
                
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:

                    os.chmod(file_path, stat.S_IWRITE)
                    
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                except Exception as e:
                    print(e)

def run_settings():
    global is_settings_running, time_mode
    if not is_settings_running:
        is_settings_running = True
        def close_settings():
            global is_settings_running
            is_settings_running = False
            settings_app.destroy()
        def time_mode_select_12H():
            global time_mode
            set_time_mode_to_config(0)
            time_mode_12H.configure(fg_color="#4B4B4B")
            time_mode_24H.configure(fg_color="transparent")
            time_mode = 0
        def time_mode_select_24H():
            global time_mode
            set_time_mode_to_config(1)
            time_mode_12H.configure(fg_color="transparent")
            time_mode_24H.configure(fg_color="#4B4B4B")
            time_mode = 1
        def change_auto_clean_mode(*args):
            mode = auto_clean_combobox.get()
            with open(CONFIG_PATH, "r") as file:
                data = json.load(file)
                if mode == "Never":
                    data["auto_clean"] = mode
                else:
                    data["auto_clean"] = int(mode[:2])
            with open(CONFIG_PATH, "w") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            set_next_clean()
        def get_current_auto_clean_mode():
            with open(CONFIG_PATH, "r") as file:
                mode = json.load(file)["auto_clean"]
                if mode == "Never":
                    return "Never"
                else:
                    return f"{mode}h"
        def change_auto_scan_mode(*args):
            mode = auto_scan_combobox.get()
            with open(CONFIG_PATH, "r") as file:
                data = json.load(file)
                data["scan_mode"] = mode
                data["next_scan"] = mode
            with open(CONFIG_PATH, "w") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            set_next_scan()
        def get_current_auto_scan_mode():
                with open(CONFIG_PATH, "r") as file:
                    mode = json.load(file)["scan_mode"]
                    return mode

        settings_app = CTkToplevel(root)
        settings_app.geometry("330x222")
        settings_app.after(200, lambda: settings_app.iconbitmap(SETTINGS_ICON_PATH))
        settings_app.resizable(False, False)
        settings_app.title("Settings")
        ctk.set_appearance_mode("dark")
        settings_app.attributes('-topmost', True)
        settings_app.after(210, lambda: settings_app.attributes('-topmost', False))
        settings_app.focus_force()

        time_mode_label = CTkLabel(settings_app, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Time mode", font=("Ariel", 20))
        time_mode_label.place(x=10, y=12)

        time_mode_frame = CTkFrame(settings_app, 110, 35, fg_color="#353535")
        time_mode_frame.place(x=210, y=5)

        time_mode_12H = CTkButton(time_mode_frame, 10, 10, 5, bg_color="transparent", fg_color="transparent", hover_color="#4B4B4B", text_color="#FFFFFF", text="12H", font=("Ariel", 20), command=time_mode_select_12H)
        time_mode_12H.place(x=4, y=3)

        time_mode_24H = CTkButton(time_mode_frame, 10, 10, 5, bg_color="transparent", fg_color="transparent", hover_color="#4B4B4B", text_color="#FFFFFF", text="24H", font=("Ariel", 20), command=time_mode_select_24H)
        time_mode_24H.place(x=60, y=3)

        with open(CONFIG_PATH, "r") as file:
            last_clean = json.load(file)["last_clean"]
            now = int(time.time())
            diff = now - last_clean
        if diff < 60:
            last_clean_text = "just now"
        elif diff < 3600: 
            last_clean_text = f"{diff // 60}m"
        elif diff < 86400: 
            last_clean_text = f"{diff // 3600}h"
        else:
            last_clean_text = f"{diff // 86400}d"

        auto_clean_label = CTkLabel(settings_app, 0, 0, 0, bg_color="transparent", fg_color="transparent", text_color="#FFFFFF", text=f"Auto-Clean ({last_clean_text})", font=("Ariel", 20))
        auto_clean_label.place(x=10, y=58)

        auto_clean_combobox = CTkComboBox(
            settings_app, 
            width=110, 
            height=30, 
            corner_radius=8,
            values=["Never", "12h", "24h", "36h", "48h"],
            command=change_auto_clean_mode,
            
            # الألوان الأساسية
            fg_color="#2B2B2B",
            border_color="#363636",
            button_color="#363636",
            button_hover_color="#4D4D4D",
            text_color="#FFFFFF",
            font=("Arial", 16),
            
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#C0BFBF",
            dropdown_text_color="#000000",
            dropdown_font=("Arial", 14),
            
            state="readonly"
        )
        auto_clean_combobox.place(x=210, y=56)
        auto_clean_combobox.set(get_current_auto_clean_mode())

        if get_time_mode_from_config() == 0:
            time_mode_12H.configure(fg_color="#4B4B4B")
            time_mode_24H.configure(fg_color="transparent")
        elif get_time_mode_from_config() == 1:
            time_mode_12H.configure(fg_color="transparent")
            time_mode_24H.configure(fg_color="#4B4B4B")

        horizontal_line1 = CTkFrame(settings_app, 320, 2, 0, 0, fg_color="#7E7E7E")
        horizontal_line1.place(x=5, y=46)

        horizontal_line2 = CTkFrame(settings_app, 320, 2, 0, 0, fg_color="#7E7E7E")
        horizontal_line2.place(x=5, y=94)

        auto_scan_label = CTkLabel(settings_app, 1, 1, 0, bg_color="transparent", text_color="#ffffff", text="Auto-Scan", font=("Ariel", 20))
        auto_scan_label.place(x=10, y=106)
        
        auto_scan_combobox = CTkComboBox(
            settings_app, 
            width=110, 
            height=30, 
            corner_radius=8,
            values=["Never", "daily", "weekly", "monthly"],
            command=change_auto_scan_mode,
            
            # الألوان الأساسية
            fg_color="#2B2B2B",
            border_color="#363636",
            button_color="#363636",
            button_hover_color="#4D4D4D",
            text_color="#FFFFFF",
            font=("Arial", 16),
            
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#C0BFBF",
            dropdown_text_color="#000000",
            dropdown_font=("Arial", 14),
            
            state="readonly"
        )
        auto_scan_combobox.place(x=210, y=106)
        auto_scan_combobox.set(get_current_auto_scan_mode())

        github_button = CTkButton(settings_app, 20, 20, corner_radius=2, text="", image=covers_cache["github"], fg_color="#242424", hover_color="#3D3D3D", command=lambda: webbrowser.open("https://github.com/AbdulRahmanElsa3ed"))
        github_button.place(x=25, y=185)

        github_name = CTkLabel(settings_app, 1, 1, text="AbdulRahmanElsa3ed",  font=("Ariel", 25))
        github_name.place(x=55, y=185)

        settings_app.protocol("WM_DELETE_WINDOW", close_settings)
        settings.mainloop()

# ---------------- Main Window ----------------

def update_current_games():
    global games, current_list
    games_name = get_games_data(current_page)[0]
    saved_games = get_games_data('games')[0]
    current_list = []
    for name in games_name:
        current_list.append(name)
        games[name] = saved_games[name]
    current_list.sort()

def add_to_games(launcher, name, cover, release_date, platforms, summary):
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
        data['games'][name] = {
                    'launcher': launcher,
                    'cover': cover,
                    "release_date": release_date,
                    "platforms": platforms,
                    "summary": summary
                }
        data["all_games"].append(name)
    with open(GAMES_DATA_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def download_cover(name, source):  
    games = get_games_data("games")[0]
    game = games.get(name, None)

    if source == "IGDB":
        response = requests.get(game['cover'].replace("t_thumb", "t_1080p"), stream=True)

    elif source == "SteamGridDB":
        response = requests.get(f"https://www.steamgriddb.com/api/v2/search/autocomplete/{name}", headers=STEAMGRIDDB_HEADERS)
        game_id = response.json()['data'][0]['id']
        response = requests.get(f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}", headers=STEAMGRIDDB_HEADERS)
        for item in response.json()["data"]:
            if item.get('width') == 600 and item.get('height') == 900:
                        if not item.get('nsfw') and not item.get('humor'):
                            cover_url = item.get('url')
                            response = requests.get(cover_url, stream=True)
                            break

    else: return

    if response.status_code == 200:
        save_dir = COVERS_PATH
        file_path = os.path.join(save_dir, f"{name}.png")
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        with open(GAMES_DATA_PATH, 'r') as file:
            data = json.load(file)
            data['games'][name]['cover'] = f"{name}.png"
        with open(GAMES_DATA_PATH, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    
def add_game_func(game_name_app, launcher, name):
    if game_name_app != None:
        game_name_app.destroy()
    name = remove_symbols(name.lower())

    is_already_exists = False
    for key in games.keys():
        similarity = fuzz.ratio(name, key)
        if similarity >= 85:
            is_already_exists = True

    blacklist = [
    "steamworks", "redistributables", "shared", "vcredist", 
    "directx", "setup", "update", "compiler"
    ]
    in_black_list = False
    for i in blacklist:
        if i in name.split(" "):
            in_black_list = True
    if not is_already_exists and not in_black_list:
        if is_available_in_IGDB(name):
            cover, release_date, platforms, summary = get_game_data_by_name_IGDB(name)
            add_to_games(launcher, name, cover, release_date, platforms, summary)
            download_cover(name, "IGDB")

        elif is_available_in_SteamGridDB(name):
            add_to_games(launcher, name, None, "Unknown", [], "Unknown")
            download_cover(name, "SteamGridDB")

        else:
            add_to_games(launcher, name, None, "Unknown", [], "Unknown")
    
        get_games_to_ram()
        get_covers_to_ram()
        update_current_games()

        apply_page("all_games", all_games)
        global games_frame_update, bottom_bar_text
        games_frame_update = True
        bottom_bar_text = f"Library Update: {name} has been added."

def is_available_in_IGDB(name):
    query = f'fields name; where name ~ "{name}"; limit 1;'
    response = requests.post(IGDB_URL, headers=IGDB_HEADERS, data=query)
    if response.status_code == 200 and len(response.json()) > 0:
        return True
    else:
        return False
    
def is_available_in_SteamGridDB(name):
    response = requests.get(f"https://www.steamgriddb.com/api/v2/search/autocomplete/{name}", headers=STEAMGRIDDB_HEADERS)
    if response.status_code == 200 and len(response.json()) > 0:
        return True
    else:
        return False
    
def get_game_data_by_name_IGDB(name):
    query = f'fields name, summary, first_release_date, platforms.name, cover.url; where name ~ "{name}"; limit 1;'
    response = requests.post(IGDB_URL, headers=IGDB_HEADERS, data=query)
    try:
        if response.status_code == 200:
            data = response.json()

            cover = data[0].get('cover', None)
            if cover != None:
                cover_IGDB_URL = f"https:{cover.get('url', 'Unknown')}"

            rd_raw = data[0].get('first_release_date', 'Unknown')
            release_date = datetime.fromtimestamp(rd_raw).strftime('%Y-%m-%d') if rd_raw else "Unknown"

            platforms = []
            for i in data[0].get("platforms", None):
                platforms.append(i.get('name', None))
            
            summary = data[0].get('summary', 'Unknown')

            return (cover_IGDB_URL, release_date, platforms, summary)
        else:
            messagebox.showerror(title="Connection Error", message="Failed to connect with IGDB.")
            return    
    except: pass
    
def check_click(event):
    global category_delete_btn
    target = event.widget
    def is_descendant(parent, child):
        if parent == child:
            return True
        while child:
            child = child.master 
            if child == parent:
                return True
        return False
    
    is_icon_clicked = is_descendant(top_bar_icon, target)
    is_add_game_clicked = is_descendant(add_game, target)

    if is_icon_clicked or is_add_game_clicked:
        list_frame.place(x=0, y=48)
        list_frame.lift()
    else:
        list_frame.place(x=-300, y=48)
        add_game_frame.place(x=-300, y=48)
    if category_delete_btn != None:
        category_delete_btn.destroy()
        category_up_btn.destroy()
        category_down_btn.destroy()
        category_edit_btn.destroy()

def remove_list():
    list_frame.place(x=-300, y=48)
    add_game_frame.place(x=-300, y=48)

# ---------------- Manual Add

def names_frame_thread(game_name, names_frame, game_name_app, launcher, search_for_names):
    query = f'''fields name;
            where name ~ *"{game_name}"*;
            sort total_rating_count desc;
            limit 30;'''

    response = requests.post(IGDB_URL, headers=IGDB_HEADERS, data=query)

    if response.status_code == 200:
        for widget in names_frame.winfo_children():
            widget.destroy()

        data = response.json()

        for idx, i in enumerate(data):
            name = i.get('name', 'Unknown')
            
            button = CTkButton(
                names_frame, 565, 40, 
                fg_color="#303030", 
                text=name, 
                font=("Ariel", 25),
                command=lambda e=launcher, n=name: 
                    threading.Thread(target=add_game_func, args=(game_name_app, e, n)).start()
            )
            
            pady_val = (5, 0) if idx == 0 else (2, 0)
            button.pack(pady=pady_val)

        button = CTkButton(
            names_frame, 605, 1, 
            fg_color="#1B1B1B",
            bg_color="#1B1B1B", 
            text="", 
            font=("Ariel", 25)
            )
        pady_val = (5, 0)
        button.pack(pady=pady_val)

        search_for_names.configure(fg_color="#1B1B1B")
        global is_searching_for_names
        is_searching_for_names = False
    else:
        messagebox.showerror(title="Connection Error", message="Failed to connect with IGDB.")
        return
    root.after(6000, empty_bottom_bar)
    
def manually_widget(launcher):
    def run_names_frame_thread(*args):
        global is_searching_for_names
        if not is_searching_for_names:
            is_searching_for_names = True
            search_for_names.configure(fg_color="#363636")
            threading.Thread(target=names_frame_thread, args=(name_entry.get(), names_frame, game_name_app, launcher, search_for_names), daemon=True).start()

    game_name_app = CTkToplevel(root)
    game_name_app.title("Get Game's Data")
    game_name_app.geometry("597x392")
    game_name_app.resizable(False, False)
    ctk.set_appearance_mode("dark")
    game_name_app.configure(fg_color="#232427")
    game_name_app.after(200, lambda: game_name_app.iconbitmap(EDIT_NAME_LIGHT_PATH))

    name_label = CTkLabel(game_name_app, 0, 0, 0, fg_color="transparent", text="Game's Name", font=("Ariel", 20))
    name_label.place(x=10, y=10)

    name_entry = CTkEntry(game_name_app, 407, 30, 4, 1, fg_color="transparent", font=("Roboto", 16))
    name_entry.place(x=140, y=8)
    name_entry.bind("<Return>", run_names_frame_thread)

    names_frame = CTkScrollableFrame(game_name_app, 575, 335, 2, 0, fg_color="#1B1B1B")
    names_frame._scrollbar.configure(width=0)
    names_frame.place(x=10, y=45)

    search_for_names_image = CTkImage(Image.open(ARROW_RIGHT_LIGHT_PATH), size=(25, 25))
    search_for_names = CTkButton(game_name_app, 10, 10, 4, 0, 0, fg_color="#1B1B1B", hover_color="#363636", image=search_for_names_image, text="")
    search_for_names.place(x=552, y=8)
    search_for_names.bind("<Button-1>", run_names_frame_thread)

    game_name_app.attributes('-topmost', True)
    game_name_app.after(210, lambda: game_name_app.attributes('-topmost', False))
    game_name_app.focus_force()
    game_name_app.mainloop()

def manually_func():
    remove_list()

    game_launcher = filedialog.askopenfilename(title="Select game .exe", filetypes=[("Executables", "*.exe")])

    if game_launcher == "":
        return

    manually_widget(game_launcher)

# ---------------- Automatic Scan

def get_registry_value(root, path, key_name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as hkey:
            value, _ = winreg.QueryValueEx(hkey, key_name)
            return value
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading registry: {e}")
        return None

def steam_scan():
    path = get_registry_value(winreg.HKEY_CURRENT_USER, r"Software\\Valve\\Steam", "SteamPath")
    if path == None:
        return
    path = Path(os.path.join(path, "steamapps"))
    for file in path.iterdir():
        if file.is_file() and str(file).endswith("vdf"):
            vdf_file = file
    
    with open(vdf_file, 'r') as file:
        data = vdf.load(file)
    steam_paths = []
    for lib in data['libraryfolders'].values():
        steam_paths.append(lib['path'])
    
    acf_files = []
    for steam_path in steam_paths:
        steam_path = Path(os.path.join(steam_path, "steamapps"))
        for file in steam_path.iterdir():
            if file.is_file() and str(file).endswith("acf"):
                acf_files.append(file._str)
    
    for acf_file in acf_files:
        with open(acf_file, "r") as file:
            data = vdf.load(file)
            name = data['AppState']['name']
            installdir = data['AppState']['installdir']
            launcher = f"steam://rungameid/{data['AppState']['appid']}"
            add_game_func(None, launcher, name)

def epicgames_scan():
    program_data = os.environ.get('ProgramData')
    manifest_path = Path(os.path.join(program_data, "Epic", "EpicGamesLauncher", "Data", "Manifests"))

    item_files = []
    for item in manifest_path.iterdir():
        if item.is_file() and str(item).endswith("item"):
            item_files.append(item)
    
    for item_file in item_files:
        with open(item_file, "r") as file:
            data = json.load(file)
            name = data['DisplayName']
            installdir = data['MandatoryAppFolderName']
            launcher = f"com.epicgames.launcher://apps/{data['CatalogNamespace']}:{data['CatalogItemId']}:{data['AppName']}?action=launch&silent=true"
            add_game_func(None, launcher, name)
            
def gog_scan():
    program_data = os.environ.get('ProgramData')
    db_path = os.path.join(program_data, "GOG.com", "Galaxy", "Storage", "index.db")
    temp_db = "gog_temp.db"

    if os.path.exists(db_path):
        try:
            shutil.copy2(db_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            query = """
            SELECT 
                Games.title, 
                Games.productId, 
                LocalGameParameters.installDirectory
            FROM Games
            JOIN LocalGameParameters ON Games.productId = LocalGameParameters.productId
            WHERE Games.isInstalled = 1
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                name = row[0]
                productid = row[1]
                installdir = row[2]
                
                launcher = f"goggalaxy://openGameView/{productid}"

                add_game_func(None, launcher, name)

            conn.close()
            os.remove(temp_db)
            
        except Exception as e:
            print(f"Error scanning GOG: {e}")
            if os.path.exists(temp_db): os.remove(temp_db)

def automatic_scan_thread():
    global bottom_bar_text
    bottom_bar_text = "Scanning..."
    
    steam_scan()
    epicgames_scan()
    gog_scan()

    root.after(2000, empty_bottom_bar)
    
def automatic_scan():
    threading.Thread(target=automatic_scan_thread, daemon=True).start()

# ---------------- Xbox & Microsoft Store Scan

def xbox_scan_widget_thread():
    remove_list()
    def get_xbox_launcher_data():
        ps_command = (
            'Get-AppxPackage | '
            'Where-Object {$_.IsFramework -eq $false -and $_.SignatureKind -eq "Store" -and $_.InstallLocation -ne $null} | '
            'Select-Object Name, PackageFamilyName, InstallLocation | '
            'ConvertTo-Json'
        )
        
        data = {}

        try:
            result = subprocess.run(["powershell", "-Command", ps_command], shell=False, capture_output=True, text=True, encoding='utf-8')
            if not result.stdout.strip(): return
            
            apps = json.loads(result.stdout)
            if isinstance(apps, dict): apps = [apps]

            games_list = []

            for app in apps:
                folder = app.get('InstallLocation')
                manifest_path = os.path.join(folder, "AppxManifest.xml")
                
                if os.path.exists(manifest_path):
                    try:
                        tree = ET.parse(manifest_path)
                        root = tree.getroot()
                        ns = {'ns': 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}
                        
                        app_tag = root.find('.//ns:Application', ns)
                        properties = root.find('.//ns:Properties', ns)
                        display_name = properties.find('ns:DisplayName', ns).text if properties is not None else app['Name']
                        
                        if app_tag is not None:
                            app_id = app_tag.get('Id')
                            
                            if "Microsoft" in display_name and "Game" not in display_name:
                                continue
                                
                            games_list.append({
                                "name": display_name,
                                "path": folder,
                                "launch_cmd": f"{app['PackageFamilyName']}!{app_id}"
                            })
                    except:
                        continue

            for g in games_list:
                data[str(g['name'])] = f"shell:AppsFolder\\{g['launch_cmd']}"
            show_results(data)
                
        except Exception as e:
            return
        
    def show_results(results):
            for name, launcher in results.items():
                button = CTkButton(
                    names_frame, 605, 40, 
                    fg_color="#303030", 
                    text=name, 
                    font=("Ariel", 25),
                    command= lambda n=name, l=launcher:
                    threading.Thread(target=add_game_func(xbox_scan_app, l, n))
                    )
                pady_val = (5, 0)
                button.pack(pady=pady_val)
            root.after(10000, empty_bottom_bar)

            button = CTkButton(
                names_frame, 605, 1, 
                fg_color="#1B1B1B",
                bg_color="#1B1B1B", 
                text="", 
                font=("Ariel", 25)
                )
            pady_val = (5, 0)
            button.pack(pady=pady_val)

    threading.Thread(target=get_xbox_launcher_data, daemon=True).start()
    xbox_scan_app = CTkToplevel(root)
    xbox_scan_app.title("Xbox Scan")
    xbox_scan_app.geometry("637x392")
    xbox_scan_app.resizable(False, False)
    ctk.set_appearance_mode("dark")
    xbox_scan_app.configure(fg_color="#232427")
    xbox_scan_app.after(200, lambda: xbox_scan_app.iconbitmap(XBOX_LOGO_LIGHT_PATH))

    names_frame = CTkScrollableFrame(xbox_scan_app, 615, 370, 2, 0, fg_color="#1B1B1B")
    names_frame._scrollbar.configure(width=0)
    names_frame.place(x=10, y=10)

    xbox_scan_app.attributes('-topmost', True)
    xbox_scan_app.after(210, lambda: xbox_scan_app.attributes('-topmost', False))
    xbox_scan_app.focus_force()
    xbox_scan_app.mainloop()

def xbox_scan_widget():
    threading.Thread(target=xbox_scan_widget_thread, daemon=True).start()

# ---------------- Search

def on_search(*args):
    global search_list
    search_list.clear()
    search_input = search.get()
    for i in current_list:
        if fuzz.partial_ratio(search_input, i) >= 70 or i.startswith(search_input):
            search_list.append(i)
    generate_games_cards(True)

# ---------------- category

def update_categories():
    for item in side_bar.winfo_children():
        if item.winfo_name() not in ["!ctkbutton", "!ctkbutton2"]:
            item.destroy()

    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)
        for i in data['_arrangement']:
            btn = CTkButton(side_bar, 200, 50, 0, 1, border_color="#353535", fg_color="#232427", bg_color="#232427", hover_color="#2B2B2B", text=i, font=("Ariel", 25))
            btn.bind("<Button-1>", lambda e, page_name=i, b=btn: apply_page(page_name, b))
            btn.bind("<Button-3>", lambda e, b=btn: right_click_category_btn(b))
            btn.pack(fill="x", pady=(0,0))

def add_category_func():
    global is_temp_frame
    if is_temp_frame:
        return()
    def add(*args):
        if get_games_data(temp_nameEntry.get()) == []:
            global is_temp_frame
            temp_frame.place(x=-200, y=-200)
            button = CTkButton(side_bar, 200, 50, 0, 1, border_color="#353535", fg_color="#232427", hover_color="#2B2B2B", text=temp_nameEntry.get(), font=("Ariel", 25))
            button.bind("<Button-1>", command=lambda e, page=temp_nameEntry.get(), b=button: apply_page(page, b))
            button.bind("<Button-3>", command=lambda e, b=button: right_click_category_btn(b))
            button.pack(fill="x", pady=(0,0))
            add_category_to_games_data(temp_nameEntry.get())
            is_temp_frame = False
            generate_games_cards()
        else:
            temp_nameEntry.delete(0, tk.END)
            messagebox.showerror(title="Category Error", message="This name is already exists, Please choose another name.")

    def delete(*args):
        temp_frame.place(x=-200, y=0)
        global is_temp_frame
        is_temp_frame = False

    temp_frame = CTkFrame(side_bar, 200, 50, 0, 1, border_color="#353535", fg_color="#232427")
    temp_nameEntry = CTkEntry(temp_frame, 190, 40, 0, None, font=("Ariel", 25), border_color="#353535", fg_color="#353536")
    temp_nameEntry.bind("<Return>", command=add)
    temp_nameEntry.bind("<Escape>", command=delete)
    temp_frame.pack(fill="x", pady=(0,0))
    temp_nameEntry.place(x=5, y=5)
    temp_nameEntry.focus_set()
    root.update_idletasks()
    side_bar._parent_canvas.yview_moveto(1.0)
    is_temp_frame = True

def right_click_category_btn(button, *args):
    global category_delete_btn, category_up_btn, category_down_btn, category_edit_btn
    if category_delete_btn != None:
        category_delete_btn.destroy()
        category_up_btn.destroy()
        category_down_btn.destroy()
        category_edit_btn.destroy()
    def delete():
        global category_delete_btn
        button.destroy()
        delete_from_games_data(button.cget("text"))
        category_delete_btn = None
        apply_page("all_games", all_games)
    def move_category(section_name, direction):
        with open(GAMES_DATA_PATH, "r") as file:
            data = json.load(file)
            lst = data["_arrangement"]
            result = change_dict_arrangement(lst, section_name, direction) 
            data["_arrangement"] = result if result != False else lst
        with open(GAMES_DATA_PATH, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        update_categories()
        generate_games_cards()

    def edit_category_name(name):
        global is_temp_frame
        with open(GAMES_DATA_PATH, "r") as file:
            data = json.load(file)
        def add(original_value):
            global is_temp_frame
            temp_frame.place(x=-200, y=-200)
            data.pop(name)
            data["_arrangement"].remove(name)
            data[temp_nameEntry.get()] = original_value
            data["_arrangement"].append(temp_nameEntry.get())
            with open(GAMES_DATA_PATH, "w") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            is_temp_frame = False
            update_categories()
        def back():
            global is_temp_frame
            temp_frame.place(x=-200, y=-200)
            is_temp_frame = False
            update_categories()

        original_value = data[name]
        button.destroy()

        temp_frame = CTkFrame(side_bar, 200, 50, 0, 1, border_color="#353535", fg_color="#232427")
        temp_nameEntry = CTkEntry(temp_frame, 190, 40, 0, None, font=("Ariel", 25), border_color="#353535", fg_color="#353536")
        temp_nameEntry.insert(0, name)
        temp_nameEntry.bind("<Return>", command=lambda e, ov=original_value: add(ov))
        temp_nameEntry.bind("<Escape>", command=lambda e: back())
        temp_frame.pack(fill="x", pady=(0,0))
        temp_nameEntry.place(x=5, y=5)
        temp_nameEntry.focus_set()
        root.update_idletasks()
        side_bar._parent_canvas.yview_moveto(1.0)
        is_temp_frame = True

    category_delete_btn = CTkButton(button, 5, 5, text="❌", font=("Ariel", 8), fg_color="#353535", bg_color="#353535", hover_color="#353535", command=delete)
    category_delete_btn.place(x=183, y=1)

    category_up_btn = CTkButton(button, 5, 5, text="⬆", font=("Ariel", 9), fg_color="#353535", bg_color="#353535", hover_color="#353535", command=lambda b=button._text, d="up": move_category(b, d))
    category_up_btn.place(x=1, y=0)

    category_down_btn = CTkButton(button, 5, 5, text="⬇", font=("Ariel", 9), fg_color="#353535", bg_color="#353535", hover_color="#353535", command=lambda b=button._text, d="down": move_category(b, d))
    category_down_btn.place(x=1, y=32)

    category_edit_btn = CTkButton(button, 5, 5, text="--", font=("Ariel", 14), fg_color="#353535", bg_color="#353535", hover_color="#353535", command=lambda b=button._text:edit_category_name(b))
    category_edit_btn.place(x=183, y=32)

# ---------------- Games display

def edit_category(category, game_name, operation):
    global bottom_bar_text
    with open(GAMES_DATA_PATH, "r") as file:
        data = json.load(file)      
        if operation == "add" and game_name not in data[category]:
            
            bottom_bar_text = f"Library Update: {game_name} has been added to {category}"
            root.after(2000, empty_bottom_bar) 
            data[category].append(game_name)
        elif operation == "remove":          
            if category == "all_games":
                if messagebox.askokcancel(title="Remove from Library", 
                                        message=f"Are you sure you want to permanently remove '{game_name}' from your collection? This action cannot be undone.", 
                                        icon="warning"):
                    bottom_bar_text = f"Library Update: {game_name} has been removed."
                    root.after(2000, empty_bottom_bar) 
                    for key in list(data.keys()):
                        if isinstance(data[key], dict) and game_name in data[key]:
                            data[key].pop(game_name)
                        elif isinstance(data[key], list) and game_name in data[key]:
                            data[key].remove(game_name)
                    
                    if 'games' in locals() or 'games' in globals():
                        if game_name in games: del games[game_name]

            else:
                bottom_bar_text = f"Library Update: {game_name} has been removed from {category}"
                root.after(2000, empty_bottom_bar) 
                if category in data and isinstance(data[category], list):
                    if game_name in data[category]:
                        data[category].remove(game_name)

    with open(GAMES_DATA_PATH, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    apply_page(current_page)

def auto_games_frame_update():
    global games_frame_update
    if games_frame_update == True:
        generate_games_cards()
        games_frame_update = False
    root.after(1000, auto_games_frame_update)

def generate_games_cards(searching = False):  
    for child in games_frame.winfo_children():
        child.destroy()

    if (not searching and current_list == []) or (searching and search_list == []):
        games_frame.columnconfigure(0, weight=1)
        games_frame.rowconfigure(0, weight=1)
        CTkButton(games_frame, 210, 280, border_width=0, corner_radius=0, fg_color="#232427", hover_color="#232427", text="", image=covers_cache["ghost_image"]).grid(column=1, row=1, sticky="nsew")
    else:
        for game in (current_list if (search.get() == "") else search_list):
            def show_games_menu(event, current_game_menu=None):
                current_game_menu.post(event.x_root, event.y_root) if current_game_menu else pass_func
            games_menu = Menu(root, tearoff=0, fg="#000000", bg="#FFFFFF", font=("Ariel", 14))
            category_menu = Menu(root, tearoff=0, fg="#000000", bg="#FFFFFF", font=("Ariel", 14))

            no_of_categories = 0
            with open(GAMES_DATA_PATH, "r") as file:
                data = json.load(file)
                for category in data["_arrangement"]:
                    if category not in ["games", "all_games", "favourites", "_arrangement"]:
                        no_of_categories += 1
                        category_menu.add_command(label=(category+" •" if game in data[category] else category), 
                                            command=lambda cat=category, g=game: edit_category(cat, g, "add"))
            
            games_menu.add_command(label="Play", 
                                command=lambda L=games[game]["launcher"], g=game: run_game(L,g))
            games_menu.add_command(label=("Add To Favourites"+" •" if game in data["favourites"] else "Add To Favourites"), 
                                command=lambda g=game: edit_category("favourites", g, "add"))
            if no_of_categories != 0:
                games_menu.add_cascade(label="Add To Category", menu=category_menu)
            games_menu.add_command(label="Delete", 
                                command=lambda cat=current_page, g=game: edit_category(cat, g, "remove"))
            btn = CTkButton(games_frame, 210, 280, border_width=0, corner_radius=0, 
                            fg_color="#232427", hover_color="#AFAFAF", text="", 
                            image=covers_cache[game], 
                            command=lambda L=games[game]["launcher"], g=game: run_game(L,g))
            btn.bind("<Button-3>", lambda e, menu=games_menu: show_games_menu(e, menu))
        global last_no_of_cards
        last_no_of_cards = 0
        frame_resize()

def frame_resize(*args):
    global last_no_of_cards
    width = games_frame.winfo_width()
    no_of_cards = int(width / 210)

    if no_of_cards != last_no_of_cards :
        last_no_of_cards = no_of_cards
        for i in range(20):
            games_frame.columnconfigure(i, weight=0)
        games_frame.columnconfigure(0, weight=1)
        games_frame.columnconfigure(no_of_cards + 1, weight=1)
        games_frame.rowconfigure(0, minsize=5)

        c = 1
        r = 1
        for card in games_frame.winfo_children():
            card.grid(column=c, row=r)
            
            c += 1
            if c > no_of_cards:
                c = 1
                r += 1


# ---------------- Main Funcs

def pass_func():
    pass

def show_add_game_frame():
    add_game_frame.place(x=300, y=48)

def apply_page(page_name, button = None):
    global current_page, current_list
    current_page = page_name
    current_list = get_games_data(page_name)[0]
    update_current_games()
    generate_games_cards()

    if button:
        all_games.configure(fg_color="#232427")
        favourites.configure(fg_color="#232427")
        for child in side_bar.winfo_children():
            child.configure(fg_color="#232427")

        button.configure(fg_color="#2B2B2B")

def close_window():
    width = root.winfo_width()
    height = root.winfo_height()
    set_last_width_and_height(width, height)

    root.destroy()

IGDB_CLIENT_SECRET = "gxtfdr6kfaajn6xrlnohhntb2b3kod"
IGDB_CLIENT_ID = "duhf9vhy4qyp8t2k9bebwbn9bw0up4"
IGDB_URL = "https://api.igdb.com/v4/games"
igdb_access_token_check()
IGDB_ACCESS_TOKEN = get_config("igdb_access_token")[0]
IGDB_HEADERS = {
    "Client-ID": IGDB_CLIENT_ID,
    "Authorization": f"Bearer {IGDB_ACCESS_TOKEN}"
}

STEAMGRIDDB_API_KEY = "ad2b0e7dcfcee950ce812da2074478a9"
STEAMGRIDDB_HEADERS = {"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"}

last_geometry = get_config("last_width", "last_height")
icon_path = os.path.join(ICONS_PATH, "icon.ico")

root = CTk()
root.title("Nexus")
root.iconbitmap(icon_path)
root.geometry(f"{last_geometry[0]}x{last_geometry[1]}")
root.minsize(width=840, height=633)
root.configure(fg_color="#232427")
ctk.set_appearance_mode("dark")
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=0)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(1, weight=1)

# ---------------- Top Bar

top_bar = CTkFrame(root, 0, 48, 0, 0, fg_color="#232427")
top_bar.grid(row=0, column=0, columnspan=4, sticky="ew")
top_bar.grid_rowconfigure(0, weight=1)
top_bar.grid_columnconfigure(0, weight=1)

horizontal_line = CTkFrame(top_bar, 0, 2, 0, 0, fg_color="#353535")
horizontal_line.grid(row=1, column=0, columnspan=3, sticky="ew")

top_bar_icon_image = CTkImage(Image.open(TOP_BAR_LIGHT_ICON_PATH), size=(30, 30))
top_bar_icon = CTkButton(top_bar, 0, 0, 0, 0, image=top_bar_icon_image, text="", fg_color="#232427", hover_color="#232427", command=lambda: pass_func)
top_bar_icon.place(x=4, y=5)

search_frame = CTkEntry(top_bar, 400, 30, 8, 1, bg_color="#232427", fg_color="#232427", text_color="#FFFFFF", border_color="#FFFFFF")
search_frame.place(x=45, y=9)

entry_var = ctk.StringVar()
entry_var.trace_add("write", on_search)
search = CTkEntry(top_bar, 374, 24, 8, 0, bg_color="#232427", fg_color="#232427", text_color="#FFFFFF", font=("Roboto", 16), textvariable=entry_var)
search.place(x=69, y=12)

search_icon_image = CTkImage(Image.open(SEARCH_LIGHT_ICON_PATH), size=(16, 16))
search_icon = CTkButton(top_bar, 0, 0, 0, 0, image=search_icon_image, text="", fg_color="#232427", hover_color="#232427", hover=False)
search_icon.place(x=51, y=12)

time_label = CTkLabel(top_bar, 0, 0, 0, fg_color="#232427", text="00:00 ##", font=("Ariel", 22))
time_label.grid(row=0, column=0, sticky="e", padx=10, pady=10)
threading.Thread(target=update_time, daemon=True).start()

if get_time_mode_from_config() == 0:
    time_mode = 0
elif get_time_mode_from_config() == 1:
    time_mode = 1

# ---------------- Side Bar

side_bar = CTkScrollableFrame(root, 200, 0, 0, 0, fg_color="#353535")
side_bar._scrollbar.configure(width=0)
side_bar.grid(row=1, column=0, sticky="wns")

all_games_image = CTkImage(Image.open(ALL_GAMES_LIGHT_IMAGE_PATH), size=(22, 22))
all_games = CTkButton(side_bar, 200, 50, 0, 1, image=all_games_image, border_color="#353535", fg_color="#232427", hover_color="#2B2B2B", text="All Games", font=("Ariel", 25))
all_games.bind("<Button-1>", command=lambda e, b=all_games: apply_page("all_games", b))
all_games.pack(fill="x", pady=(0, 0))

favourites_image = CTkImage(Image.open(FAVOURITES_LIGHT_IMAGE_PATH), size=(22, 22))
favourites = CTkButton(side_bar, 200, 50, 0, 1, image=favourites_image, border_color="#353535", fg_color="#232427", hover_color="#2B2B2B", text="Favourites", font=("Ariel", 25))
favourites.bind("<Button-1>", command=lambda e, b=favourites: apply_page("favourites", b))
favourites.pack(fill="x", pady=(0, 0))

update_categories()

side_bar_bottom_frame = CTkFrame(root, 200, 102, 0, 0, fg_color="#232427")
side_bar_bottom_frame.grid(column=0, row=2, sticky="ws")

clear_image = CTkImage(Image.open(CLEAR_LIGHT_IMAGE_PATH), size=(32, 32))
clear = CTkButton(side_bar_bottom_frame, 200, 50, 0, 1, text="Clear Cache", border_color="#353535", fg_color="#232427", hover_color="#2B2B2B", image=clear_image, compound="left", font=("Ariel", 25), command=run_clear_cache, anchor="w", border_spacing=5)
clear.grid(column=0, row=0)

settings_image = CTkImage(Image.open(SETTINGS_LIGHT_IMAGE_PATH), size=(22, 22))
settings = CTkButton(side_bar_bottom_frame, 200, 52, 0, 1, text=" Settings", border_color="#353535", fg_color="#232427", hover_color="#2B2B2B", image=settings_image, compound="left", font=("Ariel", 25), anchor="w", border_spacing=10, command=run_settings)
settings.grid(column=0, row=1)

bottom_bar = CTkFrame(root, 1, 20, 0, 1, border_color="#1A1A1A", fg_color="#1A1A1A")
bottom_bar.grid(column=0, row=3, columnspan=4, sticky="we")

# ---------------- Games Frame

games_frame = CTkScrollableFrame(root, 0, 0, 0, 0, fg_color="transparent")
games_frame.grid(column=2, row=1, rowspan=2, sticky="wens")
games_frame._scrollbar.configure(width=0)

# ---------------- List Frame 2

add_game_frame = CTkFrame(root, 300, 100, 0, 2)

manually = CTkButton(add_game_frame, 300, 30, 0, 1, 4, fg_color="#1B1B1B", hover_color="#353535", text="Manually", compound="left", anchor="w", font=("Ariel", 22), command=manually_func)
manually.grid(column=0, row=0)

scan = CTkButton(add_game_frame, 300, 30, 0, 1, 4, fg_color="#1B1B1B", hover_color="#353535", text="Scan Automatically", compound="left", anchor="w", font=("Ariel", 22), command=automatic_scan)
scan.grid(column=0, row=1)

xbox_scan = CTkButton(add_game_frame, 300, 30, 0, 1, 4, fg_color="#1B1B1B", hover_color="#353535", text="Xbox & Microsoft Store Scan", compound="left", anchor="w", font=("Ariel", 22), command=xbox_scan_widget)
xbox_scan.grid(column=0, row=2)

# ---------------- List frame 1

list_frame = CTkFrame(root, 300, 60, 0, 2)

add_game_image = CTkImage(Image.open(ADD_GAME_IMAGE_PATH), size=(16, 16))
add_game = CTkButton(list_frame, 300, 30, 0, 1, 4, fg_color="#1B1B1B", hover_color="#353535", text="Add Game                        ▶", image=add_game_image, compound="left", anchor="w", font=("Ariel", 22), command=show_add_game_frame)
add_game.grid(column=0, row=0)

add_category_image = CTkImage(Image.open(ADD_CATEGORY_LIGHT_PATH), size=(16, 16))
add_category = CTkButton(list_frame, 300, 30, 0, 1, 4, fg_color="#1B1B1B", hover_color="#353535", text="Add Category", image=add_category_image, compound="left", anchor="w", font=("Ariel", 22), command=add_category_func)
add_category.grid(column=0, row=1)


# ---------------- Main App ----------------

get_games_to_ram()
get_covers_to_ram()
generate_games_cards()
auto_games_frame_update()
threading.Thread(target=auto_bottom_bar_thread, daemon=True).start()
apply_page("all_games", all_games)

root.bind_all("<Button-1>", check_click)
root.bind("<Configure>", frame_resize)
threading.Thread(target=auto_thread, daemon=True).start()
root.protocol("WM_DELETE_WINDOW", close_window)
root.mainloop()