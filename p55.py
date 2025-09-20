import cv2
import numpy as np
import imutils

# ---------------- STEP 1: Load the OMR Sheet ----------------
image = cv2.imread("omr_sheet.jpg")
orig = image.copy()
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Preprocessing
blur = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

# ---------------- STEP 2: Detect Contours ----------------
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)

questionCnts = []

# Filter only circular/oval bubbles
for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)
    if w >= 20 and h >= 20 and 0.9 <= ar <= 1.2:  # approx circle
        questionCnts.append(c)

# Sort from top-to-bottom
questionCnts = sorted(questionCnts, key=lambda c: cv2.boundingRect(c)[1])

# ---------------- STEP 3: Define Answer Key ----------------
# Suppose 5 questions, each with options A-D
answer_key = {0: 1, 1: 2, 2: 2, 3: 3, 4: 1}  
# (question: correct option index)

# ---------------- STEP 4: Process Questions ----------------
score = 0
for (q, i) in enumerate(range(0, len(questionCnts), 4)):
    cnts = sorted(questionCnts[i:i + 4], key=lambda c: cv2.boundingRect(c)[0])  # left-to-right
    bubbled = None

    for (j, c) in enumerate(cnts):
        # Create a mask for the bubble
        mask = np.zeros(thresh.shape, dtype="uint8")
        cv2.drawContours(mask, [c], -1, 255, -1)

        # Count non-zero pixels in the bubble area
        mask = cv2.bitwise_and(thresh, thresh, mask=mask)
        total = cv2.countNonZero(mask)

        if bubbled is None or total > bubbled[0]:
            bubbled = (total, j)

    # Compare detected bubble with answer key
    color = (0, 0, 255)  # red by default
    k = answer_key[q]

    if bubbled[1] == k:
        color = (0, 255, 0)  # green if correct
        score += 1

    cv2.drawContours(orig, [cnts[k]], -1, color, 3)

# ---------------- STEP 5: Show Final Score ----------------
print(f"Final Score: {score}/{len(answer_key)}")

cv2.putText(orig, f"Score: {score}/{len(answer_key)}", (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

cv2.imshow("OMR Result", orig)
cv2.waitKey(0)
cv2.destroyAllWindows()
