import cv2
import dlib
import serial
import time
import numpy as np

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])

    ear = (A + B) / (2.0 * C)

    return ear

def shape_to_np(shape, dtype="int"):
    coords = np.zeros((shape.num_parts, 2), dtype=dtype)
    for i in range(0, shape.num_parts):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

def send_signal_to_arduino(ser, signal1, signal2):
    combined_signal = f"{signal1},{signal2}"
    ser.write(combined_signal.encode())
    print(f"Signal sent to Arduino: {combined_signal}")

def read_arduino_reply(ser):
    reply = ser.readline().decode().strip()
    return reply

def draw_eye_outline(frame, eye, color=(0, 255, 0), thickness=2):
    for i in range(len(eye) - 1):
        cv2.line(frame, tuple(eye[i]), tuple(eye[i+1]), color, thickness)
    cv2.line(frame, tuple(eye[-1]), tuple(eye[0]), color, thickness)

def main():
    ser = serial.Serial('COM5', 9600, timeout=1)  # Change 'COM5' to your Arduino port
    time.sleep(2)  # Allow time for the serial connection to be established

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("E:/shape_predictor_68_face_landmarks.dat")

    consecutive_drowsy_frames = 0
    drowsy_detection_active = True  # Flag to indicate if drowsy detection is active

    cap = cv2.VideoCapture(0)
    drowsycount = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray)

        if drowsy_detection_active:
            drowsy_detected = False  # Flag to indicate if drowsiness was detected in this frame

            for face in faces:
                shape = predictor(gray, face)
                shape = shape_to_np(shape)

                left_eye = shape[42:48]
                right_eye = shape[36:42]

                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)

                avg_ear = (left_ear + right_ear) / 2.0

                if avg_ear < 0.2:  # You may need to adjust this threshold based on your conditions
                    drowsy_detected = True
                    draw_eye_outline(frame, left_eye)
                    draw_eye_outline(frame, right_eye)

            if drowsy_detected:
                consecutive_drowsy_frames += 1
                if consecutive_drowsy_frames == 5:
                    drowsycount += 1
                    print("Drowsy state checked for 5 consecutive frames")

                    # Check if the elapsed time is less than 30 minutes
                    elapsed_time = time.time() - start_time
                    if elapsed_time < 1800:
                        if drowsycount < 2:
                            send_signal_to_arduino(ser, "Drowsy", str(drowsycount))
                            time.sleep(5)  # Wait for 5 seconds for the buzzer to ring
                            reply = read_arduino_reply(ser)
                            print(reply)  # Print the Arduino's reply
                        elif drowsycount==2:
                            send_signal_to_arduino(ser,"Drowsy",str(drowsycount))
                            time.sleep(5)
                            while(True):

                                reply = read_arduino_reply(ser)
                                # Check if the pause signal is received from Arduino
                                if reply == "PauseDrowsyDetection":
                                    drowsy_detection_active = False
                                    print("Drowsy detection paused by Arduino")

                                # Check if the resume signal is received from Arduino
                                elif reply == "ResumeDrowsyDetection":
                                    drowsy_detection_active = True
                                    print("Drowsy detection resumed by Arduino")
                                    drowsycount=0
                                    start_time=time.time()
                                    break

                    else:
                        print("Resetting drowsycount and timer")
                        drowsycount = 0
                        start_time = time.time()

            else:
                consecutive_drowsy_frames = 0

        cv2.imshow("Frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Add a small delay to make sure frames are processed
        time.sleep(0.1)

    cap.release()
    cv2.destroyAllWindows()
    ser.close()
if __name__ =="__main__":
    main()