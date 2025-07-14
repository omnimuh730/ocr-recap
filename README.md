# ocr-recap

## Purpose

`ocr-recap` is a cross-platform desktop application designed to streamline the process of extracting text from images (OCR), copying it via a hotkey, and providing real-time translation support. The tool is ideal for users who frequently need to capture and translate text from screenshots or images.

## Features

- **Optical Character Recognition (OCR):** Extract text from images or screen regions quickly and accurately.
- **Hotkey Support:** Use a customizable hotkey to instantly copy recognized text to the clipboard.
- **Real-Time Translation:** Automatically translate recognized text into your preferred language.
- **Seamless Desktop Integration:** User-friendly interface built with React and Electron.
- **Local Communication:** Secure, fast communication between frontend and backend via localhost.

## Architecture

- **Frontend:** Built with React and Electron for a modern, responsive desktop experience.
- **Backend:** Python service handling OCR and translation logic.
- **Communication:** The frontend and backend communicate over localhost using an internal API (e.g., HTTP or WebSocket).

## Getting Started

1. **Clone the repository**
2. **Install dependencies** for both backend (Python) and frontend (Node.js/React/Electron)
3. **Run the backend** Python server
4. **Start the Electron app**

## Future Improvements

- Support for more OCR languages
- Customizable translation providers
- Enhanced hotkey configuration

---
This project is under active development.