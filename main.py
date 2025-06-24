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

from score_photo import score_image  # adjust if needed
import os

class MiniscopeApp:
    def __init__(self, miniscope):
        self.window = miniscope
        self.window.title("MiniScope Camera")
        self.video_capture = cv2.VideoCapture(0) # might need a change
        self.current_image = None
        self.canvas = tk.Canvas(miniscope, width= 640, height= 480)
        self.canvas.pack()
        self.update_webcam()

    def update_webcam(self):
        ret, frame = self.video_capture.read()

        if ret:
            self.current_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            self.photo= ImageTk.PhotoImage(image = self.current_image)
            self.canvas.create_image(0,0,image = self.photo, anchor = tk.NW)
            self.window.after(15,self.update_webcam)

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
