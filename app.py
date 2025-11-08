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
from forms import SignInForm, SignUpForm, UploadForm, ForgotPasswordForm, VerificationForm, ResetPasswordForm, UserDetailsForm
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
        if request.method == "POST":
            # Check for validation errors and flash them
            if not form.validate():
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{getattr(form, field).label.text}: {error}", "danger")
                return render_template("auth_signup.html", form=form)

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
            # Clear guest detection count when signing in
            session.pop("guest_detection_count", None)
            session.pop("guest_session_id", None)
            flash("Signed in successfully.", "success")
            return redirect(url_for("dashboard"))
        return render_template("auth_signin.html", form=form)

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        form = ForgotPasswordForm()

        # If user is already signed in, pre-fill their email and lock it
        is_authed = current_user.is_authenticated and not getattr(current_user, "is_guest", False)
        if request.method == "GET" and is_authed:
            form.email.data = current_user.email

        if form.validate_on_submit():
            email = form.email.data.lower().strip()

            # If user is signed in, only allow reset for their registered email
            if is_authed:
                if email != current_user.email:
                    flash("You can only request a password reset for your registered email address.", "danger")
                    return render_template("forgot_password.html", form=form, is_authed=is_authed)
                user = current_user
            else:
                user = User.query.filter_by(email=email).first()
                # Always show the same message for security (don't reveal if email exists)
                if not user:
                    flash("If an account exists, you'll receive reset instructions shortly.", "info")
                    return redirect(url_for("signin"))

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

            # If user was signed in, redirect back to user details, otherwise to signin
            if is_authed:
                return redirect(url_for("reset_password"))
            return redirect(url_for("signin"))
        return render_template("forgot_password.html", form=form, is_authed=is_authed)

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        form = ResetPasswordForm()
        email = session.get('pending_reset_email')
        is_authed = current_user.is_authenticated and not getattr(current_user, "is_guest", False)

        if not email:
            flash("Please request a password reset first.", "warning")
            return redirect(url_for("forgot_password"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid reset request.", "danger")
            session.pop('pending_reset_email', None)
            return redirect(url_for("forgot_password"))

        if request.method == "POST":
            # Check for validation errors and flash them
            if not form.validate():
                for field, errors in form.errors.items():
                    for error in errors:
                        field_label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                        flash(f"{field_label}: {error}", "danger")
                form.token.data = ""
                return render_template("reset_password.html", form=form, email=email, is_authed=is_authed)

        if form.validate_on_submit():
            code = form.token.data.strip()

            if not user.is_verification_code_valid(code):
                flash("Invalid or expired reset code. Please request a new one.", "danger")
                form.token.data = ""
                return render_template("reset_password.html", form=form, email=email, is_authed=is_authed)

            # Update password
            user.password_hash = generate_password_hash(form.password.data)
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()

            session.pop('pending_reset_email', None)

            # Check if user is already signed in
            if is_authed and current_user.id == user.id:
                flash("Password reset successfully!", "success")
                return redirect(url_for("user_details"))
            else:
                flash("Password reset successfully! You can now sign in.", "success")
                return redirect(url_for("signin"))

        form.token.data = ""  # Don't pre-fill token
        return render_template("reset_password.html", form=form, email=email, is_authed=is_authed)

    @app.route("/verify", methods=["GET", "POST"])
    def verify_account():
        form = VerificationForm()
        email = session.get('pending_verification_email')
        pending_email_change = session.get('pending_email_change')

        # Check if this is an email change verification
        if pending_email_change:
            # This is an email change - look up user by user_id, not email
            user = User.query.get(pending_email_change['user_id'])
            if not user:
                flash("Invalid verification request.", "danger")
                session.pop('pending_email_change', None)
                session.pop('pending_verification_email', None)
                return redirect(url_for("signup"))
            email = pending_email_change['new_email']  # Display new email in template
        elif not email:
            # If no pending verification, check if user is logged in but not verified
            if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
                if not current_user.email_verified:
                    email = current_user.email
                    user = current_user
                else:
                    flash("Your email is already verified.", "info")
                    return redirect(url_for("dashboard"))
            else:
                flash("Please sign up or sign in first.", "warning")
                return redirect(url_for("signup"))
        else:
            # Regular verification - look up by email
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Invalid verification request.", "danger")
                session.pop('pending_verification_email', None)
                return redirect(url_for("signup"))

        if form.validate_on_submit():
            code = form.code.data.strip()

            if not user.is_verification_code_valid(code):
                flash("Invalid or expired verification code. Please check your email or request a new code.", "danger")
                is_authed = current_user.is_authenticated and not getattr(current_user, "is_guest", False)
                return render_template("verification.html", form=form, email=email, is_authed=is_authed)

            # If this is an email change, update the email in database
            if pending_email_change and pending_email_change['user_id'] == user.id:
                # Check if new email is already taken by another user
                existing_user = User.query.filter_by(email=pending_email_change['new_email']).first()
                if existing_user and existing_user.id != user.id:
                    flash("This email is already registered to another account.", "danger")
                    session.pop('pending_email_change', None)
                    session.pop('pending_verification_email', None)
                    return redirect(url_for("user_details"))

                # Update email in database
                user.email = pending_email_change['new_email']
                user.email_verified = True
                user.verification_code = None
                user.verification_code_expires = None
                db.session.commit()

                session.pop('pending_email_change', None)
                session.pop('pending_verification_email', None)

                flash("Email changed and verified successfully!", "success")
                return redirect(url_for("user_details"))
            else:
                # Regular email verification
                user.email_verified = True
                user.verification_code = None
                user.verification_code_expires = None
                db.session.commit()

                session.pop('pending_verification_email', None)

                # Auto-login if not already logged in
                if not current_user.is_authenticated or getattr(current_user, "is_guest", False):
                    login_user(user)
                    # Clear guest detection count when auto-logging in after verification
                    session.pop("guest_detection_count", None)
                    session.pop("guest_session_id", None)
                    flash("Email verified successfully! You can now sign in.", "success")
                    return redirect(url_for("dashboard"))
                else:
                    # User is already signed in, just verify the email
                    flash("Email verified successfully!", "success")
                    # Redirect based on where they came from
                    if request.referrer and 'user-details' in request.referrer:
                        return redirect(url_for("user_details"))
                    return redirect(url_for("dashboard"))

        is_authed = current_user.is_authenticated and not getattr(current_user, "is_guest", False)
        return render_template("verification.html", form=form, email=email, is_authed=is_authed)

    @app.route("/resend-verification", methods=["POST"])
    def resend_verification():
        email = session.get('pending_verification_email')
        pending_email_change = session.get('pending_email_change')

        if pending_email_change:
            # This is an email change - get user by user_id
            user = User.query.get(pending_email_change['user_id'])
            if not user:
                flash("Invalid verification request.", "danger")
                session.pop('pending_email_change', None)
                session.pop('pending_verification_email', None)
                return redirect(url_for("signup"))
            # Generate new code
            code = user.generate_verification_code()
            db.session.commit()

            # Send to new email
            from email_utils import send_verification_email
            temp_user = type('obj', (object,), {
                'email': pending_email_change['new_email'],
                'first_name': user.first_name
            })
            if send_verification_email(mail, temp_user, code):
                flash("Verification code resent to your new email address.", "success")
            else:
                flash("Failed to resend verification email. Please try again later.", "danger")
            return redirect(url_for("verify_account"))

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

    @app.route("/request-password-reset", methods=["POST"])
    def request_password_reset():
        """Request password reset code from user details page"""
        if not current_user.is_authenticated or getattr(current_user, "is_guest", False):
            flash("Please sign in to request a password reset.", "warning")
            return redirect(url_for("signin"))

        user = current_user
        # Generate reset code (6-digit code like verification)
        import random
        from datetime import datetime, timedelta
        reset_code = f"{random.randint(100000, 999999)}"
        user.verification_code = reset_code
        user.verification_code_expires = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

        if send_password_reset_email(mail, user, reset_code):
            session['pending_reset_email'] = user.email
            flash(f"Password reset code sent to {user.email}. Please check your inbox.", "success")
            return redirect(url_for("reset_password"))
        else:
            flash("Failed to send password reset email. Please try again later.", "danger")
            return redirect(url_for("user_details"))

    @app.route("/guest")
    def guest():
        if "guest_session_id" not in session:
            session["guest_session_id"] = secrets.token_hex(16)
        flash("You are browsing as Guest. Sign up to keep your history across devices.", "info")
        # Redirect with hash to trigger scroll to uploader
        return redirect(url_for("dashboard") + "#uploader")

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
        is_guest = not (current_user.is_authenticated and not getattr(current_user, "is_guest", False))

        # Check guest detection limit
        if is_guest:
            guest_detection_count = session.get("guest_detection_count", 0)
            if guest_detection_count >= 2:
                flash("You've reached the guest detection limit (2 analyses). Please sign up or sign in for unlimited access.", "warning")
                return render_template("dashboard.html", form=form, result=result, guest_limit_reached=True)

        if form.validate_on_submit():
            file = form.image.data
            if file and allowed_file(file.filename):
                # Check guest limit before processing
                if is_guest:
                    guest_detection_count = session.get("guest_detection_count", 0)
                    if guest_detection_count >= 2:
                        flash("You've reached the guest detection limit (2 analyses). Please sign up or sign in for unlimited access.", "warning")
                        return render_template("dashboard.html", form=form, result=result, guest_limit_reached=True)

                try:
                    # Ensure upload directory exists
                    upload_dir = Path(Config.UPLOAD_FOLDER)
                    upload_dir.mkdir(parents=True, exist_ok=True)

                    # Generate safe filename
                    safe_name = f"{secrets.token_hex(8)}_{file.filename}"
                    save_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)

                    # Save file
                    file.save(save_path)

                    # Verify file was saved
                    if not os.path.exists(save_path):
                        flash("Failed to save uploaded image. Please try again.", "danger")
                        return render_template("dashboard.html", form=form, result=result)

                    # Run detection
                    label, confidence = detect_image(save_path)

                    # Save to database
                    if current_user.is_authenticated and not getattr(current_user, "is_guest", False):
                        upload = Upload(
                            filename=safe_name,
                            result_label=label,
                            confidence=confidence,
                            user_id=current_user.id
                        )
                    else:
                        guest_id = session.get("guest_session_id") or secrets.token_hex(16)
                        session["guest_session_id"] = guest_id

                        # Increment guest detection count
                        session["guest_detection_count"] = session.get("guest_detection_count", 0) + 1

                        upload = Upload(
                            filename=safe_name,
                            result_label=label,
                            confidence=confidence,
                            guest_session_id=guest_id
                        )

                    db.session.add(upload)
                    db.session.commit()

                    result = {"label": label, "confidence": confidence, "filename": safe_name}
                    flash(f"Analysis complete: {label} ({confidence}%)", "success")

                    # Show remaining guest detections
                    if is_guest:
                        remaining = 2 - session.get("guest_detection_count", 0)
                        if remaining > 0:
                            flash(f"Guest detections remaining: {remaining}. Sign up for unlimited access!", "info")
                        else:
                            flash("You've reached the guest limit. Sign up for unlimited access!", "warning")

                except Exception as e:
                    db.session.rollback()
                    print(f"[dashboard] Error processing upload: {e}")
                    flash(f"An error occurred while processing your image: {str(e)}", "danger")
            else:
                flash("Unsupported file type. Please upload PNG/JPG/JPEG.", "danger")

        # Load model info for display
        try:
            import json
            model_info_path = Path(__file__).parent / "models" / "model_info.json"
            with open(model_info_path, 'r') as f:
                model_info = json.load(f)
        except Exception as e:
            print(f"[dashboard] Error loading model info: {e}")
            model_info = None

        # Get guest detection count
        guest_detection_count = session.get("guest_detection_count", 0) if is_guest else 0
        guest_remaining = max(0, 2 - guest_detection_count) if is_guest else None

        return render_template("dashboard.html", form=form, result=result, model_info=model_info,
                             guest_detection_count=guest_detection_count, guest_remaining=guest_remaining,
                             guest_limit_reached=is_guest and guest_detection_count >= 2)

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

    @app.route("/user-details", methods=["GET", "POST"])
    def user_details():
        if not current_user.is_authenticated or getattr(current_user, "is_guest", False):
            flash("Please sign in to access your account details.", "warning")
            return redirect(url_for("signin"))

        form = UserDetailsForm()

        if request.method == "GET":
            form.first_name.data = current_user.first_name
            form.last_name.data = current_user.last_name
            form.email.data = current_user.email

        if request.method == "POST":
            # Check for validation errors and flash them (except for optional password fields)
            if not form.validate():
                for field, errors in form.errors.items():
                    # Skip password and confirm if they're empty (optional fields)
                    if field in ['password', 'confirm'] and not form.password.data:
                        continue
                    for error in errors:
                        field_label = getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field
                        flash(f"{field_label}: {error}", "danger")
                # Re-populate form data
                form.first_name.data = form.first_name.data or current_user.first_name
                form.last_name.data = form.last_name.data or current_user.last_name
                form.email.data = form.email.data or current_user.email
                return render_template("user_details.html", form=form)

        if form.validate_on_submit():
            # Verify current password first
            if not check_password_hash(current_user.password_hash, form.current_password.data):
                flash("Current password is incorrect.", "danger")
                form.first_name.data = current_user.first_name
                form.last_name.data = current_user.last_name
                form.email.data = current_user.email
                return render_template("user_details.html", form=form)

            # Check if email is being changed and if it's already taken
            new_email = form.email.data.lower().strip()
            email_changed = new_email != current_user.email

            if email_changed:
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user and existing_user.id != current_user.id:
                    flash("Email is already registered to another account.", "danger")
                    form.first_name.data = current_user.first_name
                    form.last_name.data = current_user.last_name
                    form.email.data = current_user.email
                    return render_template("user_details.html", form=form)

            # Update user details
            current_user.first_name = form.first_name.data.strip()
            current_user.last_name = form.last_name.data.strip()
            current_user.full_name = f"{form.first_name.data.strip()} {form.last_name.data.strip()}"

            # If email changed, require verification before updating
            if email_changed:
                # Don't update email yet - store it in session for verification
                # Generate verification code
                code = current_user.generate_verification_code()
                db.session.commit()

                # Create a temporary user object with new email for sending verification
                # We'll send to the new email, but verify against current user
                from email_utils import send_verification_email
                temp_user = type('obj', (object,), {
                    'email': new_email,
                    'first_name': current_user.first_name
                })

                # Send verification email to the NEW email address
                if send_verification_email(mail, temp_user, code):
                    # Store pending email change in session
                    session['pending_email_change'] = {
                        'new_email': new_email,
                        'user_id': current_user.id
                    }
                    session['pending_verification_email'] = new_email
                    flash("A verification code has been sent to your new email address. Please verify to complete the email change.", "warning")
                    return redirect(url_for("verify_account"))
                else:
                    flash("Failed to send verification email. Please try again later.", "danger")
                    form.first_name.data = current_user.first_name
                    form.last_name.data = current_user.last_name
                    form.email.data = current_user.email
                    return render_template("user_details.html", form=form)
            else:
                current_user.email = new_email

            # Update password only if provided
            if form.password.data:
                from forms import PASSWORD_RULE
                import re
                if not re.match(PASSWORD_RULE.regex.pattern, form.password.data):
                    flash("Password must be 8+ chars with at least one uppercase, one lowercase, and one digit.", "danger")
                    form.first_name.data = current_user.first_name
                    form.last_name.data = current_user.last_name
                    form.email.data = current_user.email
                    return render_template("user_details.html", form=form)
                if form.password.data != form.confirm.data:
                    flash("Passwords do not match.", "danger")
                    form.first_name.data = current_user.first_name
                    form.last_name.data = current_user.last_name
                    form.email.data = current_user.email
                    return render_template("user_details.html", form=form)
                # Check if new password is same as current password
                if check_password_hash(current_user.password_hash, form.password.data):
                    flash("New password must be different from your current password.", "danger")
                    form.first_name.data = current_user.first_name
                    form.last_name.data = current_user.last_name
                    form.email.data = current_user.email
                    return render_template("user_details.html", form=form)
                current_user.password_hash = generate_password_hash(form.password.data)

            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("user_details"))

        return render_template("user_details.html", form=form)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename, as_attachment=False)

    @app.route("/explore-plans")
    def explore_plans():
        return render_template("explore_plans.html")

    @app.route("/join-waitlist")
    def join_waitlist():
        return render_template("join_waitlist.html")

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
