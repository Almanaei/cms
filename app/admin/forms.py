from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, Optional

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional()])
    role_id = SelectField('Role', validators=[DataRequired()], coerce=int)
    is_active = BooleanField('Active')
    profile_image = FileField('Profile Image')
