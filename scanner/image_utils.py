import cv2


def draw_frame_number(image, frame_number):
    position = (20, 30)  # X, Y coordinates (bottom-left of text)
    font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
    font_scale = 1  # Font size
    color = (0, 255, 0)  # Green color in BGR
    thickness = 2  # Thickness of the text
    line_type = cv2.LINE_AA  # Anti-aliased text

    # Add text to image
    cv2.putText(image, str(frame_number), position, font, font_scale, color, thickness, line_type)