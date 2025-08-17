# app/models.py
from datetime import datetime
from app import db, bcrypt
from flask_login import UserMixin
import os
import secrets

class Vendor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), unique=True, nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    whatsapp_number = db.Column(db.String(20), unique=True, nullable=False)
    location_zone = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    logo_url = db.Column(db.String(200), nullable=False, default='logos/default.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    referral_code = db.Column(db.String(10), unique=True, nullable=False)
    referred_by = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    
    snacks = db.relationship('Snack', backref='vendor', lazy=True, cascade="all, delete-orphan")
    referrals = db.relationship('Vendor', backref=db.backref('referrer', remote_side=[id]), lazy=True)

    def __init__(self, **kwargs):
        super(Vendor, self).__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = secrets.token_hex(5).upper()

    def __repr__(self):
        return f"Vendor('{self.business_name}', '{self.email}', 'Admin: {self.is_admin}')"
    
    @staticmethod
    def create_admin():
        """Creates or updates a default admin user."""
        with db.session.no_autoflush:
            admin_vendor = Vendor.query.filter_by(email='admin@arewabites.com').first()
            if not admin_vendor:
                hashed_password = bcrypt.generate_password_hash('adminpass').decode('utf-8')
                admin = Vendor(
                    business_name='Arewa Bites Admin',
                    contact_name='Admin User',
                    whatsapp_number='2348000000000',
                    location_zone='Headquarters',
                    state='Lagos',
                    email='admin@arewabites.com',
                    password=hashed_password,
                    is_admin=True,
                    is_verified=True,
                    logo_url='logos/admin_logo.png'
                )
                db.session.add(admin)
                print("Default admin user created successfully.")
            else:
                # Ensure the admin's password is correct if the user already exists
                admin_vendor.password = bcrypt.generate_password_hash('adminpass').decode('utf-8')
                admin_vendor.is_admin = True
                print("Admin user already exists. Password has been reset.")
            db.session.commit()

class Snack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    media_url = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    reviews = db.relationship('Review', backref='snack', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Snack('{self.name}', '{self.date_posted}')"
        
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    snack_id = db.Column(db.Integer, db.ForeignKey('snack.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Review('{self.rating}', '{self.date_posted}')"
        
class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(10), nullable=True)
    link_url = db.Column(db.String(255), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"Ad('{self.title}', '{self.date_posted}')"