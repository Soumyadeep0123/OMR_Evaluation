# OMR Sheet Evaluation API

This project provides a Python-based API for automatically grading Optical Mark Recognition (OMR) sheets from images. The system uses OpenCV for image processing to identify and score the bubbled answers and Flask to expose this functionality as a web API.

## Features

- **Automatic Grading:** Scores OMR sheets from an uploaded image.
- **OpenCV-Powered:** Utilizes robust image processing techniques to accurately detect bubbles.
- **Flask API:** A simple and clean API for easy integration with other services.
- **Error Handling:** Provides clear feedback for common issues like missing files, invalid images, or poor bubble detection.
- **Configuration:** Uses environment variables for flexible configuration.
- **Docker Support:** Includes a `Dockerfile` for easy containerization.

## How It Works

The core of the application is the OMR processing pipeline, which involves the following steps:

1.  **Image Preprocessing:**
    *   The uploaded image is decoded and converted to grayscale.
    *   A Gaussian blur is applied to reduce noise.
    *   Adaptive thresholding (Osu's method) is used to create a binary image, making the bubbles stand out.

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
-   **Description:** Upload an OMR sheet image and an answer key to be graded.
-   **Request:** `multipart/form-data`
    -   `omr`: The image file of the OMR sheet.
    -   `answers`: A comma-separated string of the correct answers (e.g., "1,4,2,3").
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
-   python-dotenv

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd OMR_Evaluation/backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies from `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Create a `.env` file in the `backend` directory and add the following environment variables:

```
CORS_ORIGIN=http://localhost:3000
MAX_FILE_SIZE_MB=5
```

-   `CORS_ORIGIN`: The origin allowed to make requests to the API.
-   `MAX_FILE_SIZE_MB`: The maximum allowed file size for uploads in megabytes.

### Running the Application

1.  **Run the Flask server:**
    ```bash
    python main.py
    ```

The API will be running at `http://0.0.0.0:8000`.

## Usage

You can use a tool like `curl` to test the API endpoint:

```bash
curl -X POST -F "omr=@/path/to/your/omr_sheet.jpg" -F "answers=1,2,3,4,1" http://localhost:8000/grade
```

Replace `/path/to/your/omr_sheet.jpg` with the actual path to your OMR sheet image.

## Docker

The project includes a `Dockerfile` to build and run the application in a Docker container.

### Build the Docker Image

```bash
docker build -t omr-evaluation-api .
```

### Run the Docker Container

```bash
docker run -p 8000:8000 -v $(pwd):/app omr-evaluation-api
```

The API will be accessible at `http://localhost:8000`.

## Dependencies

-   **Flask:** For creating the web server and API endpoints.
-   **Flask-Cors:** For handling Cross-Origin Resource Sharing (CORS).
-   **OpenCV-Python (`cv2`):** For all image processing tasks.
-   **NumPy:** For numerical operations and image manipulation.
-   **imutils:** For convenience functions used with OpenCV.
-   **python-dotenv:** For managing environment variables.