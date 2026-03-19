from app.repositories.conversation_repo import ConversationRepository


class ConversationService:
    def __init__(self, db):
        self.db = db
        self.conv_repo = ConversationRepository(db)
    def get_conv(self, id, character_id):
        conv= self.conv_repo .get_active(id, character_id)
        return conv







