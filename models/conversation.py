import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class Conversation(Base):
    """
    Represents a chat conversation between the user and the AI agent.
    """
    __tablename__ = "conversation"

    # Unique ID for the conversation (UUID as string is good for mobile sync)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sync_id = Column(String, nullable=True)
    title = Column(String, nullable=True, default="New Chat")
    user_sync_token = Column(String, ForeignKey("user_profile.sync_token", ondelete="CASCADE"), nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user_profile = relationship("UserProfile", backref="conversations")

    # Relationship to fetch all messages for this conversation easily
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")


class ConversationMessage(Base):
    """
    Tracks individual messages within a conversation, including tool calls and results.
    """
    __tablename__ = "conversation_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_id = Column(String, nullable=True)
    conversation_id = Column(String, ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
    
    # The role of the entity that sent this message: 'user', 'model', or 'tool' / 'function'
    role = Column(String, nullable=False)
    
    # Standard text content from the user or the AI model
    content = Column(Text, nullable=True)
    
    # To track when the model decides to call functions
    # E.g., [{"name": "get_workouts", "args": {"dateFrom": "..."}}]
    tool_calls = Column(JSON, nullable=True)
    
    # To track the results returned from the mobile client after executing the tool calls
    # E.g., [{"name": "get_workouts", "response": {...}}]
    tool_results = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
