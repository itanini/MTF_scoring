import numpy as np
from scipy.signal import find_peaks
import scipy
import preprocess_img as pre
import cv2
import matplotlib.pyplot as plt


def contrast_score(mean_one_dimensional_photo):
    maxima_peaks, _  = find_peaks(mean_one_dimensional_photo)

    minima_peaks, _ =find_peaks(-mean_one_dimensional_photo)
    peaks_indices = np.sort(np.concatenate([minima_peaks,maxima_peaks]))
    peak_values = mean_one_dimensional_photo[peaks_indices]
    stripes_whites_indices = find_peaks(peak_values, threshold= 10)[0]
    stripes_blacks_indices = stripes_whites_indices - 1
    strip_white_values = peak_values[stripes_whites_indices]
    stripes_blacks_values = peak_values[stripes_blacks_indices]

    nominator =  sum(strip_white_values - stripes_blacks_values)
    denominator = sum(strip_white_values + stripes_blacks_values)

    contrast_score = nominator/denominator
    return contrast_score*100


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


    preprocessed_image = pre.preprocess_image(original_image, display= True)
    no_white_image = preprocessed_image.astype(float)
    y_axis_mean = np.nanmean(no_white_image, axis=0)
    smoothed_y_axis_mean = scipy.ndimage.median_filter(y_axis_mean, size=kernel_size)
    score = contrast_score(smoothed_y_axis_mean)
    print(f'Image Score : {score}')
    return lps, score
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