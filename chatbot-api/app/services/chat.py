import json

from app.repositories.conversations import ConversationRepository
from app.services.audit import record


def sse(event):
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


class ChatService:
    def __init__(self, db, provider):
        self.db, self.provider = db, provider
        self.conversations = ConversationRepository(db)

    def prepare(self, context, body):
        # Validate ownership before invoking a future provider (which may have cost).
        if body.conversation_id:
            detail = self.conversations.detail(str(body.conversation_id), context)
            if detail["mode"] != body.mode:
                from fastapi import HTTPException

                raise HTTPException(409, "Hội thoại thuộc chủ đề khác.")
        answer = self.provider.answer(context.department, body.mode, body.message)
        cid = self.conversations.append(context, body, answer)
        record(self.db, "chat_turn", context.user.id, context.department, cid)
        return {
            "type": "done",
            "response": answer,
            "conversation_id": cid,
            "user_message": body.message,
            "resolved_mode": body.mode,
            "citations": [],
            "contact_info": None,
            "interactive": None,
            "provider": "stub",
        }

    @staticmethod
    def stream(result):
        # Stub answer is committed before delivery; disconnect never creates partial turns.
        answer = result["response"]
        for index in range(0, len(answer), 24):
            yield sse({"type": "token", "text": answer[index : index + 24]})
        yield sse(result)
