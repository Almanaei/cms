from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, DateTimeField, FileField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Email
from flask_wtf.file import FileAllowed

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    summary = TextAreaField('Summary', validators=[Optional(), Length(max=500)])
    meta_title = StringField('Meta Title', validators=[Optional(), Length(max=200)])
    meta_description = TextAreaField('Meta Description', validators=[Optional(), Length(max=500)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    published = BooleanField('Published')
    schedule = BooleanField('Schedule')
    scheduled_date = StringField('Date', validators=[Optional()])
    scheduled_time = StringField('Time', validators=[Optional()])
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    tags = StringField('Tags', validators=[Optional()])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Active')
