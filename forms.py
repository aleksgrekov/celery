from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import MultipleFileField, StringField
from wtforms.validators import InputRequired, Email


class BlurImagesForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            FileRequired(),
            FileAllowed(['jpeg', 'jpg', 'png'], 'Image files only')
        ]
    )
    email = StringField(
        validators=[
            InputRequired(),
            Email()
        ]
    )


class SubscribeForm(FlaskForm):
    email = StringField(
        validators=[
            InputRequired(),
            Email()
        ]
    )
