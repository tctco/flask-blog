from flask import Blueprint, render_template, request
from flask_blog.models import chatHistory, User, chatRoom
from flask_blog import socketio, db
from flask_socketio import send, emit, join_room, leave_room
from flask_login import login_required, current_user
import json
import inspect#adding info
from datetime import datetime

chatroom = Blueprint('chatroom', __name__)


@chatroom.route('/chatroom', methods=['POST', 'GET'])
@login_required
def chatroom_homepage():
    return render_template('chatroom.html')
    

@chatroom.route('/chatroom/history/<string:room_name>')
@login_required
def chatroom_history(room_name):
    chatroom = chatRoom.query.filter_by(room_name=room_name).first()
    messages = chatroom.chatroom_history
    return render_template('history_page.html', room_name=room_name, messages=messages)


socketio.room_users = {}#room:users
socketio.reqid_info = {}#sid{room, talker}
socketio.user_sid = {}#username:sid


@socketio.on('connect')
def connect_event_handler():
    @socketio.on('join')
    def talker_join_handler(data):
        talker = current_user.username
        room = data['room']
        print(room)
        
        chatroom = chatRoom.query.filter_by(room_name=room).first()
        if chatroom is None:
            chatroom = chatRoom(room_name=room)
            db.session.add(chatroom)
            db.session.commit()
        try:
            original_room = socketio.reqid_info[request.sid]['room']
            if room != original_room:
                socketio.room_users[room].remove(talker)
                leave_room(original_room)
        except:
            pass

        susr = f'{talker}--{request.sid}'
        
        #add talker into talker list
        socketio.room_users.setdefault(room, [])
        if talker not in socketio.room_users[room]:
            socketio.room_users[room].append(talker)

        # socketio.room_users.setdefault(room, []).append(susr)#append room if there isn't a room
        socketio.reqid_info.setdefault(request.sid, {}).update({
            'room': room,
            'talker': talker,
        })
        join_room(room)
        current_user.join(chatroom)
        db.session.commit()

        
        message = f'#=>{datetime.now()}:{susr} action:{inspect.stack()[0][-4:-2]} room:{room}'
        print(message)
        talkers = []
        for item_users in socketio.room_users.values():
            if item_users not in talkers:
                talkers.extend(item_users)
        print('#=>current users: ', talkers)
        socketio.emit('sys broadcast', {'message':message})
    
    
    @socketio.on('disconnect')
    def disconnect_handler():
        talker = current_user.username
        room = socketio.reqid_info[request.sid]['room']
        susr = f'{talker}--{request.sid}'
        try:
            socketio.room_users[room].remove(talker)
        except:
            pass
        message = f'#=>{datetime.now()}:{susr} action:{inspect.stack()[0][-4:-2]} room:{room}'
        print(message)
        socketio.emit('sys broadcast', {'message':message})
        leave_room(room)


    @socketio.on('message')
    def message_handler(msg): 

        room = socketio.reqid_info[request.sid]['room']   
        chatroom = chatRoom.query.filter_by(room_name=room).first()

        print('Message: '+ msg)

        message = chatHistory(message=msg, talker=current_user, chatroom_belonged=chatroom)
        db.session.add(message)
        db.session.commit()

        d = {'message_type': 'message', 'message':message.message, 'talker':message.talker.username, 'time':message.time_stamp.strftime(r'%Y-%m-%d %H:%M')}
        d = json.dumps(d)

        send(d, broadcast=True, room=room)


    @socketio.on('get room talkers')
    def online_talkers_handler(room_name):
        chatroom = chatRoom.query.filter_by(room_name=room_name).first()
        talkers = []
        for talker in chatroom.talkers_joined:
            talkers.append(talker.username)
        message = str(socketio.room_users[room_name]) + str(talkers)
        print('users in room: ', message)
        emit('sys broadcast', {'message': 'sys: '+ message})


    @socketio.on('private message', namespace='/private')
    def private_message_handler(payload):
        friend_name = payload['friend_name']
        friend = User.query.filter_by(username=friend_name).first()
        if current_user.is_friend(friend):
            message = payload['private_message']
            if socketio.user_sid[friend_name]:
                firend_sid = socketio.user_sid[friend_name]
                emit('new private message', message, room=firend_sid)
            else:
                pass
        else:
            emit('sys broadcast', {'message': 'sys: '+ f'{friend_name} is still not your friend!'})

        
