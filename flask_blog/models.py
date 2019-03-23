from datetime import datetime
from flask_blog import db, login_manager
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
import random


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#auxiliary table follower and followed
followers = db.Table('followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
    )

#auxiliary table chatRoom and User
joins = db.Table('joins',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('chatroom_id', db.Integer, db.ForeignKey('chat_room.id'))
    )


class chatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column('room_name', db.String(60), unique=True, nullable=False)
    chatroom_history = db.relationship('chatHistory', backref="chatroom_belonged")




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    image_file = db.Column(db.String(20), nullable = False, default = f'default{random.randint(0,9)}.png')
    password = db.Column(db.String(60), nullable = False)
    posts = db.relationship('Post', backref = "author", lazy = True)
    messages = db.relationship('chatHistory', backref="talker", lazy=True)
    
    followed = db.relationship('User', secondary=followers,
        primaryjoin=(followers.c.follower_id==id),
        secondaryjoin=(followers.c.followed_id==id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
        )


    chatroom_joined = db.relationship('chatRoom', secondary=joins, backref=db.backref('talkers_joined', lazy='dynamic'), lazy='dynamic')


    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)


    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)


    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id==user.id).count() > 0


    def is_friend(self, user):
        if user.is_following(self) and self.is_following(user):
            return True
        else:
            return False


    def is_joining(self, chatroom):
        return self.chatroom_joined.filter(joins.c.chatroom_id==chatroom.id).count() > 0

    
    def join(self, chatroom):
        if not self.is_joining(chatroom):
            self.chatroom_joined.append(chatroom)


    def leave(self, chatroom):
        if self.is_joining(chatroom):
            self.chatroom_joined.remove(chatroom)

    #entry of followed
    def followed_posts(self):
        followed = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.date_posted.desc())


    def __repr__(self):
        return f'User("{self.username}", "{self.email}", "{self.image_file}")'

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)



class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable = False)
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    content = db.Column(db.Text, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f'Post("{self.title}", "{self.date_posted}")'



class chatHistory(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    message = db.Column('message', db.String(500))
    time_stamp = db.Column('time_stamp', db.DateTime, default=datetime.utcnow)
    # room_name = db.Column('room_name', db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    chatroom_belonged_id = db.Column(db.Integer, db.ForeignKey("chat_room.id"))






class Notification(db.Model):
    id = db.Column('id', db.Integer, nullable=False, primary_key=True)
    content = db.Column('content', db.String(500))
    time_stamp = db.Column('time_stamp', db.DateTime, default=datetime.utcnow)
    sender_name = db.Column('sender_name', db.String(20), default="system")
    receiver_name = db.Column('receiver_name', db.String(20), nullable=False)