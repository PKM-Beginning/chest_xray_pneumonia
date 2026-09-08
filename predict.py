"""
predict.py

Runs the trained model on a single chest X-ray image and prints the
prediction + confidence. Optionally saves a Grad-CAM overlay.

Usage:
    python predict.py --image path/to/xray.jpeg --checkpoint best_model.pt
    python predict.py --image path/to/xray.jpeg --checkpoint best_model.pt --gradcam --out heatmap.png
"""
import argparse

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms, models

from gradcam import GradCAM, overlay_heatmap


def build_model_from_checkpoint(ckpt):
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(ckpt["model_state_dict"])
    return model


def preprocess(pil_image, img_size):
    tfms = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return tfms(pil_image).unsqueeze(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--checkpoint", default="best_model.pt")
    ap.add_argument("--gradcam", action="store_true", help="Also generate a Grad-CAM overlay")
    ap.add_argument("--out", default="gradcam_overlay.png")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.checkpoint, map_location=device)
    model = build_model_from_checkpoint(ckpt).to(device)
    model.eval()
    classes = ckpt["classes"]
    img_size = ckpt["img_size"]

    pil_image = Image.open(args.image)
    input_tensor = preprocess(pil_image, img_size).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        probs = F.softmax(output, dim=1)[0]
        pred_idx = probs.argmax().item()

    print(f"Prediction: {classes[pred_idx]}")
    print(f"Confidence: {probs[pred_idx].item():.4f}")
    print(f"Class probabilities: {dict(zip(classes, [round(p, 4) for p in probs.tolist()]))}")

    if args.gradcam:
        # requires grad, so re-run through the GradCAM wrapper (needs backward pass)
        input_tensor.requires_grad_(False)
        cam_extractor = GradCAM(model, model.layer4[-1])
        input_tensor_grad = preprocess(pil_image, img_size).to(device)
        heatmap, target_class = cam_extractor.generate(input_tensor_grad)
        overlay = overlay_heatmap(pil_image, heatmap)
        overlay.save(args.out)
        print(f"Grad-CAM overlay (explaining class '{classes[target_class]}') saved to {args.out}")
        print("Note: this heatmap shows which pixels most influenced the model's decision.")
        print("It is an interpretability aid, not a medical confirmation of pathology.")


if __name__ == "__main__":
    main()
