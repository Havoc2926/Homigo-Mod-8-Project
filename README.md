# Homigo-Mod-8-Project

Homigo is a voice recognition based smart home controller built on a three tier architecture that uses an Arduino Nano 33 BLE Sense, Raspberry Pi 5, and a Flask web application. Homigo constantly listens for set voice commands and classifies them using an on device 1D Convolutional Neutral Network (CNN) to control Govee smart lights and Spotify playback instantly.

## Tech Stack

- Python (Flask, Spotipy, Psycopg2, PySerial)
- Arduino Nano 33 BLE Sense (C++)
- Edge Impulse (ML training and CNN creation)
- 1 dimensional CNN
- MFCC Audio Feature Extraction
- Raspberry Pi 5
- PostgreSQL
- Govee Smart Lights API
- Spotify Web API

## Architecture
### 1: Voice recognition on the Arduino
The Arduino captures audio via a built-in microphone and runs real time keyword inference locally using a 1D CNN with an average latency of approximately 65ms. This local processing ensures privacy, speed, and is also a sustainable way to run voice recognition within the power and memory constraints of the Arduino.

### 2: Smart home integration and web app on the Raspberry Pi 5
The Raspberry Pi is the intermediary between the Arduino and the APIs and acts as a gateway. It receives commands from the Arduino via serial, looks up user preferences in the PostgreSQL database, and makes the necessary API calls to control lights and music.

### 3: Govee smart lights and Spotify control
The Govee API allows for instant control over the colour and brightness of the user's connected smart lights. For Spotify integration, the designated playlist for a certain mood is played via the Spotify API through a Bluetooth speaker to set the desired mood.

## The CNN
At the heart of the system, is a lightweight 1D CNN trained through Edge Impulse to classify six commands: Homigo, House, Happy, On, Off, Unknown

### Model Parameters
- Input: MFCC features (13 coefficients, 16 mel filters, 150Hz to 6000Hz)
- Two convolutional layers (16 filters -> 32 filters, kernel size of 3)
- Dropout layers (rates 0.2, 0.25, 0.3) to prevent overfitting
- Softmax output classifier
- Window size: 1000ms, stride: 200ms

### Dataset
The dataset used to train the ML model was a mixture of the [Google Speech Commands v0.02 dataset](https://huggingface.co/datasets/google/speech_commands) and over 400 recorded samples of our custom keyword "Homigo", augmented with varying levels of noise.
An example of this can be found [here](homigo.1415.wav)

## Web Application
The user-facing part of this system is the Flask and PostgreSQL based web application which allows for:
- Signup and login to manage different user preferences
- Assigning custom light colours using an RGB picker
- Assigning Spotify playlists to each scene
- Triggering scenes remotely without voice commands

## Testing Results
| Test | Result |
|---|---|
| Keyword accuracy (quiet) | ~95% |
| Keyword accuracy (moderate noise) | 75% to 85% |
| Misclassification rate | ~5% |
| Inference latency | 60 to 70ms |
| End to end chain reliability | 100% in all tests |

