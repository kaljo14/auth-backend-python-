import uuid
import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify
import easyocr
import pytesseract as pt

# Load the YOLOv5 model using OpenCV's dnn.readNetFromONNX() function.
net = cv2.dnn.readNetFromONNX('./yolov5/runs/train/Model2/weights/best.onnx')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    
# settings
INPUT_WIDTH =  640
INPUT_HEIGHT = 640

def get_detections(img, net):
    # 1.CONVERT IMAGE TO YOLO FORMAT
    image = img.copy()
    row, col, d = image.shape

    max_rc = max(row, col)
    input_image = np.zeros((max_rc, max_rc, 3), dtype=np.uint8)
    input_image[0:row, 0:col] = image

    # 2. GET PREDICTION FROM YOLO MODEL
    blob = cv2.dnn.blobFromImage(
        input_image, 1/255, (INPUT_WIDTH, INPUT_HEIGHT), swapRB=True, crop=False)
    net.setInput(blob)
    preds = net.forward()
    detections = preds[0]

    return input_image, detections


def non_maximum_supression(input_image, detections):

    # 3. FILTER DETECTIONS BASED ON CONFIDENCE AND PROBABILIY SCORE

    # center x, center y, w , h, conf, proba
    boxes = []
    confidences = []

    image_w, image_h = input_image.shape[:2]
    x_factor = image_w/INPUT_WIDTH
    y_factor = image_h/INPUT_HEIGHT

    for i in range(len(detections)):
        row = detections[i]
        confidence = row[4]  # confidence of detecting license plate
        if confidence > 0.2:
            class_score = row[5]  # probability score of license plate
            if class_score > 0.1:
                cx, cy, w, h = row[0:4]

                left = int((cx - 0.5*w)*x_factor)
                top = int((cy-0.5*h)*y_factor)
                width = int(w*x_factor)
                height = int(h*y_factor)
                box = np.array([left, top, width, height])

                confidences.append(confidence)
                boxes.append(box)

    # 4.1 CLEAN
    boxes_np = np.array(boxes).tolist()
    confidences_np = np.array(confidences).tolist()

    # 4.2 NMS
    index = cv2.dnn.NMSBoxes(boxes_np, confidences_np, 0.25, 0.45)

    return boxes_np, confidences_np, index


def drawings(image, boxes_np, confidences_np, index):
    # 5. Drawings
    for ind in index:
        x, y, w, h = boxes_np[ind]
        bb_conf = confidences_np[ind]
        conf_text = 'plate: {:.0f}%'.format(bb_conf*100)
        image_text = extract_text(image, boxes_np[ind])

        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 255), 2)
        cv2.rectangle(image, (x, y-30), (x+w, y), (255, 0, 255), -1)
        cv2.rectangle(image, (x, y+h), (x+w, y+h+25), (0, 0, 0), -1)

        cv2.putText(image, conf_text, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        cv2.putText(image, image_text, (x, y+h+27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
        
     
    return image_text


# def extract_text(image, bbox):
#     x, y, w, h = bbox
#     roi = image[y:y+h, x:x+w]
 
#     cv2.imwrite('/Users/kaloyanivanov/Documents/Learn/FinalVersion/auth-backend-python/meter_photos/img.jpg', roi)
#     if 0 in roi.shape:
#         return 'no number'
    
#     else:
#         reader = easyocr.Reader(['en'])
#         result = reader.readtext(roi)
        
#         if len(result) == 0:
#             return 'no number'
        
#         else:
#             text = result[0][1]
#             text = text.strip()
#             return text
def extract_text(image, bbox):
    x, y, w, h = bbox
    roi = image[y:y+h, x:x+w]
    # Apply gamma correction
    gamma = 1.5
    img_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    img_gamma = np.power(img_gray / float(np.max(img_gray)), gamma)
    img_gamma = np.uint8(img_gamma * 255)

    # Apply CLAHE to the image
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    cl_img = clahe.apply(img_gamma)
    unique_filename = f"{uuid.uuid4().hex}.jpg" 
    cv2.imwrite(f"/Users/kaloyanivanov/Documents/Learn/FinalVersion/auth-backend-python/meter_detection_photo/{unique_filename}", roi)


    # # Rescale the image
    #img_rescaled = cv2.resize(cl_img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

    # # Crop the region of interest
    #roi = img_rescaled[y:y+h, x:x+w]

    # Convert the ROI to binary using Otsu's thresholding
    blur = cv2.GaussianBlur(cl_img, (5, 5), 0)
    unique_filename = f"{uuid.uuid4().hex}.jpg" 
    #cv2.imwrite(f"/Users/kaloyanivanov/Documents/Learn/FinalVersion/auth-backend-python/meter_photos/{unique_filename}", blur)
    _, roi_thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # cv2.imwrite('/Users/kaloyanivanov/Documents/Learn/FinalVersion/auth-backend-python/meter_photos/roi_thresh.jpg', roi_thresh)

    ret, roi_threshs = cv2.threshold(roi,100, 255, cv2.THRESH_BINARY)
    # cv2.imwrite('/Users/kaloyanivanov/Documents/Learn/FinalVersion/auth-backend-python/meter_photos/roi_threshs.jpg', roi_threshs)
    # Check if ROI is empty
    if 0 in cl_img.shape:
        return 'no number'
    
    else:
      
        reader = easyocr.Reader(['en'])
        result = reader.readtext(roi_threshs)
        
        if len(result) == 0:
            return 'no number'
        
        else:
            text = result[0][1]
            # text = text.strip()
            return text

# predictions flow with return result
def yolo_predictions(img, net):
    # step-1: detections
    input_image, detections = get_detections(img, net)
    # step-2: NMS
    boxes_np, confidences_np, index = non_maximum_supression(
        input_image, detections)
    # step-3: Drawings
    result_img = drawings(img, boxes_np, confidences_np, index)
    return result_img

def OCR (filename,path):
  
   img = cv2.imread(path)
   
   results = yolo_predictions(img, net)
   print(results)
   return results
   