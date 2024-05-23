const int trigPin = 4;     // Trig pin of the ultrasonic sensor
const int echoPin = 2;     // Echo pin of the ultrasonic sensor
const int buzzerPin = 12;  // Buzzer pin

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // Wait for a command from Python
  String command = Serial.readStringUntil(',');
  
  if (command == "Drowsy") {
    String drowsyCountStr = Serial.readStringUntil('\n');
    int drowsyCount = drowsyCountStr.toInt();

    if (drowsyCount < 2) {
      // Ring the buzzer for 5 seconds
      tone(buzzerPin, 5000);
      delay(5000);
      noTone(buzzerPin);
    } else if (drowsyCount == 2) {
      // Ring the buzzer until an object is detected by ultrasonic sensor
      Serial.println("PauseDrowsyDetection");
      while (true) {
        tone(buzzerPin, 5000);
        delay(100);

        digitalWrite(trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);

        // Read the duration of the echo pulse
        long duration = pulseIn(echoPin, HIGH);

        // Convert the duration to distance in cm
        int distance = duration * 0.034 / 2;

        // Print a message for debugging
        if (distance <= 3) {
          noTone(buzzerPin);
          Serial.println("ResumeDrowsyDetection");
          break; 
        }
      }
    }
  }
}
