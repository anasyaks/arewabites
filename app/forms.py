# northern-market-hub/app/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import Vendor, Review
import re

class RegistrationForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_name = StringField('Contact Name', validators=[DataRequired(), Length(min=2, max=100)])
    whatsapp_number = StringField('WhatsApp Number (e.g., 23480...)', validators=[DataRequired(), Length(min=10, max=20)])
    location_zone = StringField('Location Zone', validators=[DataRequired(), Length(min=2, max=100)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    logo_file = FileField('Business Logo (PNG, JPG)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    referral_code = StringField('Referral Code (Optional)', validators=[Length(max=10)])
    submit = SubmitField('Register')
    
    def validate_whatsapp_number(self, whatsapp_number):
        if not re.match(r'^\d{10,20}$', whatsapp_number.data):
            raise ValidationError('Invalid WhatsApp number format. Please include country code, e.g., 23480...')

    def validate_email(self, email):
        user = Vendor.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')
        
    def validate_business_name(self, business_name):
        vendor = Vendor.query.filter_by(business_name=business_name.data).first()
        if vendor:
            raise ValidationError('That business name is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddSnackForm(FlaskForm):
    name = StringField('Snack Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price (₦)', validators=[DataRequired(), NumberRange(min=0.01)])
    media_file = FileField('Snack Media (Image/Video)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'mp4', 'mov'], 'Images or Videos only!')])
    submit = SubmitField('Add Snack')

class SearchForm(FlaskForm):
    location_zone = StringField('Location Zone', validators=[Length(max=100)])
    snack_type = StringField('Snack Type', validators=[Length(max=100)])
    submit = SubmitField('Search')

class VendorEditForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_name = StringField('Contact Name', validators=[DataRequired(), Length(min=2, max=100)])
    whatsapp_number = StringField('WhatsApp Number', validators=[DataRequired(), Length(min=10, max=20)])
    location_zone = StringField('Location Zone', validators=[DataRequired(), Length(min=2, max=100)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_verified = BooleanField('Verified')
    is_admin = BooleanField('Admin')
    submit = SubmitField('Update Vendor')

class SnackEditForm(FlaskForm):
    name = StringField('Snack Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price (₦)', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Update Snack')
    
class UpdateProfileForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_name = StringField('Contact Person', validators=[DataRequired(), Length(min=2, max=100)])
    whatsapp_number = StringField('WhatsApp Number', validators=[DataRequired(), Length(min=10, max=20)])
    location_zone = StringField('Location Zone', validators=[DataRequired(), Length(min=2, max=100)])
    state = StringField('State', validators=[DataRequired(), Length(min=2, max=100)])
    logo_file = FileField('Update Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Update Profile')

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Submit Review')

class AdForm(FlaskForm):
    title = StringField('Ad Title', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Ad Content', validators=[DataRequired()])
    link_url = StringField('Link URL', validators=[DataRequired()])
    media_file = FileField('Ad Media (Image/Video)', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'mp4', 'mov'], 'Images or Videos only!')])
    is_active = BooleanField('Is Active?')
    submit = SubmitField('Submit Ad')

class VendorSearchForm(FlaskForm):
    business_name = StringField('Business Name', validators=[Length(max=100)])
    location_zone = StringField('Location Zone', validators=[Length(max=100)])
    submit = SubmitField('Search Vendors')