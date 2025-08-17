from flask_socketio import emit, join_room
from app import socketio

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    # You can send a system message here, like "User joined the room"
    emit('status', {'msg': 'A user has entered the room.'}, room=room)

@socketio.on('message')
def on_message(data):
    sender = data.get('sender_id')
    room = data.get('room')
    msg = data.get('msg')
    
    # You would typically save this message to the database here

    # Send the message to everyone in the room
    emit('message', {'sender': sender, 'msg': msg}, room=room)