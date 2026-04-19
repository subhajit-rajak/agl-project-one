# Check Your Health Application

This repository contains the source code for the Check Your Health Application. The project is separated into a Python-based machine learning backend and a Android frontend UI.

## Recording

https://github.com/user-attachments/assets/dd26d4c6-7d1d-44d5-9f6e-7580554d6ff2

## Requirements
- Git
- Python 3.9 or higher
- Android Studio
- Android SDK (API 26+)

## Getting Started

### 1. Clone the Repository
Open your command prompt or terminal and clone the repository:

```bash
git clone https://github.com/subhajit-rajak/agl-project-one.git
cd <repository-directory>
```

### 2. Running the Python Backend
The Android app relies on the local API running in the background. You must start this before using the mobile application.

1. Open a Command Prompt (cmd).
2. Navigate to the python directory:
```bash
cd python
```
3. Install the necessary dependencies:
```bash
pip install -r requirements.txt
```
4. Start the server using Uvicorn:
```bash
uvicorn app:app --port 5000 --host 0.0.0.0
```
Keep this window open. The server is now listening for requests on port 5000.

### 3. Running the Android Application
The Android application assumes the backend is running locally.

1. Open Android Studio.
2. Click "Open" and select the root directory of the cloned repository. 
3. Wait for Gradle to finish syncing the dependencies.
4. From the device dropdown menu in the top toolbar, select an Android Emulator.
5. Click the green "Run" button to deploy the application on the emulator.

Note: The Android Emulator automatically routes traffic to your computer's localhost using the special IP address 10.0.2.2, which is pre-configured in the source code.

### Running on a Physical Device
If you are deploying the app to a physical Android device rather than the emulator, you must update the API URL to point to your computer's network IP:

1. Guarantee your mobile device and computer are on the exact same Wi-Fi network.
2. Find your computer's local network IP by running `ipconfig` in Command Prompt (look for IPv4 Address).
3. In Android Studio, open the `app/src/main/java/com/subhajitrajak/agl/network/RetrofitClient.kt` file.
4. Replace `10.0.2.2` with your computer's IPv4 Address.
5. Build and run the app on your physical device.
