import torch
from torchvision import models, transforms
from PIL import Image
from torchvision.utils import draw_bounding_boxes
import matplotlib.pyplot as plt
import torchvision.transforms.functional as F

# ✅ Load Faster R-CNN model
model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.eval()

# ✅ Load image and preprocess (Ensure it's RGB)
image = Image.open("resources/test_image.png").convert("RGB")  # Fix grayscale issue

# ✅ Apply transforms
transform = transforms.Compose([transforms.ToTensor()])
image = transform(image).unsqueeze(0)  # Shape: [1, 3, H, W]

# ✅ Fix potential shape mismatch
if image.shape[1] != 3:  # If image is not RGB, expand to 3 channels
    image = image.expand(-1, 3, -1, -1)  # Repeat across channel dimension

# ✅ Detect potholes
with torch.no_grad():
    predictions = model(image)

# ✅ Print results safely
for i, pred in enumerate(predictions):
    print(f"🔹 Prediction {i+1}: {pred}")


# ✅ Extract data from predictions
pred_boxes = predictions[0]['boxes']
pred_scores = predictions[0]['scores']
pred_labels = predictions[0]['labels']

# ✅ Filter out low-confidence predictions (e.g., threshold = 0.5)
confidence_threshold = 0.5
keep = pred_scores >= confidence_threshold

filtered_boxes = pred_boxes[keep]
filtered_scores = pred_scores[keep]
filtered_labels = pred_labels[keep]

# ✅ Draw bounding boxes on the original image
image_with_boxes = draw_bounding_boxes(
    image[0],  # Remove batch dimension
    boxes=filtered_boxes,
    labels=[f"{score:.2f}" for score in filtered_scores],
    colors="red",
    width=3
)

# ✅ Convert tensor back to PIL Image for displaying
image_with_boxes_pil = F.to_pil_image(image_with_boxes)

# ✅ Display the image with bounding boxes
plt.figure(figsize=(10, 10))
plt.axis('off')
plt.title("Detected Objects")
plt.imshow(image_with_boxes_pil)
plt.show()