from flask import Blueprint, render_template, request
from flask_blog.models import chatHistory
from flask_blog import socketio, db
from flask_socketio import send, join_room, leave_room
from flask_login import login_required, current_user
import json


chatroom = Blueprint('chatroom', __name__)

@socketio.on('connected')
def connected():
    print(f'{request.namespace.socket.sessid} connected')
    clients.append(request.name)

@chatroom.route('/chatroom', methods=['POST', 'GET'])
@login_required
def chatroom_homepage():
    messages = chatHistory.query.all()
    return render_template('chatroom.html', messages=messages)

@socketio.on('message')
def handleMessage(msg):
    print('Message: '+ msg)

    message = chatHistory(message=msg, talker=current_user)
    db.session.add(message)
    db.session.commit()

    d = {'message':message.message, 'talker':message.talker.username, 'time':message.time_stamp.strftime(r'%Y-%m-%d %H:%M')}
    d = json.dumps(d)
    send(d, broadcast=True)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)