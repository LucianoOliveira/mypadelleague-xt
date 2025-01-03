from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Players
from werkzeug.security import generate_password_hash, check_password_hash
# from . import db, emailS
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import os
# from flask_mail import Mail, Message
# from itsdangerous import URLSafeTimedSerializer, SignatureExpired


auth =  Blueprint('auth', __name__)
# s = URLSafeTimedSerializer('Thisisasecret123!')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = Players.query.filter_by(pl_email=email).first()
        if user:
            print("User found")
            if check_password_hash(user.pl_pwd, password):
                # flash('Logged in successfully!', category='success')
                print("Logged in successfully!")
                login_user(user, remember=True)
                return redirect(url_for('views.managementLeague'))
            else:
                flash('Incorrect password, try again.', category='error')
                print("Incorrect password, try again.")
        else:
            print("User Not found")

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # TODO - FIX THE SIGN UP PAGE
    if request.method == 'POST':
        email = request.form.get('email')
        # first_name = request.form.get('first_name')
        # mobileNumber = request.form.get('mobileNumber')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = Players.query.filter_by(pl_email=email).first()
        if user:
            if len(email) < 4:
                flash('Email must be greater than 4 characters.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 7:
                flash('Password must be greater than 6 characters.', category='error')
            else:
                user.pl_pwd = generate_password_hash(password1, method='sha256')
                db.session.commit()
                login_user(user, remember=True)
                # flash('User created successfully!', category='success')
                return redirect(url_for('views.home'))
        else:    
            flash('Cannot create new user yet!', category='error')   
            if len(email) < 4:
                flash('Email must be greater than 4 characters.', category='error')
            # elif len(first_name) < 2:
            #     flash('Name must be greater than 1 character.', category='error')
            # elif len(mobileNumber) < 2:
            #     flash('Mobile number must be greater than 9 characters.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 7:
                flash('Password must be greater than 6 characters.', category='error')
            else:
                # token = s.dumps(email, salt='email-confirm')
                # link = url_for('auth.confirm_email', token=token, _external=True)
                #new_user = User(email=email, first_name=first_name, mobileNumber=mobileNumber, password=generate_password_hash(password1, method='sha256'), ustatus='A')
                user_type = 'User'
                # new_user = Players(email=email, first_name=first_name, mobileNumber=mobileNumber, password=generate_password_hash(password1, method='sha256'), ustatus='V', user_type=user_type)
                # db.session.add(new_user)
                # db.session.commit()
                # Send confirmation email
                # msg = Message('Confirm Email', sender='luciano8.oliveira@gmail.com', recipients=[email])
                # msg.body = 'Welcome to NetSports. To activate your account go to this link {}'.format(link)
                # emailS.send(msg)
                # flash('User created successfully, check Email for verification!', category='success')
                # login_user(new_user, remember=True)
                # flash('User created successfully!', category='success')
                return redirect(url_for('views.home'))
        
    return render_template("sign_up.html", user=current_user)