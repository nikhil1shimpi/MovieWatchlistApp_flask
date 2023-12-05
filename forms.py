from typing import Any
from flask_wtf import FlaskForm
from wtforms import URLField, PasswordField, TextAreaField, StringField, IntegerField, SubmitField
from wtforms.validators import InputRequired, EqualTo, NumberRange, Email, Length
# flask forms gives us added functionality t protect us from CSRF attacks.
# validators are validated in order they are defined in flask wtf

class MovieForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    director = StringField("Director", validators=[InputRequired()])
    year = IntegerField("Year", validators=[InputRequired(), NumberRange(min=1878, message="Please enter year in format YYYY.")])
    submit = SubmitField("Add Movie")

class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist: list[Any]) -> None:
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data =[]

class ExtendedMovieForm(MovieForm):
    cast = StringListField("Cast")
    series = StringListField("Series")
    tags = StringListField("Tags")
    description = StringListField("Description")
    video_link = URLField("video link")
    submit = SubmitField("Submit")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password =PasswordField("Password", validators=[InputRequired(), Length(min=4, max=20, message="Please enter password 4-20 character long")])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired(), EqualTo("password", message="This password didnot match with password field")])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password =PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")