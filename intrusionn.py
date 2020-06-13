import numpy as np
import cv2
import json
import datetime
import time
from threading import Thread
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
	Mail, Attachment, FileContent, FileName,
	FileType, Disposition, ContentId)

def SendMail(ImgFileName):
	message = Mail(
		from_email='alert@intrusion.com',
		to_emails='praneshh89@gmail.com',
		subject='SURVEILLANCE ALERT: Unauthorized Access of MAIN GATE',
		html_content='<strong>REPORT FOR INTRUSION DETECTION: Person has crossed the area, Here we attached a reference image </strong>')
	
	data = cv2.imencode('.jpg', ImgFileName)[1].tostring()

	encoded = base64.b64encode(data).decode()
	attachment = Attachment()
	attachment.file_content = FileContent(encoded)
	attachment.file_type = FileType('application/jpg')
	attachment.file_name = FileName('alert.jpg')
	attachment.disposition = Disposition('attachment')
	attachment.content_id = ContentId('Example Content ID')
	message.attachment = attachment
	
	try:
	    sendgrid_client = SendGridAPIClient('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')
	    response = sendgrid_client.send(message)
	    print(response.status_code)
	    print(response.body)
	    print(response.headers)

	except Exception as e:
	    print(e)

with open('config.json') as file:
    config = json.load(file)

#cap1 = cv2.VideoCapture("rtsp://25.169.165.35:8080/h264_pcm.sdp")
#cap1 = cv2.VideoCapture(0)
cap1 = cv2.VideoCapture("IMG_3260.MOV")

net = cv2.dnn.readNetFromCaffe(config["object_model"], config["object_path"])
ret, frame = cap1.read()
(h, w) = frame.shape[:2]
text = "Unoccupied"
exit = False
email = True
time_format = "%d-%m-%Y %H:%M:%S"
polygon = Polygon(eval(config["points"]))
while True:
    try:
        if exit is False:

            ret, image = cap1.read()
            ori_image = image.copy()
            (h, w) = image.shape[:2]
            if cap1.get(1) % config["in_fps"] == 0:
                if text == "Unoccupied":
                    taken = False
                    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
                    net.setInput(blob)
                    detections = net.forward()
                    threshold = 0.6
                    for i in np.arange(0, detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        if confidence > threshold:
                            idx = int(detections[0, 0, i, 1])

                            if idx == 15:
                                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                                (startX, startY, endX, endY) = box.astype("int")
                                center = (endX,endY)
                                cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
                                print("person detected")
                                point = Point(center)
                                #print(point)
                                print(polygon.contains(point))
                               
                                if polygon.contains(point) == True and email is True:
                                    t = Thread(target=SendMail, args=(image,))
                                    t.start()
                                    print("email sent successfully")
                                    email = False
                                    t2 = time.time()
                                if email is False:
                                    email_time = ((time.time()-t2)/60)
                                    print("the email delay  :", email_time)
                                    if email_time > 0.5:
                                        email = True
                                   
            
            cv2.polylines(image,np.int32([eval(config["points"])]),True,(255,0,0),2)
            cv2.putText(image, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                        (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            cv2.namedWindow("intrusion", cv2.WINDOW_NORMAL)
            cv2.imshow("intrusion", image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Don't close the thread until it finished")
                exit = True
    except Exception as E:
        print(E)
        print("Don't close the thread until it finished")
        cap1.release()
        cap1 = cv2.VideoCapture(config["camera_url"])
        #exit = True

cap1.release()
cv2.destroyAllWindows()

print("Total application gets completed")

