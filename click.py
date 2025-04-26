import tkinter as tk
from tkinter import filedialog, messagebox
import pyautogui
import time
import threading
import os
import json
from PIL import ImageGrab
import pygetwindow as gw

running = False
kep_path = "screenshot.png"
SETTINGS_FILE = "beallitasok.json"

FONT = ("Segoe UI", 10)

# --- BEÁLLÍTÁSOK KEZELÉSE ---
def beallitasok_mentese():
    data = {
        "ablaknev": ablaknev.get(),
        "ido": ido_entry.get(),
        "kep_path": kep_path,
        "kattintas_tipus": kattintas_tipus.get()
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def beallitasok_betoltese():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if data.get("ablaknev") in ablakcimek:
                    ablaknev.set(data["ablaknev"])
                ido_entry.delete(0, tk.END)
                ido_entry.insert(0, data.get("ido", "60"))
                global kep_path
                kep_path = data.get("kep_path", kep_path)
                if os.path.isfile(kep_path):
                    status_label.config(text=f"Kép betöltve: {os.path.basename(kep_path)}")
                kattintas_tipus.set(data.get("kattintas_tipus", "Egyszeres kattintás"))
            except Exception as e:
                print("Hiba a beállítások betöltésekor:", e)
                logolas(f"Hiba a beállítások betöltésekor:", e)

# --- KATTINTÁS FUNKCIÓ ---
def ablak_eloterbe_hozasa(ablak_cim):
    try:
        ablak = gw.getWindowsWithTitle(ablak_cim)[0]
        ablak.restore()
        ablak.activate()
        print(f"Ablak előtérbe hozva: {ablak_cim}")
        return True
    except IndexError:
        print("Nem található ilyen nevű ablak:", ablak_cim)
        logolas(f"Nem található ilyen nevű ablak: {ablak_cim}")
        return False

from datetime import datetime

LOG_FILE = "click_log.txt"

def logolas(uzenet):
    idopont = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{idopont}] {uzenet}\n")


def kattintas_loop(path, ido_perc):
    global running
    while running:
        for _ in range(int(ido_perc * 60)):
            if not running:
                return
            time.sleep(1)

        if not ablak_eloterbe_hozasa(ablaknev.get()):
            print(f"Ablak nem hozható előtérbe: {ablaknev.get()}")
            logolas(f"Ablak nem hozható előtérbe: {ablaknev.get()}")
            # Nem állunk meg, próbálkozunk tovább

        time.sleep(1.5)

        try:
            gomb = pyautogui.locateOnScreen(path, confidence=0.75)
            if gomb:
                x, y = pyautogui.center(gomb)
                pyautogui.moveTo(x, y)
                if kattintas_tipus.get() == "Dupla kattintás":
                    pyautogui.doubleClick()
                else:
                    pyautogui.click()
                print(f"Kattintottam: {x}, {y}")
                logolas(f"Kattintás történt: x={x}, y={y}")
            else:
                print("Gomb nem található a képernyőn.")
                logolas("Gomb nem található a képernyőn.")
        except Exception as e:
            print(f"Hiba a gombkeresés közben: {e}")
            logolas(f"Hiba a gombkeresés közben: {e}")

# --- GUI FUNKCIÓK ---
def inditas():
    global running
    if not os.path.isfile(kep_path):
        messagebox.showerror("Hiba", "Nem található képfájl.")
        return
    try:
        ido_perc = float(ido_entry.get())
        if ido_perc <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Hiba", "Adj meg egy pozitív számot!")
        return

    if not running:
        beallitasok_mentese()
        running = True
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        threading.Thread(target=kattintas_loop, args=(kep_path, ido_perc), daemon=True).start()

def leallitas():
    global running
    running = False
    start_button.config(state="normal")
    stop_button.config(state="disabled")

def kep_kivalasztas():
    file = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file:
        global kep_path
        kep_path = file
        status_label.config(text=f"Kép betöltve: {os.path.basename(kep_path)}")

def screenshot_terulet():
    root.withdraw()
    time.sleep(1)
    screenshot = ImageGrab.grab()
    overlay = tk.Tk()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.3)
    overlay.configure(bg='black')

    start_x = start_y = end_x = end_y = 0
    rect_id = None
    canvas = tk.Canvas(overlay, cursor="cross", bg='black')
    canvas.pack(fill="both", expand=True)

    def on_mouse_down(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)

    def on_mouse_move(event):
        if rect_id:
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        nonlocal end_x, end_y
        end_x, end_y = event.x, event.y
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)
        overlay.destroy()

        bbox = (x1, y1, x2, y2)
        cropped = screenshot.crop(bbox)
        cropped.save(kep_path)
        status_label.config(text=f"Kép mentve: {kep_path}")
        root.deiconify()

    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    overlay.mainloop()

def listaz_ablakokat():
    return sorted(set(w.title for w in gw.getAllWindows() if w.title.strip()))

def frissit_ablaklistat():
    global ablakcimek
    ablakcimek = listaz_ablakokat()
    menu = ablak_menu["menu"]
    menu.delete(0, "end")
    for cim in ablakcimek:
        menu.add_command(label=cim, command=lambda value=cim: ablaknev.set(value))
    if ablakcimek:
        ablaknev.set(ablakcimek[0])

def label(text):
    return tk.Label(root, text=text, font=FONT)

def entry():
    return tk.Entry(root, font=FONT, width=32)

def wide_button(text, cmd, state="normal"):
    return tk.Button(root, text=text, command=cmd, font=FONT, width=32, state=state)

# --- GUI ---
root = tk.Tk()

root.title("Automatikus gombkattintó")
root.geometry("420x500")
root.resizable(False, False)

ablaknev = tk.StringVar()
ablakcimek = listaz_ablakokat()
if ablakcimek:
    ablaknev.set(ablakcimek[0])

label("Válassz ablakot:").pack(pady=(10, 0))
ablak_menu = tk.OptionMenu(root, ablaknev, *ablakcimek)
ablak_menu.config(width=30, font=FONT)
ablak_menu.pack(pady=(0, 5))
wide_button("Ablaklista frissítése", frissit_ablaklistat).pack(pady=(0, 10))

label("Időköz percben:").pack()
ido_entry = entry()
ido_entry.insert(0, "60")
ido_entry.pack()

label("Kattintás típusa:").pack(pady=(5, 0))
kattintas_tipus = tk.StringVar(value="Egyszeres kattintás")
kattintas_menu = tk.OptionMenu(root, kattintas_tipus, "Egyszeres kattintás", "Dupla kattintás")
kattintas_menu.config(width=30, font=FONT)
kattintas_menu.pack(pady=(0, 10))

start_button = wide_button("Indítás", inditas)
start_button.pack(pady=(20, 5))

stop_button = wide_button("Leállítás", leallitas, "disabled")
stop_button.pack(pady=5)

wide_button("Gomb kijelölése képernyőn", screenshot_terulet).pack(pady=5)
wide_button("Kép betöltése fájlból", kep_kivalasztas).pack(pady=5)

status_label = tk.Label(root, text="Nincs kép kiválasztva", font=("Segoe UI", 9), fg="gray")
status_label.pack(pady=(10, 5))

wide_button("Kilépés", root.quit).pack(pady=(15, 10))

beallitasok_betoltese()

root.mainloop()
