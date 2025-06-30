import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import preprocess_img_manually
import scipy
import warnings

WHITE_THRESHOLD = 150 #Thresh to define white lines

def find_black_line_distances(img):
    # Threshold to isolate dark lines
    _, binary = cv2.threshold(img, WHITE_THRESHOLD, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    y_sets = []
    for cnt in contours:
        y_vals = set(pt[0,1] for pt in cnt)
        y_sets.append(y_vals)

    # Step 2: Find common y-values across all contours
    differences = []
    common_y = set.intersection(*y_sets)

    for y in sorted(common_y):
        x_coords = []
        for cnt in contours:
            # Find the x for this y (may be more than one — take first or average)
            xs_all = [pt[0,0] for pt in cnt if pt[0,1] == y]
            xs = [min(xs_all), max(xs_all)]
            if xs:
                x_coords.append(np.mean(xs))
        differences_in_fixed_y = np.diff(np.sort(x_coords))
        differences.append(np.mean(differences_in_fixed_y))

    mean_x_distances= np.mean(differences)

    return mean_x_distances

def preprocess_image(img, display = False):
    user_rotated_image, user_angle = preprocess_img_manually.preprocess_manually(img)
    min_distance_between_lines = find_black_line_distances(user_rotated_image)
    rotated_image = user_rotated_image
    distance_as_function_of_angle = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Treat warnings as errors

            for angle in np.arange(-10, 10, 0.2):
                cur_rotated = preprocess_img_manually.rotate(user_rotated_image, angle=angle)
                cur_distance_between_lines= find_black_line_distances(cur_rotated)
                # distance_as_function_of_angle[angle] = cur_distance_between_lines
                # if cur_distance_between_lines < min_distance_between_lines:
                #     min_distance_between_lines = cur_distance_between_lines
                #     rotated_image = cur_rotated
                distance_as_function_of_angle[angle] = cur_distance_between_lines
            # Convert keys and values to arrays
            angles = np.array(list(distance_as_function_of_angle.keys()))
            distances = np.array(list(distance_as_function_of_angle.values()))

            # Apply mean filter to values
            smooth_distances = scipy.ndimage.uniform_filter(distances, size=13)

            # Find the index of the minimal value in the smoothed array
            minimal_index = np.argmin(smooth_distances)

            # Get the corresponding angle from the distances
            optimal_rotation_angle = angles[minimal_index]
            rotated_image = preprocess_img_manually.rotate(user_rotated_image, angle= optimal_rotation_angle)
            made_optimization = True
            if display:
                display_results(dict(zip(angles, smooth_distances)), rotated_image, user_angle)
    except Exception as e:
        print(f"Warning or error encountered: {e}")
        rotated_image = user_rotated_image
        made_optimization = False

    # Extract keys and values
    return rotated_image, made_optimization


def display_results(distance_as_function_of_angle, rotated_image, user_angle):
    x = list(distance_as_function_of_angle.keys())
    plot_distance_as_func_of_angle(distance_as_function_of_angle, x, user_angle)
    no_white_image = rotated_image.astype(float)
    y_axis_mean = np.nanmean(no_white_image, axis=0)
    # y_axis_mean = scipy.ndimage.median_filter(y_axis_mean, size = 15)
    x_columns = np.arange(len(y_axis_mean))  # one x-value per column
    # Plot
    plt.plot(x_columns, y_axis_mean, color='blue')
    plt.xlabel('Column Index')
    plt.ylabel('Mean Pixel Value (excluding white)')
    plt.title('Mean Pixel Intensity per Column')
    plt.grid(True)
    plt.show()
    # Compute mean y-coordinate
    cv2.imshow('final_rotation', rotated_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return y_axis_mean


def plot_distance_as_func_of_angle(distance_as_function_of_angle, x, user_angle):
    y = list(distance_as_function_of_angle.values())

    # Find min point
    min_index = y.index(min(y))
    min_x = x[min_index]
    min_y = y[min_index]

    # Plot distance vs angle
    plt.plot(x, y, marker='o', label='Distance Curve')
    plt.xlabel('Angle rotated (degrees)')
    plt.ylabel('Mean Distance Between Lines (pixels)')
    plt.title(f'Mean Distance Between Lines as Function of Rotation Angle\n(Minimum at {min_x:.2f}°)')

    # Highlight minimum
    plt.scatter(min_x, min_y, color='red', zorder=5, label=f'Min: {min_x:.2f}°')
    plt.annotate(f'{min_x:.2f}°', xy=(min_x, min_y), xytext=(min_x, min_y + 1),
                 arrowprops=dict(facecolor='red', shrink=0.05), ha='center')

    # Mark user angle
    plt.axvline(user_angle, color='green', linestyle='--', label=f'User angle: {user_angle:.2f}°')

    plt.legend()
    plt.grid(True)
    plt.show()


# def GD_preprocess_image(img, display=True, max_steps=1000, learning_rate=1, grad_tolerance=1e-2, patience=2):
#     user_rotated_image, user_angle = preprocess_img_manually.preprocess_manually(img)
#
#     def loss(angle):
#         rotated = preprocess_img_manually.rotate(user_rotated_image, angle)
#         rotated_minus = preprocess_img_manually.rotate(user_rotated_image, angle - 0.1)
#         rotated_plus = preprocess_img_manually.rotate(user_rotated_image, angle + 0.1)
#         return (find_black_line_distances(rotated) + find_black_line_distances(rotated_minus) + find_black_line_distances(rotated_plus))/3
#
#     def numerical_gradient(f, a, delta=0.2):
#         return (f(a + delta) - f(a - delta)) / (2 * delta)
#
#     angle = 0.0
#     best_angle = angle
#     best_loss = loss(angle)
#
#     small_grad_steps = 0
#
#     for step in range(max_steps):
#         grad = numerical_gradient(loss, angle)
#
#         if abs(grad) < grad_tolerance:
#             small_grad_steps += 1
#         else:
#             small_grad_steps = 0  # Reset if gradient becomes significant again
#
#         if small_grad_steps >= patience:
#             print(f"Stopped early at step {step}: gradient small for {patience} steps.")
#             break
#
#         angle -= learning_rate * grad
#         current_loss = loss(angle)
#
#         if current_loss < best_loss:
#             best_loss = current_loss
#             best_angle = angle
#
#         print(f"Step {step}: angle={angle:.4f}, grad={grad:.6f}, loss={current_loss:.4f}")
#
#     print(f"Best angle found: {best_angle:.4f}° with loss {best_loss:.4f}")
#     rotated_image = preprocess_img_manually.rotate(user_rotated_image, best_angle)
#
#     if display:
#         angles_sampled = np.linspace(best_angle - 5, best_angle + 5, 50)
#         distance_as_function_of_angle = {a: loss(a) for a in angles_sampled}
#         display_results(distance_as_function_of_angle, rotated_image, user_angle)
#
#     return rotated_image

# preprocess_image()