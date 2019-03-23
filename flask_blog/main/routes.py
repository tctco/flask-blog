from flask import render_template, request, Blueprint
from flask_blog.models import Post
from flask_login import login_required, current_user


main = Blueprint('main', __name__)


@main.route("/home")
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@main.route("/")
@main.route('/everyone')
def home_everyone():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)



@main.route("/about")
def about():
    return render_template('about.html', title='About')
