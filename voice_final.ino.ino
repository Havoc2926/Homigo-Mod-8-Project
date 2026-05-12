#include <PDM.h>
#include <TinyMLShield.h>

// 16-bit sample buffer from PDM
short sampleBuffer[256];
volatile int samplesRead = 0;

bool record = true;     // Start recording immediately
bool commandRecv = false;
String command = "";

void setup() {
  Serial.begin(115200);
  while (!Serial);

  initializeShield();

  // Setup PDM mic: 1 channel (mono), 16kHz
  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 16000)) {
    while (1); // Halt if mic fails
  }
}

void loop() {
  // Optional: toggle with button
  if (readShieldButton()) {
    delay(300); // Debounce
    record = !record;
  }

  // Optional: toggle with serial 'click'
  while (Serial.available()) {
    char c = Serial.read();
    if (c != '\n' && c != '\r') {
      command.concat(c);
    } else if (c == '\r') {
      commandRecv = true;
      command.toLowerCase();
    }
  }

  if (commandRecv && command == "click") {
    commandRecv = false;
    command = "";
    record = !record;
  }

  // Stream raw 16-bit audio when recording
  if (record && samplesRead > 0) {
    Serial.write((uint8_t*)sampleBuffer, samplesRead * 2); // 2 bytes/sample
    samplesRead = 0;
  }
}

void onPDMdata() {
  int bytesAvailable = PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  samplesRead = bytesAvailable / 2;

  // Optional: Apply gain
  float gain = 9.0;
  for (int i = 0; i < samplesRead; i++) {
    int32_t amplified = sampleBuffer[i] * gain;
    if (amplified > 32767) amplified = 32767;
    if (amplified < -32768) amplified = -32768;
    sampleBuffer[i] = (short)amplified;
  }
}
