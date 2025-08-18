import os
import secrets
from flask import render_template, url_for, flash, redirect, request, Blueprint, session, current_app
from flask_login import login_user, logout_user, login_required
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
import cloudinary.uploader # Import only uploader, as config is handled in __init__.py
import cloudinary.exceptions # Import exceptions for error handling

from app import db, bcrypt, login_manager
from app.models import Vendor, Snack, Review, Ad
from app.forms import RegistrationForm, LoginForm, AddSnackForm, SearchForm, VendorEditForm, SnackEditForm, UpdateProfileForm, ReviewForm, AdForm, VendorSearchForm

# Create a Blueprint named 'main'
main = Blueprint('main', __name__)

# --- CORRECTED FUNCTION TO UPLOAD TO CLOUDINARY ---
def upload_to_cloudinary(file, folder):
    try:
        # The Cloudinary configuration is already set globally in __init__.py
        # So, we just need to call the upload method with the file and folder.
        upload_result = cloudinary.uploader.upload(file, folder=folder)
        return upload_result['secure_url']
    except cloudinary.exceptions.Error as e:
        print(f"Cloudinary upload error: {e}")
        return None
# ----------------------------------------------------

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Vendor, int(user_id))

# Helper function for vendor verification status
def vendor_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('vendor_id'):
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function for admin verification status
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        vendor_id = session.get('vendor_id')
        if not vendor_id:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('main.login'))
        vendor = db.session.get(Vendor, vendor_id)
        if not vendor or not vendor.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to make 'now' and 'current_vendor' available to all templates
@main.context_processor
def inject_globals():
    current_vendor = None
    if 'vendor_id' in session:
        current_vendor = db.session.get(Vendor, session.get('vendor_id'))
    return {
        'now': datetime.utcnow(),
        'current_vendor': current_vendor
    }

@main.route("/")
@main.route("/home")
def home():
    search_form = SearchForm()
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    fresh_snacks = Snack.query.filter(Snack.date_posted > one_day_ago).order_by(Snack.date_posted.desc()).all()
    vendors = Vendor.query.order_by(Vendor.business_name).all()
    ads = Ad.query.filter_by(is_active=True).all()
    
    return render_template('home.html', snacks=fresh_snacks, vendors=vendors, search_form=search_form, ads=ads)

@main.route("/search", methods=['GET'])
def search_snacks():
    search_form = SearchForm(request.args)
    results = []

    location_zone = search_form.location_zone.data
    snack_type = search_form.snack_type.data

    if search_form.validate():
        query = db.session.query(Snack).join(Vendor).filter(
            Snack.date_posted > datetime.utcnow() - timedelta(days=1)
        )
        if location_zone:
            query = query.filter(Vendor.location_zone.ilike(f'%{location_zone}%'))
        if snack_type:
            query = query.filter(Snack.name.ilike(f'%{snack_type}%'))
        results = query.order_by(Snack.date_posted.desc()).all()

    return render_template('search_results.html', search_form=search_form, results=results)

@main.route("/register", methods=['GET', 'POST'])
def register_vendor():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # New upload logic
        # You must replace this with a URL to a default image you've uploaded to Cloudinary.
        # Example: 'https://res.cloudinary.com/dlwkdmh7b/image/upload/v1234567890/logos/default_logo.png'
        default_logo_url = 'https://res.cloudinary.com/dlwkdmh7b/image/upload/v1723991206/logos/default.png' 
        logo_url = upload_to_cloudinary(form.logo_file.data, 'logos') if form.logo_file.data else default_logo_url

        referrer_vendor = None
        if form.referral_code.data:
            referrer_vendor = Vendor.query.filter_by(referral_code=form.referral_code.data).first()
        
        vendor = Vendor(
            business_name=form.business_name.data,
            contact_name=form.contact_name.data,
            whatsapp_number=form.whatsapp_number.data,
            location_zone=form.location_zone.data,
            state=form.state.data,
            email=form.email.data,
            password=hashed_password,
            logo_url=logo_url,
            referred_by=referrer_vendor.id if referrer_vendor else None
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register_vendor.html', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        vendor = Vendor.query.filter_by(email=form.email.data).first()
        if vendor and bcrypt.check_password_hash(vendor.password, form.password.data):
            session['vendor_id'] = vendor.id
            login_user(vendor, remember=form.remember.data)
            flash('Login successful!', 'success')
            if vendor.is_admin:
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.vendor_dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('vendor_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@main.route("/vendor/<int:vendor_id>")
def vendor_profile(vendor_id):
    vendor = db.session.get(Vendor, vendor_id)
    if not vendor:
        return 'Vendor not found', 404
    
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    
    snacks_with_reviews = db.session.query(Snack, func.avg(Review.rating).label('average_rating')) \
        .outerjoin(Review) \
        .filter(Snack.vendor_id == vendor.id) \
        .filter(Snack.date_posted > one_day_ago) \
        .group_by(Snack.id) \
        .order_by(Snack.date_posted.desc()) \
        .all()
        
    return render_template('vendor_profile.html', vendor=vendor, snacks=snacks_with_reviews)
    
@main.route("/chat/<int:vendor_id>")
@vendor_only
def chat(vendor_id):
    vendor_to_chat_with = db.session.get(Vendor, vendor_id)
    if not vendor_to_chat_with:
        flash('Vendor not found.', 'danger')
        return redirect(url_for('main.home'))

    chat_history = [] 

    return render_template('chat.html', vendor_to_chat_with=vendor_to_chat_with, chat_history=chat_history)

@main.route("/snack/<int:snack_id>/review", methods=['GET', 'POST'])
def review_snack(snack_id):
    snack = db.session.get(Snack, snack_id)
    if not snack:
        flash('Snack not found.', 'danger')
        return redirect(url_for('main.home'))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            snack_id=snack.id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Thank you for your review!', 'success')
        return redirect(url_for('main.vendor_profile', vendor_id=snack.vendor_id))
        
    return render_template('review_snack.html', form=form, snack=snack)

@main.route("/vendors")
def list_vendors():
    search_form = VendorSearchForm()
    vendors = Vendor.query.order_by(Vendor.business_name).all()
    return render_template('list_vendors.html', vendors=vendors, search_form=search_form)

@main.route("/search_vendors", methods=['GET'])
def search_vendors():
    search_form = VendorSearchForm(request.args)
    results = []

    business_name = search_form.business_name.data
    location_zone = search_form.location_zone.data
    
    query = Vendor.query

    if business_name:
        query = query.filter(Vendor.business_name.ilike(f'%{business_name}%'))
    if location_zone:
        query = query.filter(Vendor.location_zone.ilike(f'%{location_zone}%'))

    results = query.order_by(Vendor.business_name).all()

    return render_template('vendor_search_results.html', search_form=search_form, results=results)


@main.route("/dashboard")
@vendor_only
def vendor_dashboard():
    vendor = db.session.get(Vendor, session.get('vendor_id'))
    if not vendor:
        session.pop('vendor_id', None)
        flash('You have been logged out due to an issue.', 'danger')
        return redirect(url_for('main.login'))
    
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    snacks = Snack.query.filter_by(vendor_id=vendor.id).filter(Snack.date_posted > one_day_ago).order_by(Snack.date_posted.desc()).all()
    
    referrals_count = Vendor.query.filter_by(referred_by=vendor.id).count()

    return render_template('vendor_dashboard.html', vendor=vendor, snacks=snacks, referrals_count=referrals_count)

@main.route("/add_snack", methods=['GET', 'POST'])
@vendor_only
def add_snack():
    form = AddSnackForm()
    vendor_id = session.get('vendor_id')
    vendor = db.session.get(Vendor, vendor_id)
    
    if form.validate_on_submit():
        media_url = None
        media_type = 'image'
        if form.media_file.data:
            media_url = upload_to_cloudinary(form.media_file.data, 'snack_media')
            if media_url and (media_url.lower().endswith('.mp4') or media_url.lower().endswith('.mov')):
                media_type = 'video'
            
        snack = Snack(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            media_url=media_url,
            media_type=media_type,
            vendor_id=vendor.id
        )
        db.session.add(snack)
        db.session.commit()
        flash('Snack added successfully!', 'success')
        return redirect(url_for('main.vendor_dashboard'))
    return render_template('add_snack.html', form=form)

@main.route("/delete_snack/<int:snack_id>", methods=['POST'])
@vendor_only
def delete_snack(snack_id):
    snack = db.session.get(Snack, snack_id)
    vendor_id = session.get('vendor_id')

    if snack.vendor_id != vendor_id:
        flash('You do not have permission to delete this snack.', 'danger')
        return redirect(url_for('main.vendor_dashboard'))
    
    # New delete logic: No need to delete from local file system anymore
    db.session.delete(snack)
    db.session.commit()
    flash('Snack deleted successfully.', 'success')
    return redirect(url_for('main.vendor_dashboard'))

@main.route("/admin")
@admin_only
def admin_dashboard():
    vendors = Vendor.query.order_by(Vendor.business_name).all()
    all_snacks = Snack.query.order_by(Snack.date_posted.desc()).all()
    all_ads = Ad.query.order_by(Ad.date_posted.desc()).all()
    return render_template('admin_dashboard.html', vendors=vendors, all_snacks=all_snacks, all_ads=all_ads)

@main.route("/verify_vendor/<int:vendor_id>", methods=['POST'])
@admin_only
def verify_vendor(vendor_id):
    vendor_to_verify = db.session.get(Vendor, vendor_id)
    vendor_to_verify.is_verified = True
    db.session.commit()
    flash(f'Vendor "{vendor_to_verify.business_name}" has been verified!', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/edit_vendor/<int:vendor_id>", methods=['GET', 'POST'])
@admin_only
def admin_edit_vendor(vendor_id):
    vendor = db.session.get(Vendor, vendor_id)
    if not vendor:
        flash('Vendor not found.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
        
    form = VendorEditForm(obj=vendor)
    if form.validate_on_submit():
        form.populate_obj(vendor)
        db.session.commit()
        flash('Vendor details updated successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('admin_edit_vendor.html', form=form, vendor=vendor)

@main.route("/admin/delete_vendor/<int:vendor_id>", methods=['POST'])
@admin_only
def admin_delete_vendor(vendor_id):
    vendor_to_delete = db.session.get(Vendor, vendor_id)
    if vendor_to_delete and not vendor_to_delete.is_admin:
        db.session.delete(vendor_to_delete)
        db.session.commit()
        flash(f'Vendor "{vendor_to_delete.business_name}" has been deleted!', 'success')
    else:
        flash('Cannot delete this vendor.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/edit_snack/<int:snack_id>", methods=['GET', 'POST'])
@admin_only
def admin_edit_snack(snack_id):
    snack = db.session.get(Snack, snack_id)
    if not snack:
        flash('Snack not found.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    form = SnackEditForm(obj=snack)
    if form.validate_on_submit():
        form.populate_obj(snack)
        db.session.commit()
        flash('Snack details updated successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_edit_snack.html', form=form, snack=snack)

@main.route("/admin/delete_snack/<int:snack_id>", methods=['POST'])
@admin_only
def admin_delete_snack(snack_id):
    snack_to_delete = db.session.get(Snack, snack_id)
    if snack_to_delete:
        db.session.delete(snack_to_delete)
        db.session.commit()
        flash(f'Snack "{snack_to_delete.name}" has been deleted!', 'success')
    else:
        flash('Snack not found.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@main.route("/admin/edit_profile", methods=['GET', 'POST'])
@admin_only
def admin_edit_profile():
    admin = db.session.get(Vendor, session.get('vendor_id'))
    form = UpdateProfileForm(obj=admin)
    if form.validate_on_submit():
        # New upload logic
        if form.logo_file.data:
            logo_url = upload_to_cloudinary(form.logo_file.data, 'logos')
            admin.logo_url = logo_url
        
        form.populate_obj(admin)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.admin_dashboard'))
    return render_template('edit_profile.html', form=form, vendor=admin)

@main.route("/edit_profile", methods=['GET', 'POST'])
@vendor_only
def edit_profile():
    vendor = db.session.get(Vendor, session.get('vendor_id'))
    if not vendor:
        flash('Vendor not found.', 'danger')
        return redirect(url_for('main.login'))
        
    form = UpdateProfileForm(obj=vendor)
    if form.validate_on_submit():
        # New upload logic
        if form.logo_file.data:
            logo_url = upload_to_cloudinary(form.logo_file.data, 'logos')
            vendor.logo_url = logo_url
        
        form.populate_obj(vendor)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        if vendor.is_admin:
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.vendor_dashboard'))

    return render_template('edit_profile.html', form=form, vendor=vendor)

# Admin ad routes
@main.route("/admin/add_ad", methods=['GET', 'POST'])
@admin_only
def add_ad():
    form = AdForm()
    if form.validate_on_submit():
        media_url = None
        media_type = 'image'
        if form.media_file.data:
            media_url = upload_to_cloudinary(form.media_file.data, 'ads')
            # Assuming file extension check for media type
            if media_url and (media_url.lower().endswith('.mp4')):
                media_type = 'video'
            else:
                media_type = 'image'
        
        ad = Ad(
            title=form.title.data,
            content=form.content.data,
            media_url=media_url,
            media_type=media_type,
            link_url=form.link_url.data,
            is_active=form.is_active.data
        )
        db.session.add(ad)
        db.session.commit()
        flash('Ad created successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))
    return render_template('admin_add_ad.html', form=form)

@main.route("/admin/edit_ad/<int:ad_id>", methods=['GET', 'POST'])
@admin_only
def edit_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if not ad:
        flash('Ad not found.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    
    form = AdForm(obj=ad)
    if form.validate_on_submit():
        if form.media_file.data:
            media_url = upload_to_cloudinary(form.media_file.data, 'ads')
            ad.media_url = media_url
            if media_url and (media_url.lower().endswith('.mp4')):
                media_type = 'video'
            else:
                media_type = 'image'
        
        form.populate_obj(ad)
        db.session.commit()
        flash('Ad updated successfully!', 'success')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('admin_edit_ad.html', form=form, ad=ad)

@main.route("/admin/delete_ad/<int:ad_id>", methods=['POST'])
@admin_only
def delete_ad(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad:
        db.session.delete(ad)
        db.session.commit()
        flash('Ad deleted successfully!', 'success')
    else:
        flash('Ad not found.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/toggle_ad_status/<int:ad_id>", methods=['POST'])
@admin_only
def toggle_ad_status(ad_id):
    ad = db.session.get(Ad, ad_id)
    if ad:
        ad.is_active = not ad.is_active
        db.session.commit()
        flash('Ad status updated successfully!', 'success')
    else:
        flash('Ad not found.', 'danger')
    return redirect(url_for('main.admin_dashboard'))'