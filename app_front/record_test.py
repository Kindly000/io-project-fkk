import cv2
import numpy as np
from PIL import ImageGrab
from screeninfo import get_monitors

for m in get_monitors():
    x: int= m.x
    y: int=m.y
    width: int=m.width
    height: int=m.height

fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
captured_video = cv2.VideoWriter("recorded_video.avi",fourcc,30.0,(width,height))

record_status = False

def screen_record():
    global record_status
    while record_status:
        img = ImageGrab.grab(bbox=(x,y,width,height))
        np_img = np.array(img)
        cvt_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)
        # cv2.imshow('VideoCapture', cvt_img)

        captured_video.write(cvt_img)
        cv2.waitKey(0)
    cv2.destroyAllWindows()

def stop_screen_record():
    global record_status
    record_status = False

def start_record():
    global record_status
    record_status = True
    screen_record()

def stop_record():
    stop_screen_record()