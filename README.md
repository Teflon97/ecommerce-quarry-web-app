<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/0aca3292-8832-4401-a4af-6c834bcaa524

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCrf0VaS5EV71fei5RNxDIY82VF8Hd7LL8",
  authDomain: "quarry-app-771b0.firebaseapp.com",
  projectId: "quarry-app-771b0",
  storageBucket: "quarry-app-771b0.firebasestorage.app",
  messagingSenderId: "771202704926",
  appId: "1:771202704926:web:dbf775b4c9f3f86824b00f"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
