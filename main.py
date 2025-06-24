# This is a sample Python script.
from tkinter import messagebox

import cv2
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import matplotlib.pyplot as plt
import argparse
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
# import serial
# from serial.tools import list_ports

from score_photo import score_image, score_image_interactive  # adjust if needed
import os

class MiniscopeApp:
    def __init__(self, miniscope):
        self.window = miniscope
        self.window.title("MiniScope Camera")
        
        self.video_capture = None  # will be initialized later
        self.current_image = None

        self.canvas = tk.Canvas(miniscope, width=640, height=480)
        self.canvas.pack()

        self.capture_bottom = tk.Button(
            miniscope,
            text="Start Scoring Miniscope",
            command=self.ask_for_lps
        )
        self.capture_bottom.pack()

        self.LPS = None
        self.current_lp_index = 0
        self.current_lps = None
        self.scores = []

    def next_lps(self):
        if self.current_lp_index >= len(self.LPS):
            tk.messagebox.showinfo("Done", "All LPS values have been processed.")
            return

        self.current_lps = self.LPS[self.current_lp_index] 
        self.instruction_label.config(text=f"Please capture LPS {self.current_lps} ({self.current_lp_index+1}/ {len(self.LPS)})")
        # self.capture_image()  # this stores image to self.current_image

        # # Show image in canvas or popup
        # self.show_confirmation_dialog()
        
    def set_lps_and_start(self, lps_window):
        self.LPS = [lps for lps, var in self.lp_vars.items() if var.get()]
        if not self.LPS:
            tk.messagebox.showwarning("No Selection", "You must select at least one LPS.")
            return

        lps_window.destroy()           # Close the LPS selection popup
        self.window.destroy()          # Close the main/root window

        # Create new window for camera and capturing
        self.camera_window = tk.Tk()
        self.camera_window.title("Camera Preview")

        self.canvas = tk.Canvas(self.camera_window, width=640, height=480)
        self.canvas.pack()
        self.instruction_label = tk.Label(self.camera_window, text="", font=("Helvetica", 14))
        self.instruction_label.pack(pady=10)

        self.video_capture = cv2.VideoCapture(0)
        self.current_lp_index = 0
        self.update_webcam()
        self.capture_button = tk.Button(
            self.camera_window,
            text="Capture Image",
            command=self.capture_and_confirm
        )

        self.capture_button.pack(pady=10)
        self.next_lps()

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
        popup.title(f"Captured Image - LP {lp}")

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

        yes_button = tk.Button(button_frame, text="Yes, I'm satisfied", command=confirm)
        yes_button.pack(side=tk.LEFT, padx=5)

        no_button = tk.Button(button_frame, text="No, retake", command=retake)
        no_button.pack(side=tk.LEFT, padx=5)


    def save_and_score(self, lps, image):
        save_dir = "captured_images"
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"{lps}_image.png")
        image.save(filepath)

        self.scores.append(score_image_interactive(filepath, lps))

        self.current_lp_index += 1
        if self.current_lp_index < len(self.LPS):
            self.next_lps()
        else:
            tk.messagebox.showinfo("Done", "All LPS processed.")
            scoring_plot(self.LPS, self.scores)
            self.close_camera_window()

    def ask_for_lps(self):
        lps_window = tk.Toplevel(self.window)
        lps_window.title("Select LPS values")

        tk.Label(lps_window, text="Choose LPS values:").pack()

        options = [23,26,29,32,40,45,51,54,64,72,80,90,101,114,128,143,161,180]
        self.lp_vars = {}

        for lp in options:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(lps_window, text=str(lp), variable=var)
            chk.pack(anchor='w')
            self.lp_vars[lp] = var

        confirm_button = tk.Button(
            lps_window,
            text="Confirm",
            command=lambda: self.set_lps_and_start(lps_window)
        )
        confirm_button.pack(pady=10)

    def start_capture_sequence(self):
        self.next_lps()

        if self.current_image is not None:
            file_path = os.path.expanduser("./captured_images/{label}_captured")
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
            
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
# LPS = [23,26,29,32,40,45,51,54,64,72,80,90,101,114,128,143,161,180]
LPS = [23,26,29]

# if os.name == 'nt':  # sys.platform == 'win32':
#     from serial.tools.list_ports_windows import comports
# elif os.name == 'posix':
#     from serial.tools.list_ports_posix import comports
# #~ elif os.name == 'java':
# else:
#     raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

def main(image_dir):

    # Loop through all files in the directory
    lps_list = []
    score_list = []

    for filename in os.listdir(image_dir):
        if filename.lower().endswith(IMAGE_EXTENSIONS):
            filepath = os.path.join(image_dir, filename)
            lps, image_score = score_image(filepath)

            if lps.strip().lower() == "skip":
                print(f"Skipped: {filename}")
                continue
            try:
                lps = float(lps)
                lps_list.append(lps)
                score_list.append(image_score)
            except ValueError:
                print(f"Invalid LPS input for {filename}: '{lps}' — must be a number or 'skip'.")

    sorted_pairs = sorted(zip(lps_list, score_list), key=lambda x: x[0])
    lps_list_sorted, score_list_sorted = zip(*sorted_pairs)

    scoring_plot(lps_list_sorted, score_list_sorted)


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

# def choose_LED_power():
#     window = tk.Tk()
#     v1 = tk.DoubleVar()
#     window.geometry("300x100")
#     window.title('Choose LED power')
#     #master.title('Choose LED level')
#     w = tk.Scale(window, from_=0, to=255,orient=tk.HORIZONTAL,width=10,variable = v1,command = set_LED) #int(v1.get())
#     w.pack()
#     window.mainloop()
#     s = ('4n'+chr(int(0))).encode('latin-1')
#     ser.write(s)
#     return int(v1.get())


# def set_LED(level):
#     s = ('4n' + chr(int(level))).encode('latin-1')
#     # s= struct.pack('!b',int(level))

#     ser.write(s)



def interactive_main():
    SAVE_DIR = "captured_images"
    os.makedirs(SAVE_DIR, exist_ok=True)

    def capture_image(label):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open webcam")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow(f"Take photo for: {label}", frame)
            key = cv2.waitKey(1)

            # Press SPACE to capture
            if key == 32:  # Space key
                image_path = os.path.join(SAVE_DIR, f"{label}.jpg")
                cv2.imwrite(image_path, frame)
                break

        cap.release()
        cv2.destroyAllWindows()
        return image_path

    def start_capture():
        lps_list = []
        score_list = []
        for lps in LPS:
            messagebox.showinfo("Next Sample", f"Please take a picture of: {lps}. (press space to take a picture)")
            image_path = capture_image(lps)
            _, image_score  = score_image(image_path)

            lps = float(lps)
            lps_list.append(lps)
            score_list.append(image_score)


        sorted_pairs = sorted(zip(lps_list, score_list), key=lambda x: x[0])
        lps_list_sorted, score_list_sorted = zip(*sorted_pairs)
        messagebox.showinfo("Done", "All images have been captured and scored.")

        scoring_plot(lps_list_sorted, score_list_sorted)

    # def choose_LED_power():
    #     window = tk.Tk()
    #     v1 = tk.DoubleVar()
    #     window.geometry("300x100")
    #     window.title('Choose LED power')
    #     # master.title('Choose LED level')
    #     w = tk.Scale(window, from_=0, to=255, orient=tk.HORIZONTAL, width=10, variable=v1,
    #                  command=set_LED)  # int(v1.get())
    #     w.pack()
    #     window.mainloop()
    #     s = ('4n' + chr(int(0))).encode('latin-1')
    #     ser.write(s)
    #     return int(v1.get())

    # def set_LED(level):
    #     s = ('4n' + chr(int(level))).encode('latin-1')
    #     # s= struct.pack('!b',int(level))

    #     ser.write(s)

    # Main GUI
    root = tk.Tk()
    app = MiniscopeApp(root)


    root.mainloop()

    #################################
    # root.title("Image Capture Tool")
    #
    # label = tk.Label(root, text="Click the button to start capturing images.")
    # label.pack(pady=10)
    #
    # start_button = tk.Button(root, text="Start", command=start_capture)
    # start_button.pack(pady=10)
    #
    # root.mainloop()


# def choose_COM():
#     print("------------------------")
#     print("Available COM port:")
#     print("------------------------")
#     port = list(list_ports.comports())
#     idx = 0
#     for p in port:
#         print(str(idx) + ': ' + str(p.device))
#         idx += 1
#     com_idx = input('Type COM channel number: ')
#     return str(port[int(com_idx)].device)



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
