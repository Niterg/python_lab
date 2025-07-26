from sqladmin import Admin, ModelView
from app.models import Message, Room
from app.dependencies import engine

class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.content, Message.timestamp]
    can_export = True

class RoomAdmin(ModelView, model=Room):
    column_list = [Room.id, Room.name, Room.created_at]

def setup_admin(app):
    admin = Admin(app, engine)
    admin.add_view(MessageAdmin)
    admin.add_view(RoomAdmin)