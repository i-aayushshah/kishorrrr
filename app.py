# app.py
import os
import secrets
from pathlib import Path

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, session, request
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, current_user, AnonymousUserMixin
from flask_mail import Mail

from models import db, User, Upload
from forms import SignInForm, SignUpForm, UploadForm, ForgotPasswordForm, VerificationForm, ResetPasswordForm
from config import Config
from detect import detect_image
from email_utils import send_verification_email, send_password_reset_email


def create_app():
    print("[app] create_app() called")  # <--- diagnostic print
    app = Flask(__name__, instance_relative_config=True)  # MUST be __name_
    app.config.from_object(Config)

    # Ensure upload folder exists
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    print(f"[app] UPLOAD_FOLDER = {app.config['UPLOAD_FOLDER']}")  # diagnostic

    # Init DB & migrations
    db.init_app(app)
    Migrate(app, db)

    # Init Mail
    mail = Mail(app)

    # Login manager
    login_manager = LoginManager(app)
    login_manager.login_view = "signin"
    login_manager.login_message_category = "warning"

    class GuestUser(AnonymousUserMixin):
        @property
        def is_guest(self):
            return True

    login_manager.anonymous_user = GuestUser

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route("/")
    def root():
        return redirect(url_for("dashboard"))

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
            return redirect(url_for("dashboard"))

        if request.method == "GET" and session.get('pending_verification_email'):
            # If there's a pending verification, take the user straight there
            flash("Finish verifying your email before creating another account.", "info")
            return redirect(url_for("verify_account"))

        form = SignUpForm()
        if form.validate_on_submit():
            email = form.email.data.lower().strip()
            username = form.username.data.strip()

            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash("Email is already registered.", "danger")
                return redirect(url_for("signin"))
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                flash("Username is already taken.", "danger")
                return redirect(url_for("signup"))
            user = User(
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                username=username,
                full_name=f"{form.first_name.data.strip()} {form.last_name.data.strip()}",
                email=email,
                password_hash=generate_password_hash(form.password.data),
                email_verified=False,
            )
            # Generate verification code
            code = user.generate_verification_code()
            db.session.add(user)
            db.session.commit()

            # Send verification email
            if send_verification_email(mail, user, code):
                flash("Account created! Please check your email for the verification code.", "success")
                session['pending_verification_email'] = email
                return redirect(url_for("verify_account"))
            else:
                flash("Account created, but failed to send verification email. Please contact support.", "warning")
                session['pending_verification_email'] = email
                return redirect(url_for("verify_account"))
        return render_template("auth_signup.html", form=form)

    @app.route("/signin", methods=["GET", "POST"])
    def signin():
        if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
            return redirect(url_for("dashboard"))

        form = SignInForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if not user or not check_password_hash(user.password_hash, form.password.data):
                flash("Invalid email or password.", "danger")
                return redirect(url_for("signin"))

            # Check if email is verified
            if not user.email_verified:
                flash("Please verify your email address before signing in. Check your email for the verification code.", "warning")
                session['pending_verification_email'] = user.email
                return redirect(url_for("verify_account"))

            login_user(user)
            flash("Signed in successfully.", "success")
            return redirect(url_for("dashboard"))
        return render_template("auth_signin.html", form=form)

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            email = form.email.data.lower().strip()
            user = User.query.filter_by(email=email).first()

            # Always show the same message for security (don't reveal if email exists)
            if user:
                # Generate reset code (6-digit code like verification)
                import random
                from datetime import datetime, timedelta
                reset_code = f"{random.randint(100000, 999999)}"
                user.verification_code = reset_code
                user.verification_code_expires = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()

                if send_password_reset_email(mail, user, reset_code):
                    session['pending_reset_email'] = email
                    flash("Password reset code sent to your email. Please check your inbox.", "success")
                    return redirect(url_for("reset_password"))
                else:
                    flash("Failed to send reset email. Please try again later.", "danger")
            else:
                flash("If an account exists, you'll receive reset instructions shortly.", "info")
            return redirect(url_for("signin"))
        return render_template("forgot_password.html", form=form)

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        form = ResetPasswordForm()
        email = session.get('pending_reset_email')

        if not email:
            flash("Please request a password reset first.", "warning")
            return redirect(url_for("forgot_password"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid reset request.", "danger")
            session.pop('pending_reset_email', None)
            return redirect(url_for("forgot_password"))

        if form.validate_on_submit():
            code = form.token.data.strip()

            if not user.is_verification_code_valid(code):
                flash("Invalid or expired reset code. Please request a new one.", "danger")
                form.token.data = ""
                return render_template("reset_password.html", form=form, email=email)

            # Update password
            user.password_hash = generate_password_hash(form.password.data)
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()

            session.pop('pending_reset_email', None)
            flash("Password reset successfully! You can now sign in.", "success")
            return redirect(url_for("signin"))

        form.token.data = ""  # Don't pre-fill token
        return render_template("reset_password.html", form=form, email=email)

    @app.route("/verify", methods=["GET", "POST"])
    def verify_account():
        form = VerificationForm()
        email = session.get('pending_verification_email')

        if not email:
            # If no pending verification, check if user is logged in but not verified
            if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
                if not current_user.email_verified:
                    email = current_user.email
                else:
                    flash("Your email is already verified.", "info")
                    return redirect(url_for("dashboard"))
            else:
                flash("Please sign up or sign in first.", "warning")
                return redirect(url_for("signup"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid verification request.", "danger")
            session.pop('pending_verification_email', None)
            return redirect(url_for("signup"))

        if form.validate_on_submit():
            code = form.code.data.strip()

            if not user.is_verification_code_valid(code):
                flash("Invalid or expired verification code. Please check your email or request a new code.", "danger")
                return render_template("verification.html", form=form, email=email)

            # Verify email
            user.email_verified = True
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()

            session.pop('pending_verification_email', None)
            flash("Email verified successfully! You can now sign in.", "success")

            # Auto-login if not already logged in
            if not current_user.is_authenticated or getattr(current_user, "is_guest", False):
                login_user(user)
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("dashboard"))

        return render_template("verification.html", form=form, email=email)

    @app.route("/resend-verification", methods=["POST"])
    def resend_verification():
        email = session.get('pending_verification_email')
        if not email:
            if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
                email = current_user.email
            else:
                flash("No pending verification found.", "warning")
                return redirect(url_for("signup"))

        user = User.query.filter_by(email=email).first()
        if user:
            code = user.generate_verification_code()
            db.session.commit()
            if send_verification_email(mail, user, code):
                flash("Verification code resent to your email.", "success")
            else:
                flash("Failed to resend verification email.", "danger")

        return redirect(url_for("verify_account"))

    @app.route("/guest")
    def guest():
        if "guest_session_id" not in session:
            session["guest_session_id"] = secrets.token_hex(16)
        flash("You are browsing as Guest. Sign up to keep your history across devices.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/signout")
    def signout():
        logout_user()
        session.pop("guest_session_id", None)
        flash("Signed out.", "info")
        return redirect(url_for("signin"))

    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    @app.route("/dashboard", methods=["GET", "POST"])
    def dashboard():
        form = UploadForm()
        result = None

        if form.validate_on_submit():
            file = form.image.data
            if file and allowed_file(file.filename):
                safe_name = f"{secrets.token_hex(8)}_{file.filename}"
                save_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
                file.save(save_path)

                label, confidence = detect_image(save_path)

                if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
                    upload = Upload(filename=safe_name, result_label=label, confidence=confidence, user_id=current_user.id)
                else:
                    guest_id = session.get("guest_session_id") or secrets.token_hex(16)
                    session["guest_session_id"] = guest_id
                    upload = Upload(filename=safe_name, result_label=label, confidence=confidence, guest_session_id=guest_id)

                db.session.add(upload)
                db.session.commit()

                result = {"label": label, "confidence": confidence, "filename": safe_name}
                flash(f"Result: {label} ({confidence}%)", "success")
            else:
                flash("Unsupported file type. Please upload PNG/JPG/JPEG.", "danger")

        return render_template("dashboard.html", form=form, result=result)

    @app.route("/history")
    def history():
        if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
            items = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.created_at.desc()).all()
        else:
            guest_id = session.get("guest_session_id")
            items = (
                Upload.query.filter_by(guest_session_id=guest_id)
                .order_by(Upload.created_at.desc())
                .all()
                if guest_id
                else []
            )
        return render_template("history.html", items=items)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename, as_attachment=False)

    @app.context_processor
    def inject_user_flags():
        is_authed = current_user.is_authenticated and not getattr(current_user, "is_guest", False)
        email_verified = False
        if is_authed:
            email_verified = getattr(current_user, "email_verified", False)
        return {
            "is_guest": getattr(current_user, "is_guest", False),
            "is_authed": is_authed,
            "email_verified": email_verified,
        }

    return app


if __name__ == "_main_":  # MUST be exactly this (two underscores on each side)
    print("[app] _main_ entry reached")  # diagnostic
    app = create_app()
    with app.app_context():
        print("[app] creating tables (if missing)...")  # diagnostic
        db.create_all()
    print("[app] starting Flask dev server on http://127.0.0.1:5000")  # diagnostic
    app.run(debug=True, host="127.0.0.1", port=5000)
