from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional()])
    role_id = SelectField('Role', validators=[DataRequired()], coerce=int)
    is_active = BooleanField('Active')
    profile_image = FileField('Profile Image')

class SettingsForm(FlaskForm):
    key = StringField('Key', validators=[DataRequired()])
    value = TextAreaField('Value', validators=[DataRequired()])
    type = SelectField('Type', choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON')
    ])
    description = TextAreaField('Description')
