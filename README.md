
# Chest X-Ray Pneumonia Detection

A deep-learning project for binary classification of chest X-ray images as **NORMAL** or **PNEUMONIA** using transfer learning with **ResNet18**.

The project also includes **Grad-CAM explainability** to visualize image regions that influenced the model's prediction.

## Model

- Architecture: ResNet18
- Learning approach: Transfer learning
- Task: Binary image classification
- Classes:
  - NORMAL
  - PNEUMONIA
- Explainability: Grad-CAM

## Evaluation

The model was evaluated on a held-out test set.

- Test accuracy: **83.17%**
- ROC-AUC: **95.97%**
- Pneumonia recall: **99.74%**

## Application

A Streamlit interface allows users to:

1. Upload a chest X-ray
2. Obtain a NORMAL/PNEUMONIA prediction
3. View prediction confidence
4. View class probabilities
5. Generate a Grad-CAM visualization

## Project Structure

```text
chest-xray-pneumonia/
│
├── app.py
├── predict.py
├── best_model.pt
├── requirements.txt
├── README.md
│
├── data_split/
│   ├── train/
│   ├── val/
│   └── test/
│
└── *.png
