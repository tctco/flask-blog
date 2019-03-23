from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from flask_blog import db, bcrypt
from flask_blog.models import User, Post, Notification
from flask_blog.users.forms import RegistrationForm, LoginForm, UpdateAccountField, RequestResetForm, ResetPasswordForm
from flask_blog.users.utils import save_picture, send_reset_email, delete_picture


users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash(
            f'You have already logged in! Welcome back user: {current_user.username} XD!', 'info')
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    password=hashed_password, email=form.email.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Your account has been created! You are now able to log in.", 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        flash(
            f'You have already logged in! Welcome back user: {current_user.username} XD!', 'info')
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash(f"Login Unsuccessful! Please check email or password!", 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    flash(f'Successfully logged out! See ya!', 'primary')
    return redirect(url_for('main.home'))

@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountField()
    if form.validate_on_submit():

        if form.picture.data:
            original_picture = current_user.image_file
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
            delete_picture(original_picture)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=['POST', 'GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title="Reset Password", form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid token!', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You can login with your new password!', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route("/user/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} does not exist!', 'warning')
        return redirect(url_for('main.home'))
    if user == current_user:
        flash('You cannot follow yourself!', 'warning')
        return redirect(url_for('users.account'))
    else:
        current_user.follow(user)
        flash(f'You are now following {username}!', 'info')
        friend_invitation = Notification(sender_name=current_user.username, receiver_name=username, 
            content=f"User {current_user.username} has followed you! Follow him/her so that you can chat and share posts with him/her!")
        db.session.add(friend_invitation)
        db.session.commit()
        return redirect(url_for('users.user_posts', username=username))


@users.route("/user/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} does not exist!', 'warning')
        return redirect(url_for('main.home'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('account'))
    else:
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}!', 'info')
        friend_denial = Notification(sender_name=current_user.username, receiver_name=username,
            content=f"User {current_user.username} has unfollowed you. You can no longer chat with him. You can also choose to unfollow him/her.")
        db.session.commit()
        return redirect(url_for('users.user_posts', username=username))


@users.route("/user/notifications")
@login_required
def notifications():
    notifications = Notification.query.filter_by(receiver_name=current_user.username).all()
    return render_template('notifications.html', notifications=notifications)