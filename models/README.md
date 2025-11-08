# Model Files

## Model Information

The model file `fake_real_classifier.keras` (125.93 MB) is not included in this repository due to GitHub's 100 MB file size limit.

### Model Details
- **File**: `fake_real_classifier.keras`
- **Size**: 125.93 MB
- **Format**: Keras/TensorFlow
- **Accuracy**: 94.08% (test accuracy)
- **Training Data**: 28,020+ images
- **Input Size**: 256×256×3
- **Classes**: fake, real
- **Framework**: TensorFlow 2.19.0

### How to Get the Model

1. **If you have the model file locally:**
   - Place `fake_real_classifier.keras` in the `models/` directory
   - Ensure `models/model_info.json` is also present

2. **If you need to train the model:**
   - See `model_train.ipynb` for training instructions
   - The model will be saved to `models/fake_real_classifier.keras` after training

3. **For production deployment:**
   - Upload the model file to your server separately (not via Git)
   - Use cloud storage (AWS S3, Google Cloud Storage, etc.) if needed
   - Or use Git LFS if you need version control for the model

### Model Structure

The model uses a CNN architecture with:
- 5 Convolutional layers (16, 64, 128, 256, 512 filters)
- MaxPooling2D layers
- Dense layers (512 neurons)
- Dropout (0.5)
- Softmax output (2 classes)

### Files in Repository

- ✅ `model_info.json` - Model metadata (included in Git)
- ❌ `fake_real_classifier.keras` - Model weights (excluded from Git)

### Note

The model file is excluded from Git via `.gitignore`. Make sure to have the model file in the `models/` directory when running the application locally or in production.

