# This is a sample Python script.
from tkinter import messagebox

import cv2
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import matplotlib.pyplot as plt
import argparse
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import serial as ser
from serial.tools import list_ports
from score_photo import score_image, score_image_interactive  # adjust if needed
import os

class MiniscopeApp:
    def __init__(self, miniscope):
        self.home_window(miniscope)

        self.video_capture = None  # will be initialized later
        self.current_image = None
        self.LPS = None
        self.current_lp_index = 0
        self.current_lps = None
        self.scores = []


    def home_window(self, miniscope):
        self.home_window = miniscope  # avoid name conflict
        self.home_window.title("MTF app")
        # self.window.configure(bg="blue")

        # Use a frame to organize buttons and canvas
        main_frame = tk.Frame(self.home_window, padx=20, pady=20)

        image_path = "ponny_canary.webp"  # or .jpg, .gif, etc.
        img = Image.open(image_path)
        img = img.resize((200, 200))
        self.photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(main_frame, image=self.photo)
        img_label.grid(row=1, column=0, columnspan=2, pady=10)



        main_frame.pack()

        # Title Label
        title_label = tk.Label(main_frame, text="MTF Analysis", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))



        # ✅ Start button in main_frame
        self.start_button = tk.Button(
            main_frame,
            text="✅ Start",
            command=self.ask_for_lps,
            bg="green",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=15
        )
        self.start_button.grid(row=2, column=0, pady=10, padx=10, sticky='e')

        # ✅ Quit button in main_frame
        self.quit_button = tk.Button(
            main_frame,
            text="❌ Quit",
            command=self.home_window.destroy,
            bg="red",
            fg="white",
            font=("Helvetica", 12, "bold"),
            width=15
        )
        self.quit_button.grid(row=2, column=1, pady=10, padx=10, sticky='w')


    def next_lps(self):


        self.current_lps = self.LPS[self.current_lp_index]
        self.instruction_label.config(text=f"Please Take a Picture for {self.current_lps} LPS ({self.current_lp_index+1}/ {len(self.LPS)})",
                                      fg="white",  # text color - white looks better on red bg
                                      bg="red",  # red rectangle background
                                      font=("Helvetica", 20, "bold"),
                                      padx=10, pady=5,  # padding inside the label
                                      relief="solid",  # solid border line
                                      borderwidth=2  # thickness of border
                                      )

        self.instruction_label.place(relx=0.5, rely=0.5, anchor='center')

        # Function to move label down
        def move_label_up():
            self.instruction_label.config(font=("Helvetica", 12, "normal"))
            self.instruction_label.place(relx=0.5, rely=0.01, anchor='n')

        # After 2000 ms (2 seconds), move it down
        self.instruction_label.after(2000, move_label_up)


    def set_lps_and_start(self, lps_window):
        self.LPS = [lps for lps, var in self.lp_vars.items() if var.get()]
        if not self.LPS:
            tk.messagebox.showwarning("No Selection", "You must select at least one LPS.")
            return

        lps_window.destroy()  # Close the LPS selection popup
        self.home_window.destroy()  # Close the main/root window

        # Create new window for camera and capturing
        self.camera_window = tk.Tk()
        self.camera_window.title("Miniscope's Camera")
        self.camera_window.geometry("800x600")

        # Canvas for video preview
        self.canvas = tk.Canvas(self.camera_window, width=640, height=480)
        self.canvas.place(relx=0.5, rely=0.05, anchor='n')

        # Instruction Label (will move later)
        self.instruction_label = tk.Label(
            self.camera_window,
            text="",
            fg="white",
            bg="red",
            font=("Helvetica", 20, "bold"),
            padx=10,
            pady=5,
            relief="solid",
            borderwidth=2
        )
        self.instruction_label.place(relx=0.5, rely=0.5, anchor='center')  # initially centered

        # Load camera icon
        icon_img = Image.open("camera_icon.jpg").resize((24, 24))
        self.camera_icon = ImageTk.PhotoImage(icon_img)

        # Capture Button
        self.capture_button = tk.Button(
            self.camera_window,
            text=" Capture Image",
            image=self.camera_icon,
            compound="left",
            command=self.capture_and_confirm,
            bg="green",
            fg="white",
            font=("Helvetica", 14, "bold"),
            padx=10,
            pady=6,
            relief="raised",
            borderwidth=3,
            cursor="hand2"
        )
        self.capture_button.place(relx=0.5, rely=0.9, anchor='center')  # fixed below label

        # Initialize webcam and start feed
        self.video_capture = cv2.VideoCapture(1)
        self.current_lp_index = 0
        self.update_webcam()

        # LED Power Scale
        tk.Label(self.camera_window, text="LED Power").place(relx=0.1, rely=0.65)
        self.led_power_var = tk.DoubleVar()
        led_scale = tk.Scale(
            self.camera_window,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self.led_power_var,
            command=self.set_LED,  # Calls set_LED(level)
            length=200
        )
        led_scale.place(relx=0.1, rely=0.7)

        # Start LPS instructions
        self.next_lps()

        # === COM Port Selection ===
        tk.Label(self.camera_window, text="COM Port:").place(relx=0.5, rely=0.67)

        ports = list_ports.comports()
        self.com_options = [p.device for p in ports]
        self.selected_com = tk.StringVar()
        if self.com_options:
            self.selected_com.set(self.com_options[0])
        else:
            self.selected_com.set("No COM ports")

        com_menu = ttk.Combobox(self.camera_window, textvariable=self.selected_com, values=self.com_options,
                                state="readonly", width=15)
        com_menu.place(relx=0.5, rely=0.73)

        # Connect Button
        connect_button = tk.Button(
            self.camera_window,
            text="Connect LED",
            command=self.connect_serial_port,
            bg="blue",
            fg="white"
        )
        connect_button.place(relx=0.7, rely=0.72)

        self.camera_window.protocol("WM_DELETE_WINDOW", self.close_camera_window)
        self.camera_window.mainloop()

    def capture_and_confirm(self):
        if self.current_image is None:
            tk.messagebox.showerror("Error", "No image to capture.")
            return

        # Take a frozen copy of the current frame
        frozen_image = self.current_image.copy()
        lp = self.LPS[self.current_lp_index]

        # === Show frozen image in popup ===
        popup = tk.Toplevel(self.camera_window)
        popup.title(f"Captured Image - LPS {lp}")

        img = ImageTk.PhotoImage(frozen_image)
        label = tk.Label(popup, image=img)
        label.image = img  # Keep reference
        label.pack()

        def confirm():
            popup.destroy()
            self.save_and_score(lp, frozen_image)

        def retake():
            popup.destroy()
            tk.messagebox.showinfo("Retake", "Please retake the image.")

        button_frame = tk.Frame(popup)
        button_frame.pack(pady=10)

        yes_button = tk.Button(button_frame, text="Continue", command=confirm)
        yes_button.pack(side=tk.LEFT, padx=5)

        no_button = tk.Button(button_frame, text="Retake", command=retake)
        no_button.pack(side=tk.LEFT, padx=5)


    def save_and_score(self, lps, image):
        save_dir = "captured_images"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"{lps}_image.png")
        image.save(filepath)

        result = score_image_interactive(filepath)

        if result == "retake":
            return  # Just return so user can click "Capture Image" again

        elif result == "skip":
            self.LPS.pop(self.current_lp_index)
            if self.current_lp_index < len(self.LPS):
                self.start_capture_sequence()
            else:
                tk.messagebox.showinfo("Done", "All LPS processed.")
                scoring_plot(self.LPS, self.scores)
                self.close_camera_window()
            return

        messagebox.showinfo(
            title="Image Score",
            message=f"The image was successfully scored.\nScore: {result:.2f}"
        )
        self.scores.append(result)

        self.current_lp_index += 1
        if self.current_lp_index < len(self.LPS):
            self.next_lps()

        else:
            tk.messagebox.showinfo("Done", "All LPS processed.")
            scoring_plot(self.LPS, self.scores)
            self.close_camera_window()

    def ask_for_lps(self):
        lps_window = tk.Toplevel(self.home_window)
        lps_window.title("Select LPS values")

        tk.Label(lps_window, text="Choose LPS values to analyse:").grid(row=0, column=0, columnspan=9, pady=5)  # wide label

        options = [23, 26, 29, 32, 40, 45, 51, 57, 64, 72, 80, 90, 101, 114, 128, 143, 161, 180]
        self.lp_vars = {}

        # Number of columns (how many items per row)
        cols = (len(options) + 1) // 2  # split roughly half/half between 2 rows

        for idx, lp in enumerate(options):
            var = tk.BooleanVar()
            self.lp_vars[lp] = var
            row = 1 if idx < cols else 2  # first half row 1, second half row 2
            col = idx if idx < cols else idx - cols
            chk = tk.Checkbutton(lps_window, text=str(lp), variable=var)
            chk.grid(row=row, column=col, sticky='w', padx=5, pady=2)

        confirm_button = tk.Button(
            lps_window,
            text="Confirm",
            command=lambda: self.set_lps_and_start(lps_window)
        )
        confirm_button.grid(row=3, column=0, columnspan=cols, pady=10)

    def start_capture_sequence(self):
        self.next_lps()

        if self.current_image is not None:
            file_path = os.path.expanduser(f"./captured_images/{self.current_lps}_captured")
            self.current_image.save(file_path)
            os.startfile(file_path)

    def update_webcam(self):

        ret, frame = self.video_capture.read()

        if ret:
            self.current_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            self.photo = ImageTk.PhotoImage(image=self.current_image)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.camera_window.after(15, self.update_webcam)

    def close_camera_window(self):
        if self.video_capture is not None:
            if self.video_capture.isOpened():
                self.video_capture.release()
            self.video_capture = None

        if hasattr(self, 'camera_window') and self.camera_window.winfo_exists():
            self.camera_window.destroy()

    def connect_serial_port(self):
        port = self.selected_com.get()
        try:
            self.serial_port = ser.Serial(port, 9600)
            tk.messagebox.showinfo("Connected", f"Connected to {port}")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to connect to {port}\n{e}")

    def set_LED(self, level):
        if hasattr(self, 'serial_port') and self.serial_port:
            s = ('4n' + chr(int(float(level)))).encode('latin-1')
            self.serial_port.write(s)
            
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
# LPS = [23,26,29,32,40,45,51,54,64,72,80,90,101,114,128,143,161,180]
LPS = [23,26,29]



def scoring_plot(lps_list_sorted, score_list_sorted):
    plt.figure(figsize=(8, 5))
    plt.plot(lps_list_sorted, score_list_sorted, color='blue', marker='o')
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    plt.xticks(lps_list_sorted)
    plt.xlabel("Lines per mm (LPS)")
    plt.ylabel("Mean Contrast for Minima-Maxima Pair")
    plt.title("Image Score vs LPS")
    plt.grid(True)
    plt.show()




def interactive_main():
    SAVE_DIR = "captured_images"
    os.makedirs(SAVE_DIR, exist_ok=True)

    root = tk.Tk()
    app = MiniscopeApp(root)
    root.mainloop()



def choose_COM():
    print("------------------------")
    print("Available COM port:")
    print("------------------------")
    port = list(list_ports.comports())
    idx = 0
    for p in port:
        print(str(idx) + ': ' + str(p.device))
        idx += 1
    com_idx = input('Type COM channel number: ')
    return str(port[int(com_idx)].device)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # com_dev = choose_COM()
    # ser = serial.Serial(com_dev, baudrate=115200)

    interactive_main()

# if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Process images and plot scores vs LPS.')
    # parser.add_argument('image_dir', type=str, help='Path to the directory containing images.')
    # args = parser.parse_args()
    # main(args.image_dir)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
