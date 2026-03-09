# Cali Clear Admin - Android App

This is a simple Android WebView app that wraps the Cali Clear Admin panel.

## How to Build the APK

### Prerequisites
1. Install Android Studio (https://developer.android.com/studio)
2. Install JDK 17 or higher

### Steps

1. **Open the Project**
   - Open Android Studio
   - Click "Open" and select the `android` folder in this project

2. **Wait for Gradle Sync**
   - Android Studio will download dependencies automatically

3. **Update the URL** (Optional)
   - Open `app/src/main/java/com/caliclear/admin/MainActivity.kt`
   - Change the URL in `webView.loadUrl("YOUR_URL")` to your deployed URL

4. **Build APK**
   - Go to **Build > Build Bundle(s) / APK(s) > Build APK(s)**
   - Wait for build to complete
   - The APK will be at `app/build/outputs/apk/debug/app-debug.apk`

### Install on Phone

1. Transfer the APK to your phone (via USB, email, or cloud storage)
2. On your phone, tap the APK file to install
3. If asked, enable "Install from unknown sources"

## Features

- Full admin panel functionality
- Works like a native app
- No browser bar
- Offline capable (for cached pages)

## Note

For development, you can use a tunnel service like ngrok or devtunnels to test on your phone while the backend runs locally.
