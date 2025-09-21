# --- 1. Import Necessary Libraries ---

# OpenCV for image processing tasks like reading images, converting colors, blurring, etc.
import cv2
# NumPy for numerical operations, especially for handling image data as arrays.
import numpy as np
# A helper library to make working with OpenCV contours easier.
import imutils
# The core Flask framework for creating the web server and API endpoints.
from flask import Flask, request, jsonify
# Flask extension to handle Cross-Origin Resource Sharing (CORS), allowing your frontend to communicate with this backend.
from flask_cors import CORS
# For loading environment variables from a .env file for configuration.
from dotenv import load_dotenv
# For interacting with the operating system, used here to get environment variables.
import os
# Python's built-in logging module for robust, production-ready logging.
import logging

# --- 2. Initial Configuration ---

# Load environment variables from a file named '.env' in the same directory.
# This allows you to configure the app without changing the code.
load_dotenv()

# Initialize the Flask application. '__name__' helps Flask find static files and templates.
app = Flask(__name__)

# Configure basic logging to output messages of level INFO and above.
# In production, you might configure this to log to a file or a logging service.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define security constraints for file uploads.
# Set allowed file extensions to prevent users from uploading potentially harmful files.
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# Set a maximum file size (in bytes) to prevent denial-of-service attacks with very large files.
# Here, it's set to 5 MB. 1024 * 1024 * 5 = 5,242,880 bytes.
MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE_MB', 5)) * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Enable CORS for the Flask app. This is crucial for allowing web browsers
# from a different origin (e.g., a React app on http://localhost:3000) to access this API.
# 'origins' specifies which frontend URL is allowed to make requests.
# 'supports_credentials=True' allows the frontend to send cookies or authentication headers.
CORS(app, origins=os.getenv('CORS_ORIGIN'), supports_credentials=True)


# --- 3. Helper Function for File Validation ---

def allowed_file(filename):
    """
    Checks if the uploaded file has an allowed extension.
    """
    # Returns True if a '.' is in the filename and the part after the '.' is in ALLOWED_EXTENSIONS.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- 4. OMR Processing Logic ---

def process_omr(image_bytes, answer_key):
    """
    Processes an OMR sheet image from its byte representation and returns the calculated score.

    Args:
        image_bytes (bytes): The raw bytes of the image file.
        answer_key (dict): A dictionary mapping question index to the correct answer index.

    Returns:
        tuple: A tuple containing the final score (int) and the total number of questions (int).

    Raises:
        ValueError: If there's an error in image processing (e.g., no bubbles found).
    """
    # --- Step 4.1: Decode and Preprocess the Image ---
    # Convert the raw byte string into a 1D NumPy array.
    nparr = np.frombuffer(image_bytes, np.uint8)
    # Decode the NumPy array into an image format that OpenCV can use (BGR color).
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # If the image could not be decoded, raise an error.
    if image is None:
        raise ValueError(
            "Image data could not be decoded. The file may be corrupt or not a valid image format.")

    # Convert the color image to grayscale, as color information is not needed for this task.
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply a Gaussian blur to the grayscale image to reduce high-frequency noise, making contour detection more reliable.
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply Otsu's thresholding to create a binary (black and white) image.
    # THRESH_BINARY_INV inverts the colors (bubbles become white on a black background).
    # THRESH_OTSU automatically determines the optimal threshold value.
    thresh = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # --- Step 4.2: Find and Filter Contours (the Bubbles) ---
    # Find all the continuous shapes (contours) in the binary image.
    # RETR_EXTERNAL retrieves only the outermost contours.
    # CHAIN_APPROX_SIMPLE compresses horizontal, vertical, and diagonal segments, saving memory.
    cnts = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # imutils.grab_contours handles differences in return format between OpenCV versions.
    cnts = imutils.grab_contours(cnts)

    # This list will store contours that are likely to be OMR bubbles.
    questionCnts = []
    # Loop through every contour found in the image.
    for c in cnts:
        # Get the bounding box (x, y coordinates, width, height) of the contour.
        (x, y, w, h) = cv2.boundingRect(c)
        # Calculate the aspect ratio (width / height) of the bounding box.
        ar = w / float(h)
        # Filter the contours. We assume bubbles are at least 20x20 pixels
        # and have an aspect ratio close to 1 (making them squarish/circular).
        if w >= 20 and h >= 20 and 0.9 <= ar <= 1.2:
            questionCnts.append(c)

    # --- Step 4.3: Sanity Checks ---
    # If no contours met our criteria, the image is likely invalid.
    if not questionCnts:
        raise ValueError(
            "No bubbles were recognized. Please ensure the image is clear, well-lit, and properly aligned.")
    # If the number of bubbles is not a multiple of 4 (assuming 4 options per question), grading is impossible.
    if len(questionCnts) % 4 != 0:
        raise ValueError(
            f"An incomplete number of bubbles ({len(questionCnts)}) was detected. Each question must have 4 options.")
    # If the number of detected questions does not match the number of answers in the key, stop.
    if len(questionCnts) / 4 != len(answer_key):
        raise ValueError(
            f"Mismatch: The image has {int(len(questionCnts)/4)} questions, but the answer key is for {len(answer_key)} questions.")

    # --- Step 4.4: Sort Contours and Grade ---
    # Sort the filtered contours from top to bottom based on their y-coordinate.
    # This arranges the bubbles by question row.
    questionCnts = sorted(questionCnts, key=lambda c: cv2.boundingRect(c)[1])

    # Initialize the student's score.
    score = 0
    # The total number of questions is determined by the length of the provided answer key.
    total_questions = len(answer_key)

    # Loop through the contours in chunks of 4 (one question row at a time).
    # `q_idx` is the question number (0, 1, 2, ...).
    # `i` is the starting index in questionCnts for the current row (0, 4, 8, ...).
    for (q_idx, i) in enumerate(range(0, len(questionCnts), 4)):
        # For the current row, sort the 4 contours from left to right based on their x-coordinate.
        cnts = sorted(questionCnts[i:i + 4],
                      key=lambda c: cv2.boundingRect(c)[0])
        # This variable will store which bubble in the row is filled in.
        bubbled = None

        # Loop through the 4 sorted bubbles for the current question.
        # `j` will be the option index (0, 1, 2, or 3).
        for (j, c) in enumerate(cnts):
            # Create a black mask with the same dimensions as the binary image.
            mask = np.zeros(thresh.shape, dtype="uint8")
            # Draw the current bubble contour on the mask, filled with white.
            cv2.drawContours(mask, [c], -1, 255, -1)
            # Use bitwise AND to isolate the region of the bubble in the thresholded image.
            # This effectively "cuts out" the bubble.
            mask = cv2.bitwise_and(thresh, thresh, mask=mask)
            # Count the number of non-zero (white) pixels within the masked bubble.
            # A filled-in bubble will have many more white pixels than an empty one.
            total = cv2.countNonZero(mask)

            # Check if this bubble is the most filled-in one we've seen so far in this row.
            if bubbled is None or total > bubbled[0]:
                # If so, store its pixel count and its index `j`.
                bubbled = (total, j)

        # --- Step 4.5: Compare with Answer Key ---
        # A threshold to decide if a bubble is truly "filled". Adjust if needed.
        bubble_fill_threshold = 200
        # Check if a bubble was detected and if its pixel count exceeds our threshold.
        if bubbled and bubbled[0] > bubble_fill_threshold:
            # Get the correct answer's index for the current question from the answer key.
            correct_answer_idx = answer_key.get(q_idx)
            # Get the student's chosen answer's index.
            student_answer_idx = bubbled[1]
            # Compare the student's answer with the correct answer.
            if correct_answer_idx == student_answer_idx:
                # If they match, increment the score.
                score += 1

    # Return the final score and the total number of questions.
    return score, total_questions


# --- 5. API Endpoint Definition ---

@app.route('/grade', methods=['POST'])
def grade_sheet():
    """
    API endpoint to receive an OMR sheet image and an answer key, then return the score.
    Expects a multipart/form-data request with:
    - An image file under the key 'omr'.
    - A comma-separated string of answers under the key 'answers' (e.g., "1,4,2,3").
    """
    # --- Step 5.1: Validate Request and File ---
    # Check if the 'omr' file part is in the request.
    if 'omr' not in request.files:
        app.logger.warning("Grading attempt failed: No image file provided.")
        return jsonify({"status": "error", "message": "No image file provided in 'omr' field."}), 400

    # Get the file object from the request.
    file = request.files['omr']

    # Check if the user submitted an empty file part without a filename.
    if file.filename == '':
        app.logger.warning("Grading attempt failed: No file selected.")
        return jsonify({"status": "error", "message": "No file selected."}), 400

    # Validate the file extension using our helper function.
    if not allowed_file(file.filename):
        app.logger.warning(
            f"Grading attempt failed: Invalid file type '{file.filename}'.")
        return jsonify({"status": "error", "message": "Invalid file type. Please upload a PNG, JPG, or JPEG image."}), 400

    # --- Step 5.2: Parse and Validate Answer Key ---
    # Get the answer key string from the form data.
    answers_str = request.form.get('answers')
    if not answers_str:
        app.logger.warning("Grading attempt failed: No answer key provided.")
        return jsonify({"status": "error", "message": "No answer key provided in 'answers' field."}), 400

    # This 'try' block handles the main logic and catches potential errors.
    try:
        # --- Step 5.3: Process Inputs ---
        # Read the entire file content into memory as bytes.
        image_bytes = file.read()

        # Parse the answers string into the dictionary format needed by `process_omr`.
        try:
            # Split "1,4,2,3" into ['1', '4', '2', '3'].
            # Convert each string number to an integer and subtract 1 to make it 0-indexed.
            # (e.g., answer '1' corresponds to index 0).
            answer_values = [int(ans.strip()) -
                             1 for ans in answers_str.split(',')]
            # Create the final dictionary, e.g., {0: 0, 1: 3, 2: 1, 3: 2}.
            answer_key = {i: val for i, val in enumerate(answer_values)}
        except (ValueError, IndexError):
            # This catches errors if the string contains non-numbers or is malformed.
            app.logger.warning(
                f"Grading attempt failed: Invalid answer key format '{answers_str}'.")
            return jsonify({"status": "error", "message": "Invalid answer key format. Must be a comma-separated list of numbers (e.g., '1,4,2,3')."}), 400

        # --- Step 5.4: Call Processing Function and Return Result ---
        # Call the main OMR processing function with the image data and the parsed answer key.
        score, total_questions = process_omr(image_bytes, answer_key)

        # Log a successful grading event.
        app.logger.info(
            f"Successfully graded sheet '{file.filename}'. Score: {score}/{total_questions}.")
        # Return a successful JSON response with the score.
        return jsonify({"status": "success", "score": score, "total_questions": total_questions}), 200

    # --- Step 5.5: Handle Errors Gracefully ---
    # Catch specific errors raised from the `process_omr` function.
    except ValueError as e:
        # Log the specific processing error.
        app.logger.error(f"Processing error for '{file.filename}': {e}")
        # Return a user-friendly error message.
        return jsonify({"status": "error", "message": str(e)}), 400
    # Catch any other unexpected exceptions that might occur.
    except Exception as e:
        # Log the full, unexpected error for debugging.
        app.logger.critical(
            f"An unexpected internal error occurred: {e}", exc_info=True)
        # Return a generic server error message to the user.
        return jsonify({"status": "error", "message": "An internal server error occurred. Please try again later."}), 500


# # --- 6. Development Server ---

# # This block ensures the following code only runs when the script is executed directly
# # (not when imported as a module).
# if __name__ == '__main__':
#     # NOTE: The Flask development server (app.run) is for development and testing ONLY.
#     # In a production environment, use a production-grade WSGI server like Gunicorn or uWSGI.
#     # Example (Gunicorn): gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
#     # Use host='0.0.0.0' to make the app accessible on your local network.
#     app.run(host='0.0.0.0', port=8000, debug=True)
