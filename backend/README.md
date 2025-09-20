# OMR Sheet Evaluation API

This project provides a Python-based API for automatically grading Optical Mark Recognition (OMR) sheets from images. The system uses OpenCV for image processing to identify and score the bubbled answers and Flask to expose this functionality as a web API.

## Features

- **Automatic Grading:** Scores OMR sheets from an uploaded image.
- **OpenCV-Powered:** Utilizes robust image processing techniques to accurately detect bubbles.
- **Flask API:** A simple and clean API for easy integration with other services.
- **Error Handling:** Provides clear feedback for common issues like missing files, invalid images, or poor bubble detection.

## How It Works

The core of the application is the OMR processing pipeline, which involves the following steps:

1.  **Image Preprocessing:**
    *   The uploaded image is decoded and converted to grayscale.
    *   A Gaussian blur is applied to reduce noise.
    *   Adaptive thresholding (Otsu's method) is used to create a binary image, making the bubbles stand out.

2.  **Bubble Detection:**
    *   Contours are detected in the binary image.
    *   These contours are filtered based on their aspect ratio and size to isolate the circular bubble shapes.

3.  **Answer Sorting:**
    *   The detected bubbles are sorted from top to bottom to establish the question order.

4.  **Grading Logic:**
    *   The system iterates through the questions, processing four bubbles at a time.
    *   For each question, the bubbles are sorted from left to right.
    *   It identifies which bubble has been filled in by analyzing the number of non-zero pixels within its contour.
    *   The selected answer is compared against a predefined answer key.
    *   The final score is calculated based on the number of correct answers.

## API Endpoint

### Grade OMR Sheet

-   **Endpoint:** `/grade`
-   **Method:** `POST`
-   **Description:** Upload an OMR sheet image to be graded.
-   **Request:** `multipart/form-data` with an image file under the key `file`.

-   **Success Response (200):**
    ```json
    {
      "status": "success",
      "score": 4,
      "total_questions": 5
    }
    ```

-   **Error Responses (400, 500):**
    ```json
    {
      "status": "error",
      "message": "Descriptive error message."
    }
    ```

## Getting Started

### Prerequisites

-   Python 3.x
-   OpenCV
-   Flask
-   NumPy
-   imutils

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd OMR_Evaluation
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install opencv-python flask numpy imutils
    ```

### Running the Application

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

2.  **Run the Flask server:**
    ```bash
    python main.py
    ```

The API will be running at `http://0.0.0.0:5000`.

## Dependencies

-   **Flask:** For creating the web server and API endpoints.
-   **OpenCV-Python (`cv2`):** For all image processing tasks.
-   **NumPy:** For numerical operations and image manipulation.
-   **imutils:** For convenience functions used with OpenCV.
