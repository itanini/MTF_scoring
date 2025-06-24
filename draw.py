
#lets try rhis for real
# img = cv.imread('practice_photos/practice_high_quality_32.jpeg')
# cv.imshow('practice_32', img)
import cv2 as cv2
import numpy as np

# blank =np.zeros((500,500,3), dtype='uint8')
# # cv.imshow('blank', blank)
#
# #draw green stripes
# stripes = [i for i in range(500) if i%10 ==0]
# #green pixel in 1 of 10 rows
# blank[stripes] = 0,255,0
#
# #draw a rectangle
# blank =np.zeros((500,500,3), dtype='uint8')
# cv.rectangle(blank, (100,100), (350,250), thickness= -1, color= (0,255,0))
# # cv.imshow('blank', blank)
#
# #draw a circle
# blank =np.zeros((500,500,3), dtype='uint8')
# cv.circle(blank, (100,100), radius= 40,color= ( 0,0,255))
# # cv.imshow('circle', blank)
#
# #converting to gray scale
# aquascape = cv.imread('practice_photos/AQUASCAPE.jpg')
# cv.imshow('aquascape', aquascape)
# gray_aquascape = cv.cvtColor(aquascape, cv.COLOR_BGR2GRAY)
# # cv.imshow('practice_32', gray_aquascape)
#
# #Blur
# blured_aquascape = cv.GaussianBlur(aquascape, ksize= (9,9), sigmaX= cv.BORDER_DEFAULT)
# # cv.imshow('blured',blured_aquascape)
# cv.waitKey(0)
#
# erode_aquascape = cv.erode(aquascape, (11,11), iterations= 3)
# # cv.imshow('eroded',erode_aquascape)
#
# #resize
# resized = cv.resize(aquascape, (700,500))
# cv.imshow('resized',resized)
# cv.waitKey(0)
def rotate(img, angle, rot_point = None):
    (height,width)= img.shape[:2]
    if rot_point is None:
        rot_point = (width//2, height//2)
    rotMat = cv2.getRotationMatrix2D(rot_point,angle,1.0)
    dimensions = (width, height)
    return cv2.warpAffine(img,rotMat,dimensions)


practice_img = cv2.imread('practice_photos/practice_high_quality_32.jpeg')
practice_img_resized = cv2.resize(practice_img, (500,500))
practice_img_rotated = rotate(practice_img_resized, 15)
cv2.imshow('rotated', practice_img_rotated)
blured_image = cv2.blur(practice_img_rotated, ksize= (5,5))
canny_img = cv2.Canny(blured_image, 50, 50)
contours = cv2.findContours(canny_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
# print(contours)
cv2.imshow('canny', canny_img)


lines = cv2.HoughLines(canny_img, 1, np.pi / 180, threshold=10)

angles = []

if lines is not None:
    for line in lines:
        rho, theta = line[0]
        angle = np.rad2deg(theta)
        # We want only near-horizontal or near-vertical lines
        if 10 < angle < 80 or 100 < angle < 170:
            angles.append(angle)

# Calculate the average angle
if angles:
    avg_angle = np.mean(angles)

    # Convert to rotation relative to vertical (90 degrees)
    rotation_angle = avg_angle - 90

    # Rotate the image to align stripes vertically
    (h, w) = canny_img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
    rotated = cv2.warpAffine(canny_img, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=255)

    # Show result
    cv2.imshow("Rotated", rotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("No lines detected.")

contours, _ = cv2.findContours(rotated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filter contours based on aspect ratio and area
stripe_contours = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    aspect_ratio = h / float(w)
    area = cv2.contourArea(cnt)
    if  aspect_ratio > 5:  # Adjust thresholds as needed
        stripe_contours.append(cnt)

# Combine bounding boxes of all stripe contours
if stripe_contours:
    x_min = min([cv2.boundingRect(c)[0] for c in stripe_contours])
    y_min = min([cv2.boundingRect(c)[1] for c in stripe_contours])
    x_max = max([cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] for c in stripe_contours])
    y_max = max([cv2.boundingRect(c)[1] + cv2.boundingRect(c)[3] for c in stripe_contours])

    # Crop the original image using the bounding box
    cropped = rotated[y_min:y_max, x_min:x_max]

    # Show or save the result
    cv2.imshow('Cropped Stripes', cropped)
    cv2.waitKey(0)
# Use Hough Line Transform to detect lines