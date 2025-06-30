import numpy as np
from scipy.signal import find_peaks
import scipy
import preprocess_img as pre
import cv2
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
import os

def contrast_score(mean_one_dimensional_photo):
    try:
        maxima_peaks, _  = find_peaks(mean_one_dimensional_photo)
        minima_peaks, _ =find_peaks(-mean_one_dimensional_photo)

        peaks_indices = np.sort(np.concatenate([minima_peaks,maxima_peaks]))
        peak_values = mean_one_dimensional_photo[peaks_indices]
        stripes_whites_indices = find_peaks(peak_values, threshold = 10)[0]
        stripes_blacks_indices = stripes_whites_indices - 1
        strip_white_values = peak_values[stripes_whites_indices]
        stripes_blacks_values = peak_values[stripes_blacks_indices]

        nominator =  sum(strip_white_values - stripes_blacks_values)
        denominator = sum(strip_white_values + stripes_blacks_values)

        contrast_score = nominator/denominator
        return contrast_score * 100
    except Exception as e:
        print("Scoring failed:", e)

        root = tk.Tk()
        root.withdraw()
        user_choice = messagebox.askretrycancel(
            "Scoring Failed",
            "Scoring failed for this image.\nDo you want to retake the image? \n (Press 'Cancel' to skip LPS)"
        )
        root.destroy()

        # Return clear instructions to the GUI logic
        return "retake" if user_choice else "skip"



def score_image(image_path, kernel_size = 5, enter_lps_manually = False):
    original_image = cv2.imread(image_path)
    lps = None


    if enter_lps_manually:
        rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        plt.imshow(rgb_image)
        plt.title("Original Image - Enter LPS")
        plt.axis('off')
        plt.show()

        lps = input(f"Enter the LPS (lines per mm) for image '{image_path} or type 'skip': ").strip()
        try:
            lps_value = float(lps)
        except ValueError:
            print(f"Non-numeric input for LPS: '{lps}'. Skipping image.")
            return "skip", None


    preprocessed_image, made_optimization = pre.preprocess_image(original_image, display= False)
    no_white_image = preprocessed_image.astype(float)
    y_axis_mean = np.nanmean(no_white_image, axis=0)

    show_intensity(y_axis_mean)

    smoothed_y_axis_mean = scipy.ndimage.median_filter(y_axis_mean, size=kernel_size)
    score = contrast_score(smoothed_y_axis_mean)
    print(f'Image Score : {score}')
    return lps, score
    # contrast_as_function_of_kernel_size(preprocessed_image)


def show_intensity(y_axis_mean):
    plt.plot(range(len(y_axis_mean)), y_axis_mean, color='blue')
    plt.xlabel('Column Index')
    plt.ylabel('Mean Pixel Value (excluding white)')
    plt.title('Mean Pixel Intensity per Column')
    plt.grid(True)
    plt.show()


def score_image_interactive(image_path, kernel_size = 5, enter_lps_manually = False, show_intensity = False):
    original_image = cv2.imread(image_path)


    if enter_lps_manually:
        rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        plt.imshow(rgb_image)
        plt.title("Original Image - Enter LPS")
        plt.axis('off')
        plt.show()

    preprocessed_image, made_optimization  = pre.preprocess_image(original_image, display= False)
    if not made_optimization:
        root = tk.Tk()
        root.withdraw()  # hide main window
        messagebox.showinfo("Manual Angle",
                            f"Auto-optimization failed for:\n{os.path.basename(image_path)}\nManual user angle was selected.")
        root.destroy()

    no_white_image = preprocessed_image.astype(float)
    y_axis_mean = np.nanmean(no_white_image, axis=0)
    if show_intensity:
        show_intensity(y_axis_mean)

    smoothed_y_axis_mean = scipy.ndimage.median_filter(y_axis_mean, size=kernel_size)
    score = contrast_score(smoothed_y_axis_mean)

    print(f'Image Score : {score}')
    return score

    # contrast_as_function_of_kernel_size(preprocessed_image)

def contrast_as_function_of_kernel_size(preprocessed_image):
    contrast_scores = []
    kernel_size = []
    for ker in range(1, 32, 2):
        blured_img = cv2.blur(preprocessed_image, ksize=(ker, ker))
        no_white_image = blured_img.astype(float)
        y_axis_mean = np.nanmean(no_white_image, axis=0)
        smoothed_y_axis_mean = scipy.ndimage.median_filter(y_axis_mean, size=5)
        contrast_scores.append(contrast_score(smoothed_y_axis_mean))
        kernel_size.append(ker)
    plt.plot(kernel_size, contrast_scores, color='blue')
    plt.ylabel('Contrast Score (%)')
    plt.xlabel('Kernel Size')
    plt.title('Contrast Score as Function of Kernel Size')
    plt.show()


if __name__ == '__main__':
    score_image('practice_photos/143_practice.jpg')