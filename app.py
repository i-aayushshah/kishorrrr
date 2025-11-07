# app.py
import os
import secrets
from pathlib import Path

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, session
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, current_user, AnonymousUserMixin

from models import db, User, Upload
from forms import SignInForm, SignUpForm, UploadForm, ForgotPasswordForm, VerificationForm
from config import Config
from detect import detect_image


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
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created. Welcome!", "success")
            return redirect(url_for("dashboard"))
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
            login_user(user)
            flash("Signed in successfully.", "success")
            return redirect(url_for("dashboard"))
        return render_template("auth_signin.html", form=form)

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            flash("If an account exists, you'll receive reset instructions shortly.", "info")
            return redirect(url_for("signin"))
        return render_template("forgot_password.html", form=form)

    @app.route("/verify", methods=["GET", "POST"])
    def verify_account():
        form = VerificationForm()
        if form.validate_on_submit():
            flash("Verification submitted. Check your email for confirmation.", "success")
            return redirect(url_for("signin"))
        return render_template("verification.html", form=form)

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
        return {
            "is_guest": getattr(current_user, "is_guest", False),
            "is_authed": current_user.is_authenticated and not getattr(current_user, "is_guest", False),
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
