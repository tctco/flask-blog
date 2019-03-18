from flask_blog import create_app, db, socketio


app = create_app()
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)
    # app.run(debug = True)

