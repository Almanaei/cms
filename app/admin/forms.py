from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, BooleanField, 
    FileField, TextAreaField, SelectMultipleField,
    DateField, TimeField
)
from wtforms.validators import DataRequired, Email, Optional, URL, Length
from flask_wtf.file import FileAllowed

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    summary = TextAreaField('Summary', validators=[Optional(), Length(max=500)])
    category_id = SelectField('Category', validators=[DataRequired()], coerce=int)
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    published = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ], validators=[DataRequired()])
    slug = StringField('Slug', validators=[Optional(), Length(max=200)])
    meta_title = StringField('Meta Title', validators=[Optional(), Length(max=200)])
    meta_description = TextAreaField('Meta Description', validators=[Optional(), Length(max=300)])
    featured = BooleanField('Featured')
    allow_comments = BooleanField('Allow Comments', default=True)
    tags = SelectMultipleField('Tags', coerce=int)
    schedule = BooleanField('Schedule for Later')
    scheduled_date = DateField('Scheduled Date', validators=[Optional()])
    scheduled_time = TimeField('Scheduled Time', validators=[Optional()])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional()])
    role_id = SelectField('Role', validators=[DataRequired()], coerce=int)
    is_active = BooleanField('Active')
    profile_image = FileField('Profile Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    website = StringField('Website', validators=[Optional(), URL()])
    social_facebook = StringField('Facebook', validators=[Optional(), URL()])
    social_twitter = StringField('Twitter', validators=[Optional(), URL()])
    social_instagram = StringField('Instagram', validators=[Optional(), URL()])

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
