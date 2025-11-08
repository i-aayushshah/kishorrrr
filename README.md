# Unmask.AI - Deepfake Detection System

<div align="center">

![Unmask.AI](https://img.shields.io/badge/Unmask.AI-Deepfake%20Detection-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Flask](https://img.shields.io/badge/Flask-3.0.3-red)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.19.0-orange)
![License](https://img.shields.io/badge/License-Educational%20Only-yellow)

**An AI-powered web application for detecting deepfake images with high accuracy**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Model Details](#model-details) • [Disclaimer](#disclaimer)

</div>

---

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Model Details](#model-details)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)

## 🎯 About

**Unmask.AI** is a deepfake detection system that uses advanced deep learning models to identify synthetic or AI-generated images. The application provides instant authenticity verification with confidence scoring, helping users determine whether an image is real or has been artificially generated.

### Key Capabilities

- ✅ **Real-time Analysis**: Upload and analyze images in seconds
- ✅ **High Accuracy**: 94.08% test accuracy on a dataset of 4,005 images
- ✅ **User Authentication**: Secure signup/signin with email verification
- ✅ **History Tracking**: Save and review your analysis history
- ✅ **Guest Mode**: Try the service without signing up (2 free analyses)
- ✅ **Password Management**: Secure password reset functionality
- ✅ **Profile Management**: Update user details and change passwords

## ✨ Features

### 🔐 Authentication & Security
- User registration with email verification
- Secure password hashing (Werkzeug)
- Password reset via email (6-digit code)
- Session-based guest access
- Email verification for account security

### 🖼️ Image Analysis
- Support for PNG, JPG, JPEG formats
- Real-time deepfake detection
- Confidence scoring (0-100%)
- Visual result display with color-coded badges
- Analysis history tracking

### 👤 User Management
- User profile management
- Change email (with verification)
- Change password (with current password verification)
- View analysis history
- Account verification status

### 🎨 User Interface
- Modern, responsive design
- Dark theme with gradient accents
- Mobile-friendly layout
- Toast notifications
- Smooth scrolling and animations

## 🛠️ Technology Stack

### Backend
- **Flask 3.0.3** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Login** - User session management
- **Flask-WTF** - Form handling and CSRF protection
- **Flask-Mail** - Email sending
- **Flask-Migrate** - Database migrations
- **TensorFlow 2.19.0** - Deep learning framework
- **Werkzeug** - Password hashing

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript** - Interactive features
- **Jinja2** - Template engine

### Database
- **SQLite** - Database (default, can be configured for PostgreSQL/MySQL)

### Machine Learning
- **TensorFlow/Keras** - Model framework
- **Custom CNN Model** - Deepfake detection model
- **PIL/Pillow** - Image processing

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/unmask-ai.git
cd unmask-ai
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv env
env\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Secret Key (generate a random string)
SECRET_KEY=your-secret-key-here

# Database URL (optional, defaults to SQLite)
DATABASE_URL=sqlite:///unmask_ai.db

# Upload Folder (optional, defaults to 'uploads')
UPLOAD_FOLDER=uploads

# Email Configuration (Gmail example)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Note:** For Gmail, you need to:
1. Enable 2-Factor Authentication
2. Generate an App Password (not your regular password)
3. Use the App Password in `MAIL_PASSWORD`

### Step 5: Set Up the Model

1. **Option A: Use Existing Model**
   - Place `fake_real_classifier.keras` in the `models/` directory
   - Ensure `models/model_info.json` is present

2. **Option B: Train Your Own Model**
   - Open `model_train.ipynb` in Jupyter Notebook
   - Follow the training instructions
   - The model will be saved to `models/fake_real_classifier.keras`

### Step 6: Initialize Database

```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

## ⚙️ Configuration

### Database Configuration

The application uses SQLite by default. To use PostgreSQL or MySQL:

1. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/unmask_ai
   # or
   DATABASE_URL=mysql://user:password@localhost/unmask_ai
   ```

2. Install the appropriate database driver:
   ```bash
   pip install psycopg2-binary  # For PostgreSQL
   # or
   pip install pymysql  # For MySQL
   ```

### Email Configuration

Configure SMTP settings in `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### File Upload Configuration

- **Max File Size**: 10 MB (configured in `config.py`)
- **Allowed Extensions**: PNG, JPG, JPEG
- **Upload Folder**: `uploads/` (created automatically)

## 🚀 Running the Application

### Development Mode

```bash
# Activate virtual environment (if not already activated)
# Windows: env\Scripts\activate
# Linux/Mac: source env/bin/activate

# Run the application
flask run
```

The application will be available at `http://localhost:5000`

### Production Mode

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Using Environment Variables

You can also set environment variables directly:

```bash
# Windows
set SECRET_KEY=your-secret-key
set DATABASE_URL=sqlite:///unmask_ai.db
flask run

# Linux/Mac
export SECRET_KEY=your-secret-key
export DATABASE_URL=sqlite:///unmask_ai.db
flask run
```

## 🤖 Model Details

### Model Architecture

- **Type**: Convolutional Neural Network (CNN)
- **Input Size**: 256×256×3 (RGB images)
- **Architecture**:
  - 5 Convolutional layers (16, 64, 128, 256, 512 filters)
  - MaxPooling2D layers
  - Dense layers (512 neurons)
  - Dropout (0.5)
  - Softmax output (2 classes: fake, real)

### Model Performance

- **Training Data**: 28,020 images
- **Test Accuracy**: 94.08%
- **Test Dataset**: 4,005 images
- **Epochs Trained**: 5
- **Total Parameters**: 10,997,634
- **Framework**: TensorFlow 2.19.0

### Model Files

- `models/fake_real_classifier.keras` - Model weights (125.93 MB, not in Git)
- `models/model_info.json` - Model metadata (included in Git)

See [models/README.md](models/README.md) for more details on obtaining the model file.

## 📁 Project Structure

```
unmask-ai/
│
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models (User, Upload)
├── forms.py               # WTForms form definitions
├── detect.py              # Model detection logic
├── email_utils.py         # Email sending utilities
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .gitignore            # Git ignore file
│
├── models/                # Model files directory
│   ├── fake_real_classifier.keras  # Model file (not in Git)
│   ├── model_info.json    # Model metadata
│   └── README.md          # Model documentation
│
├── templates/             # Jinja2 templates
│   ├── base.html          # Base template
│   ├── dashboard.html     # Main dashboard
│   ├── auth_signin.html   # Sign in page
│   ├── auth_signup.html   # Sign up page
│   ├── history.html       # Analysis history
│   ├── user_details.html  # User profile
│   ├── verification.html  # Email verification
│   ├── forgot_password.html
│   ├── reset_password.html
│   └── ...
│
├── static/                # Static files
│   ├── css/
│   │   └── app.css        # Custom styles
│   └── js/
│       └── app.js         # JavaScript functionality
│
├── uploads/               # Uploaded images (not in Git)
├── instance/              # Instance-specific files
│   └── unmask_ai.db      # SQLite database
│
├── migrations/            # Database migrations
│   └── versions/         # Migration versions
│
└── model_train.ipynb     # Model training notebook
```

## 🔌 API Endpoints

### Authentication
- `GET/POST /signup` - User registration
- `GET/POST /signin` - User login
- `GET/POST /signout` - User logout
- `GET/POST /forgot-password` - Request password reset
- `GET/POST /reset-password` - Reset password
- `GET/POST /verify` - Email verification

### Main Application
- `GET/POST /dashboard` - Main dashboard (upload & analyze)
- `GET /history` - View analysis history
- `GET/POST /user-details` - User profile management
- `GET /guest` - Guest mode access
- `GET /uploads/<filename>` - Serve uploaded images

### Additional Pages
- `GET /explore-plans` - Premium plans (coming soon)
- `GET /join-waitlist` - Waitlist registration (coming soon)

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError

**Solution:** Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Database Errors

**Solution:** Initialize and run migrations:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Issue: Email Not Sending

**Solution:**
1. Check your email credentials in `.env`
2. For Gmail, use an App Password (not your regular password)
3. Enable "Less secure app access" or use App Passwords
4. Check SMTP server and port settings

### Issue: Model Not Found

**Solution:**
1. Ensure `fake_real_classifier.keras` is in the `models/` directory
2. Check that `models/model_info.json` exists
3. Verify file permissions

### Issue: Image Upload Fails

**Solution:**
1. Check file size (max 10 MB)
2. Verify file format (PNG, JPG, JPEG only)
3. Ensure `uploads/` directory exists and is writable

### Issue: Guest Limit Reached

**Solution:**
- Sign up for a free account to get unlimited analyses
- Or clear your session/cookies to reset the guest count (not recommended)

## 📝 Usage Examples

### Running the Application

```bash
# 1. Activate virtual environment
source env/bin/activate  # Linux/Mac
# or
env\Scripts\activate  # Windows

# 2. Set environment variables (optional)
export SECRET_KEY=your-secret-key
export DATABASE_URL=sqlite:///unmask_ai.db

# 3. Run the application
flask run

# 4. Open browser and navigate to
# http://localhost:5000
```

### Using the Application

1. **Sign Up**: Create an account with email verification
2. **Sign In**: Login to your account
3. **Upload Image**: Go to dashboard and upload an image
4. **View Results**: See the analysis results with confidence score
5. **View History**: Check your analysis history
6. **Manage Profile**: Update your details in User Details page

### Guest Mode

1. Click "Try as guest" on the dashboard
2. Upload an image (limited to 2 analyses)
3. View results
4. Sign up for unlimited access

## 🔒 Security Considerations

- **Password Hashing**: Uses Werkzeug's secure password hashing
- **CSRF Protection**: Enabled on all forms
- **Session Security**: Secure session management with Flask-Login
- **Email Verification**: Required for account activation
- **File Upload Validation**: File type and size validation
- **SQL Injection Prevention**: Using SQLAlchemy ORM

## 📊 Database Schema

### Users Table
- `id` - Primary key
- `first_name`, `last_name`, `username`, `full_name`
- `email` - Unique, indexed
- `password_hash` - Hashed password
- `email_verified` - Boolean
- `verification_code`, `verification_code_expires`
- `reset_token`, `reset_token_expires`
- `created_at` - Timestamp

### Uploads Table
- `id` - Primary key
- `filename` - Uploaded file name
- `result_label` - "FAKE" or "REAL"
- `confidence` - Confidence score (0-100)
- `user_id` - Foreign key to users (nullable for guests)
- `guest_session_id` - Session ID for guests
- `created_at` - Timestamp

## 🤝 Contributing

This is an educational project. If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for **educational purposes only**.

## ⚠️ Disclaimer

<div align="center">

### 🎓 EDUCATIONAL PURPOSES ONLY

**This software is provided for educational and research purposes only.**

- This application is intended for learning about deepfake detection, machine learning, and web development
- The accuracy of deepfake detection may vary and should not be relied upon for critical decisions
- The creators and contributors are not responsible for any misuse of this software
- This tool should not be used to make definitive judgments about image authenticity
- Always verify important information through multiple sources
- Use responsibly and ethically

**By using this software, you agree that:**
- You understand this is an educational project
- You will not use it for malicious purposes
- You accept that results are not guaranteed to be accurate
- You are responsible for your own use of the software

**The developers make no warranties or representations about the accuracy, reliability, or suitability of this software for any purpose.**

</div>

## 🙏 Acknowledgments

- TensorFlow team for the deep learning framework
- Flask community for the excellent web framework
- All contributors and testers

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

<div align="center">

**Made with ❤️ for educational purposes**

**Unmask.AI** - Detecting Deepfakes, One Image at a Time

</div>

