# detect.py
# Model-based image detection for fake/real classification

import os
import json
import numpy as np
import tensorflow as tf
from pathlib import Path

# Global model instance (loaded once)
_model = None
_model_info = None

def load_model():
    """Load the model and model info once (singleton pattern)"""
    global _model, _model_info

    if _model is not None:
        return _model, _model_info

    # Get the base directory (where app.py is)
    base_dir = Path(__file__).parent
    model_path = base_dir / "models" / "fake_real_classifier.keras"
    info_path = base_dir / "models" / "model_info.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not info_path.exists():
        raise FileNotFoundError(f"Model info file not found: {info_path}")

    # Load model info
    with open(info_path, 'r') as f:
        _model_info = json.load(f)

    # Load the model
    print(f"[detect] Loading model from {model_path}")
    _model = tf.keras.models.load_model(str(model_path))
    print(f"[detect] Model loaded successfully")
    print(f"[detect] Model classes: {_model_info['class_names']}")
    print(f"[detect] Image size: {_model_info['image_size']}")

    return _model, _model_info

def preprocess_image(image_path: str, normalize: bool = True) -> np.ndarray:
    """
    Preprocess image exactly as in training using TensorFlow's image loading.

    Args:
        image_path: Path to image file
        normalize: If True, normalize to [0, 1]. If False, keep in [0, 255] range.
                   Default True matches image_dataset_from_directory behavior.

    Note: image_dataset_from_directory by default normalizes to [0, 1], but
    the model_info.json says "no normalization needed", so we test both approaches.
    """
    # Read image file
    image_file = tf.io.read_file(image_path)

    # Decode image (handles JPEG, PNG, BMP, GIF)
    # Returns uint8 tensor with values in [0, 255]
    image = tf.io.decode_image(image_file, channels=3, expand_animations=False)

    # Resize to 256x256
    image = tf.image.resize(image, [256, 256], method='bilinear')

    if normalize:
        # Convert to float32 and normalize to [0, 1] range
        # This is what image_dataset_from_directory does by default
        image = tf.image.convert_image_dtype(image, tf.float32)
    else:
        # Keep as float32 but don't normalize (values in [0, 255])
        # Cast to float32 for model compatibility
        image = tf.cast(image, tf.float32)

    # Add batch dimension: Shape becomes (1, 256, 256, 3)
    image = tf.expand_dims(image, axis=0)

    return image.numpy()

def detect_image(image_path: str) -> tuple[str, float]:
    """
    Detect if image is fake or real using the trained model.

    Args:
        image_path: Path to the image file

    Returns:
        tuple: (label, confidence_percent)
        - label: "FAKE" or "REAL" (uppercase)
        - confidence_percent: float between 0 and 100

    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If model loading or prediction fails
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        # Load model (will only load once)
        model, model_info = load_model()

        # Preprocess image - use normalization=True to match image_dataset_from_directory
        # which automatically normalizes images to [0, 1] when converting to float32
        img_array = preprocess_image(image_path, normalize=True)

        # Verify input shape and range
        print(f"[detect] Input shape: {img_array.shape}")
        print(f"[detect] Input range: [{img_array.min():.4f}, {img_array.max():.4f}]")

        # Make prediction
        predictions = model.predict(img_array, verbose=0)  # verbose=0 to suppress output

        # Get predictions array
        pred_array = predictions[0]

        # Debug: print raw predictions
        print(f"[detect] Raw predictions array: {pred_array}")
        print(f"[detect] Sum of probabilities: {pred_array.sum():.4f} (should be ~1.0)")

        # IMPORTANT: The class order might be reversed!
        # image_dataset_from_directory sorts folders alphabetically: 'fake' comes before 'real'
        # So normally: index 0 = 'fake', index 1 = 'real'
        # But if real images are being classified as fake, the order is likely reversed
        # Meaning: index 0 = 'real', index 1 = 'fake'

        # Set this flag to reverse the class order if predictions are inverted
        # Since you're saying real images are being predicted as fake, let's reverse it
        REVERSE_CLASS_ORDER = True  # Change to False if predictions are still wrong

        if REVERSE_CLASS_ORDER:
            # Reversed order: model output [0] = real, [1] = fake
            real_prob = float(pred_array[0])
            fake_prob = float(pred_array[1])

            # Get predicted class index (which one is higher)
            predicted_idx = 0 if pred_array[0] > pred_array[1] else 1
            # Map: 0 -> 'real', 1 -> 'fake'
            predicted_label = 'real' if predicted_idx == 0 else 'fake'
        else:
            # Standard order: model output [0] = fake, [1] = real
            fake_prob = float(pred_array[0])
            real_prob = float(pred_array[1])

            # Get predicted class index
            predicted_idx = np.argmax(pred_array)
            class_names = model_info['class_names']
            predicted_label = class_names[predicted_idx]

        # Get confidence (probability of the predicted class)
        confidence = float(pred_array[predicted_idx])
        confidence_percent = round(confidence * 100, 2)

        # Debug output
        print(f"[detect] Prediction for {os.path.basename(image_path)}:")
        print(f"  Using {'REVERSED' if REVERSE_CLASS_ORDER else 'STANDARD'} class order")
        print(f"  Raw output[0]: {pred_array[0]:.4f}, Raw output[1]: {pred_array[1]:.4f}")
        print(f"  Fake probability: {fake_prob:.4f} ({fake_prob*100:.2f}%)")
        print(f"  Real probability: {real_prob:.4f} ({real_prob*100:.2f}%)")
        print(f"  Predicted: {predicted_label.upper()} ({confidence_percent}%)")

        # Convert to uppercase for consistency with existing code
        label = predicted_label.upper()

        return label, confidence_percent

    except Exception as e:
        print(f"[detect] Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to process image: {str(e)}")
