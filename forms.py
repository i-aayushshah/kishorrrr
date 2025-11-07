from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from flask_wtf.file import FileAllowed, FileRequired

PASSWORD_RULE = Regexp(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$',
    message="Password must be 8+ chars with at least one uppercase, one lowercase, and one digit."
)


class SignUpForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(min=2, max=80)])
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), PASSWORD_RULE])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")


class SignInForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Send reset link")


class VerificationForm(FlaskForm):
    code = StringField("Verification code", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify account")


class UploadForm(FlaskForm):
    image = FileField(
        "Upload face image",
        validators=[FileRequired(), FileAllowed(["png", "jpg", "jpeg"], "Images only!")]
    )
    submit = SubmitField("Analyze")
