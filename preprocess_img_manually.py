import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import matplotlib.image as mpimg
import matplotlib
matplotlib.use('TkAgg')
import cv2
import numpy as np

def crop_image(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Store coordinates
    coords = {}

    def onselect(eclick, erelease):
        """Callback to store rectangle coordinates"""
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        coords["x1"], coords["y1"] = min(x1, x2), min(y1, y2)
        coords["x2"], coords["y2"] = max(x1, x2), max(y1, y2)
        plt.close()  # Close window when selection is made

    # Create the figure and rectangle selector
    fig, ax = plt.subplots()
    ax.imshow(img_rgb)

    # No 'drawtype' argument needed anymore
    selector = RectangleSelector(ax, onselect,
                                interactive=True)

    plt.title("Select a rectangle and close the window")
    plt.show()

    # Crop and show
    cropped= img_rgb
    if coords:
        cropped = img_rgb[coords["y1"]:coords["y2"], coords["x1"]:coords["x2"]]
    return cropped


def rotate(img, angle, rot_point = None):
    (height,width)= img.shape[:2]
    if rot_point is None:
        rot_point = (width//2, height//2)
    rotMat = cv2.getRotationMatrix2D(rot_point,angle,1.0)
    dimensions = (width, height)
    return cv2.warpAffine(img,rotMat,dimensions, borderValue=(255, 255, 255))

def rotate_photo_to_user_selection(img):
    
    def onclick(event):
        if event.inaxes:
            if "p1" not in line_coords:
                line_coords["p1"] = (event.xdata, event.ydata)
                ax.plot(event.xdata, event.ydata, 'ro')
                fig.canvas.draw()
            elif "p2" not in line_coords:
                line_coords["p2"] = (event.xdata, event.ydata)
                ax.plot(event.xdata, event.ydata, 'ro')
                ax.plot([line_coords["p1"][0], event.xdata],
                        [line_coords["p1"][1], event.ydata], 'r-')
                fig.canvas.draw()
                plt.close()
                
    line_coords = {}

    fig, ax = plt.subplots()
    ax.imshow(img)
    plt.title("Click two points to define the desired vertical axis")
    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    rotated = img
    if "p1" in line_coords and "p2" in line_coords:
        (x1, y1), (x2, y2) = line_coords["p1"], line_coords["p2"]

        # Calculate angle of the line with respect to horizontal
        delta_x = x2 - x1
        delta_y = y2 - y1
        angle_rad = np.arctan(delta_x/delta_y)
        angle_deg = np.degrees(-angle_rad)

        print(f"Rotating image by {abs(angle_deg):.2f} degrees to align user line to vertical")

        rotated = rotate(img, angle_deg)

    return rotated, angle_deg  # fallback

def preprocess_manually(img):
    rotated_img, angle = rotate_photo_to_user_selection(img)
    cropped_img = crop_image(rotated_img)
    
    preprocessd_img = cv2.cvtColor(cropped_img, cv2.COLOR_RGB2GRAY)
    return preprocessd_img, angle