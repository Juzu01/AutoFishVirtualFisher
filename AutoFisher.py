import pyautogui
import time
import pytesseract
from PIL import Image, ImageTk
import keyboard
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import re
import os
import sys
import itertools

# Ustawienie ścieżki do tesseract, jeśli nie jest w PATH
pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Zmien na swoja sciezke

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AutoFishBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Fish Bot")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        # Załaduj obraz tła
        bg_image_path = resource_path("fisher.jpg")
        self.bg_image = Image.open(bg_image_path)
        self.bg_image = self.bg_image.resize((700, 500), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        
        self.canvas = tk.Canvas(root, width=700, height=500)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        
        # Dodanie stylu dla przycisków i etykiet
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", foreground="white", background="#7289da", font=('Arial', 10), padding=10)
        style.configure("TLabel", foreground="white", background='#2c2f33', font=('Arial', 10))
        style.configure("TEntry", foreground="black", background="white")

        # Dodanie widżetów na canvasie
        self.label = ttk.Label(root, text="AUTO FISHER BOT", font=('Arial', 16, 'bold'))
        self.canvas.create_window(350, 40, window=self.label)  # Ustawienie etykiety na canvasie

        self.custom_label = ttk.Label(root, text="by juzui", font=('Arial', 8))
        self.canvas.create_window(60, 10, window=self.custom_label)  # Małe litery w lewym górnym rogu

        self.lamp_label = ttk.Label(root, text="Status:")
        self.canvas.create_window(350, 80, window=self.lamp_label)

        self.status_lamp = tk.Canvas(root, width=20, height=20, bg='#2c2f33', highlightthickness=0)
        self.canvas.create_window(350, 110, window=self.status_lamp)
        self.status_lamp.create_oval(2, 2, 18, 18, fill="red")  # Startowo czerwona lampka

        self.status_label = ttk.Label(root, text="Status: Oczekiwanie na uruchomienie")  # Dodanie status_label
        self.canvas.create_window(350, 140, window=self.status_label)

        self.captcha_count_label = ttk.Label(root, text="Ilość rozwiązanych CAPTCHA: 0")
        self.canvas.create_window(350, 170, window=self.captcha_count_label)

        # Ikony trybów po lewej stronie
        self.sand_timer_button = tk.Button(root, text="⏳", font=('Arial', 16), command=self.toggle_delay_option)
        self.canvas.create_window(30, 120, window=self.sand_timer_button)

        self.star_button = tk.Button(root, text="⭐", font=('Arial', 16), command=self.toggle_command_option)
        self.canvas.create_window(30, 180, window=self.star_button)

        self.info_button = tk.Button(root, text="❓", font=('Arial', 16), command=self.toggle_info_option)
        self.canvas.create_window(30, 240, window=self.info_button)

        # Opcje, które będą ukrywane i pokazywane
        self.command_entry_label = ttk.Label(root, text="Wpisz komendę:")
        self.command_entry = ttk.Entry(root, width=40)

        self.delay_label = ttk.Label(root, text="Opóźnienie między znakami (sekundy):")
        self.delay_entry = ttk.Entry(root, width=5)
        self.delay_entry.insert(0, "0.06")

        self.info_label = ttk.Label(root, text="Sterowanie programem:\n- Kliknij '-' aby zatrzymać program.\n- Kliknij '*' aby kontynuować.")

        self.set_region_button = ttk.Button(root, text="Ustaw Obszar", command=self.set_region)
        self.canvas.create_window(350, 210, window=self.set_region_button)

        self.set_input_position_button = ttk.Button(root, text="Ustaw Miejsce do Pisania", command=self.set_input_position)
        self.canvas.create_window(350, 250, window=self.set_input_position_button)

        self.start_button = ttk.Button(root, text="Start", command=self.start_bot)
        self.canvas.create_window(270, 430, window=self.start_button)

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop_bot)
        self.canvas.create_window(430, 430, window=self.stop_button)

        self.reset_button = ttk.Button(root, text="Resetuj Ustawienia", command=self.reset_settings)
        self.canvas.create_window(350, 470, window=self.reset_button)

        self.region = None
        self.input_position = None
        self.running = False
        self.captcha_solved = False  # Flaga do monitorowania stanu captchy
        self.monitor_thread = None

        # Nasłuchiwanie na klawisz "-" oraz "*"
        keyboard.add_hotkey('-', self.stop_bot)
        keyboard.add_hotkey('*', self.start_bot)

    def toggle_command_option(self):
        if not hasattr(self, 'command_visible') or not self.command_visible:
            self.command_entry_label_id = self.canvas.create_window(350, 310, window=self.command_entry_label)
            self.command_entry_id = self.canvas.create_window(350, 340, window=self.command_entry)
            self.command_visible = True
        else:
            self.canvas.delete(self.command_entry_label_id)
            self.canvas.delete(self.command_entry_id)
            self.command_visible = False

    def toggle_delay_option(self):
        if not hasattr(self, 'delay_visible') or not self.delay_visible:
            self.delay_label_id = self.canvas.create_window(350, 280, window=self.delay_label)
            self.delay_entry_id = self.canvas.create_window(350, 310, window=self.delay_entry)
            self.delay_visible = True
        else:
            self.canvas.delete(self.delay_label_id)
            self.canvas.delete(self.delay_entry_id)
            self.delay_visible = False

    def toggle_info_option(self):
        if not hasattr(self, 'info_visible') or not self.info_visible:
            self.info_label_id = self.canvas.create_window(350, 350, window=self.info_label)
            self.info_visible = True
        else:
            self.canvas.delete(self.info_label_id)
            self.info_visible = False

    def set_region(self):
        messagebox.showinfo("Ustaw Obszar", "Kliknij lewy dolny róg obszaru do monitorowania.")
        time.sleep(3)  # Czas na przejście do miejsca kliknięcia
        bottom_left = pyautogui.position()
        messagebox.showinfo("Ustaw Obszar", "Kliknij prawy górny róg obszaru do monitorowania.")
        time.sleep(3)  # Czas na przejście do miejsca kliknięcia
        top_right = pyautogui.position()
        self.region = (bottom_left.x, top_right.y, top_right.x - bottom_left.x, bottom_left.y - top_right.y)
        self.status_label.config(text=f"Region ustawiony: {self.region}")

    def set_input_position(self):
        messagebox.showinfo("Ustaw Miejsce do Pisania", "Kliknij miejsce, gdzie mają być wpisywane komendy.")
        time.sleep(3)  # Czas na przejście do miejsca kliknięcia
        self.input_position = pyautogui.position()
        self.status_label.config(text=f"Miejsce do pisania ustawione: {self.input_position}")

    def capture_screen(self):
        if self.region:
            return pyautogui.screenshot(region=self.region)
        return None

    def extract_text(self, image):
        return pytesseract.image_to_string(image)

    def clean_code(self, code):
        cleaned_code = re.sub(r'[^a-zA-Z0-9]', '', code)
        return cleaned_code

    def generate_all_combinations(self, code):
        # Lista możliwych zamienników
        replacements = {'0': ['0', 'O', 'o'], 'O': ['O', '0', 'o'], 'o': ['o', '0', 'O']}
        
        # Zamień każdy znak w kodzie na odpowiednią listę zamienników
        combos = []
        for char in code:
            if char in replacements:
                combos.append(replacements[char])
            else:
                combos.append([char])
        
        # Wygeneruj wszystkie kombinacje
        all_combinations = [''.join(combo) for combo in itertools.product(*combos)]
        return all_combinations

    def type_with_delay(self, text, delay=0.06, add_space=False):
        if self.input_position:
            pyautogui.click(self.input_position)  # Kliknięcie tylko na miejsce wpisywania
            time.sleep(0.15)  # Dodatkowe opóźnienie po kliknięciu
        for char in text:
            pyautogui.write(char)
            time.sleep(delay)
        pyautogui.press('enter')
        if add_space:
            pyautogui.press('space')  # Kliknięcie spacji tylko po /verify

    def start_bot(self):
        if not self.region:
            messagebox.showwarning("Brak regionu", "Proszę ustawić obszar do monitorowania przed rozpoczęciem.")
            return
        if not self.input_position:
            messagebox.showwarning("Brak miejsca do pisania", "Proszę ustawić miejsce do pisania przed rozpoczęciem.")
            return

        self.running = True
        self.captcha_solved = False  # Resetowanie flagi captchy
        self.status_label.config(text="Status: Bot uruchomiony")
        self.update_lamp("green")  # Zielona lampka przy starcie

        self.monitor_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.monitor_thread.start()

    def stop_bot(self):
        self.running = False
        self.status_label.config(text="Status: Bot zatrzymany")
        self.update_lamp("red")  # Czerwona lampka przy zatrzymaniu

    def update_lamp(self, color):
        self.status_lamp.create_oval(2, 2, 18, 18, fill=color)

    def reset_settings(self):
        self.region = None
        self.input_position = None
        self.captcha_solved = False
        self.captcha_count = 0
        self.command_entry.delete(0, tk.END)
        self.delay_entry.delete(0, tk.END)
        self.delay_entry.insert(0, "0.06")
        self.status_label.config(text="Status: Ustawienia zresetowane")
        self.captcha_count_label.config(text="Ilość rozwiązanych CAPTCHA: 0")
        self.update_lamp("red")  # Czerwona lampka po resetowaniu

    def bot_loop(self):
        custom_command = self.command_entry.get()
        delay = float(self.delay_entry.get())
        while self.running:
            print("Rozpoczęcie iteracji pętli bot_loop")
            screenshot = self.capture_screen()
            if screenshot:
                text = self.extract_text(screenshot)
                print(f"Wyodrębniony tekst: {text}")

                if "You currently do not have an active captcha." in text or "You may now continue." in text:
                    self.status_label.config(text="Captcha rozwiązana, kontynuowanie łowienia.")
                    self.captcha_solved = True
                    print("Captcha rozwiązana.")
                elif "Code:" in text:
                    code = text.split("Code: ")[1].split()[0]
                    cleaned_code = self.clean_code(code)
                    possible_codes = self.generate_all_combinations(cleaned_code)
                    print(f"Captcha znaleziona, próba rozwiązania z kodami: {possible_codes}")

                    # Próbuj wszystkie wygenerowane kody, ale max 5 prób
                    for attempt in possible_codes[:5]:
                        self.type_with_delay(f'/verify {attempt}', delay, add_space=True)
                        time.sleep(1)  # Krótkie opóźnienie między próbami
                        # Sprawdzenie, czy captcha została rozwiązana, jeśli tak, przerywamy pętlę
                        screenshot = self.capture_screen()
                        text = self.extract_text(screenshot)
                        if "You may now continue." in text:
                            self.status_label.config(text="Captcha rozwiązana, kontynuowanie łowienia.")
                            self.captcha_solved = True
                            print(f"Captcha rozwiązana z kodem: {attempt}")
                            break
                    else:
                        print("Nie udało się rozwiązać captchy po 5 próbach")
                else:
                    print("Brak captchy, wysyłanie komendy /fish")
                    self.type_with_delay('/fish', delay, add_space=False)
                    time.sleep(1.4)  # Przerwa między kolejnymi wpisami, normalny tryb pracy

            if self.captcha_solved:
                # Kontynuacja pisania /fish po rozwiązaniu captchy
                print("Captcha rozwiązana, powrót do wpisywania /fish")
                self.type_with_delay('/fish', delay, add_space=False)
                self.captcha_solved = False  # Resetowanie flagi do normalnego trybu
                time.sleep(1.4)  # Przerwa między kolejnymi wpisami, normalny tryb pracy

            time.sleep(0.15)  # Przerwa między kolejnymi iteracjami

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoFishBot(root)
    root.mainloop()
