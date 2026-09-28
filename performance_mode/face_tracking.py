import sys
import time
import math
import threading 
import numpy as np
from typing import Tuple, Union
from oscpy.client import OSCClient
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


fl = 407
screen_heigth = 25
user_ipd = 6.2
if len(sys.argv) >= 2:
  user_ipd = float(sys.argv[1])
address = "10.250.39.171"
port = 8000
clientOSC = OSCClient(address, port)
cap = cv2.VideoCapture(0)
first_time = time.time()*1000.0
frame_width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

class TrackingResults:
  tracking_results = None
  def get_result(self, result: vision.FaceDetectorResult, output_image: mp.Image, timestamp_ms: int):
      self.tracking_results = result
    
res = TrackingResults()

# Create a face detector instance with the live stream mode:
base_options = python.BaseOptions(model_asset_path='blaze_face_short_range.tflite')
options = vision.FaceDetectorOptions(
  base_options=base_options,
  running_mode=vision.RunningMode.LIVE_STREAM,
  result_callback=res.get_result)
detector = vision.FaceDetector.create_from_options(options)

MARGIN = 10  # pixels
ROW_SIZE = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 2
TEXT_COLOR = (255, 0, 0)  # red

def _normalized_to_pixel_coordinates(
    normalized_x: float, normalized_y: float, image_width: int,
    image_height: int) -> Union[None, Tuple[int, int]]:
  """Converts normalized value pair to pixel coordinates."""

  # Checks if the float value is between 0 and 1.
  def is_valid_normalized_value(value: float) -> bool:
    return (value > 0 or math.isclose(0, value)) and (value < 1 or
                                                      math.isclose(1, value))

  if not (is_valid_normalized_value(normalized_x) and
          is_valid_normalized_value(normalized_y)):
    # TODO: Draw coordinates even if it's outside of the image bounds.
    return None
  x_px = min(math.floor(normalized_x * image_width), image_width - 1)
  y_px = min(math.floor(normalized_y * image_height), image_height - 1)
  return x_px, y_px

def visualize(
    image,
    detection_result
) -> np.ndarray:
  
  annotated_image = image.copy()
  height, width, _ = image.shape


  for detection in detection_result.detections:
    # Draw bounding_box
    bbox = detection.bounding_box
    start_point = bbox.origin_x, bbox.origin_y
    end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height

    i=0
    for keypoint in detection.keypoints:
      i+=1
      if i<=2:
        keypoint_px = _normalized_to_pixel_coordinates(keypoint.x, keypoint.y,
                                                       width, height)
        color, thickness, radius = (0, 255, 0), 2, 2
        cv2.circle(annotated_image, keypoint_px, thickness, color, radius)
      if i==3 : 
        keypoint_px = _normalized_to_pixel_coordinates(keypoint.x, keypoint.y,
                                                       width, height)
        color, thickness, radius = (255, 0, 0), 2, 2
        cv2.circle(annotated_image, keypoint_px, thickness, color, radius)

    # Draw label and score
    category = detection.categories[0]
    category_name = category.category_name
    category_name = '' if category_name is None else category_name
    probability = round(category.score, 2)
    result_text = category_name + ' (' + str(probability) + ')'
    text_location = (MARGIN + bbox.origin_x,
                     MARGIN + ROW_SIZE + bbox.origin_y)

  return annotated_image


def compute3DPos(ibe_x,ibe_y, rec_ipd):
  
  z = int((fl*user_ipd)/rec_ipd)
  x = (ibe_x - (frame_width/2) )*z/fl
  y = (ibe_y - (frame_height/2)) *z/fl
  centered_x = int(x)
  centered_y = - int(y)
  centered_z = int(z)
  return (centered_x, centered_y, centered_z)


def select_closest_to_center(detections, frame_w, frame_h):
  """Renvoie la détection dont le centre de la bounding box est le plus
  proche du centre de l'image (au lieu de choisir arbitrairement)."""
  if not detections:
    return None

  center_x = frame_w / 2
  center_y = frame_h / 2

  closest_detection = None
  closest_dist_sq = None

  for detection in detections:
    bbox = detection.bounding_box
    det_center_x = bbox.origin_x + bbox.width / 2
    det_center_y = bbox.origin_y + bbox.height / 2
    dist_sq = (det_center_x - center_x) ** 2 + (det_center_y - center_y) ** 2

    if closest_dist_sq is None or dist_sq < closest_dist_sq:
      closest_dist_sq = dist_sq
      closest_detection = detection

  return closest_detection



################################ main fonction ##############################
  
def runtracking():

  print("\nTracking started !!!")
  print("Hit ESC key to quit...")
  
  while True:

    time.sleep(0.05)
    ret, img_bgr = cap.read()
    frame_timestamp_ms = int(time.time()*1000 - first_time)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb) 
    detector.detect_async(mp_image, frame_timestamp_ms)

    if res.tracking_results != None:

      saved_detection = select_closest_to_center(
          res.tracking_results.detections, frame_width, frame_height)

      if saved_detection is not None:
        left_eye = saved_detection.keypoints[0]
        right_eye = saved_detection.keypoints[1]

        left_eye_px=[int(left_eye.x*frame_width),int(left_eye.y*frame_height)]
        right_eye_px=[int(right_eye.x*frame_width),int(right_eye.y*frame_height)]

        if left_eye is not None and right_eye is not None : 
          center_eyes = saved_detection.keypoints[2]
          center_eyes_px =[int(center_eyes.x*frame_width),int(center_eyes.y*frame_height)]

          # compute the interpupillary distance (in pixels)
          eyes_distance = int(((left_eye_px[0] - right_eye_px[0])**2 + (left_eye_px[1] - right_eye_px[1])**2)**(1/2))
      
          x,y,z = compute3DPos(center_eyes_px[0],center_eyes_px[1],eyes_distance)
          print("x = ",x," , y = ",y," , z= ",z)
          ################### Part 5: send the head position with OSC ######################
          clientOSC.send_message(b'/tracker/head/pos_xyz', [x, y, z])
  
      # Display an image in a window (you can avoid to display the image to improve the performance)
      annotated_image = mp_image.numpy_view()
      annotated_image = visualize(annotated_image, res.tracking_results)
      bgr_annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
      cv2.imshow('img', bgr_annotated_image)
  
    # Wait for Esc key to stop 
    k = cv2.waitKey(30) & 0xff
    if k == 27: 
        break
  
  # release the video stream from the camera
  cap.release()
    
  # close the associated window 
  cv2.destroyAllWindows() 


############################ program execution #############################
      
runtracking()