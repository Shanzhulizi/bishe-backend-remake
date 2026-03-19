from app.repositories.message_repo import MessageRepository


class MessageService:
    def __init__(self, db):
        self.db = db
        self.message_repo = MessageRepository(db)
    def get_history_messages_count(self, conv_id):
        total = self.message_repo.get_message_count(conv_id)


        return total
    def get_history_messages(self, conv_id, param):
        messages = self.message_repo.get_messages_page(conv_id, param)

        return messages


