from sqlalchemy import Column,Integer,String,ForeignKey,DateTime,Text,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime,timezone
from app.database import Base
from app.schemas import FriendshipStatus
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP

class Friendship(Base):
    __tablename__ = "friendships"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLAlchemyEnum(FriendshipStatus), default=FriendshipStatus.pending, nullable=False)  # pending, accepted, declined
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", foreign_keys=[sender_id], back_populates="friendships_as_user")
    friend = relationship("User", foreign_keys=[receiver_id], back_populates="friendships_as_friend")

    def __repr__(self):
        return f"<Friendship(id={self.id}, user_id={self.sender_id}, friend_id={self.receiver_id}, status={self.status})>"
    



class User(Base):
    __tablename__="users"


    id=Column(Integer,primary_key=True,index=True)
    username=Column(String,unique=True,index=True,nullable=False)#20 charcter limit for username
    email=Column(String,unique=True,index=True,nullable=False)
    hashed_password=Column(String)
    #is_active=Column(Boolean,default=True)
    is_online=Column(Boolean,default=False)
    created_at=created_at = Column(
    TIMESTAMP(timezone=True),
    server_default=func.now(),
    nullable=False
)# will add last seen and login

    #relationships
    messages = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="[Message.receiver_id]", back_populates="receiver")

    friendships_as_user = relationship("Friendship", foreign_keys=[Friendship.sender_id], back_populates="user", cascade="all, delete-orphan")
    friendships_as_friend = relationship("Friendship", foreign_keys=[Friendship.receiver_id], back_populates="friend", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="[Message.receiver_id]", back_populates="receiver")


    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"



class Message(Base):
    __tablename__="messages"
    #will add media files afte sometime
    id=Column(Integer,primary_key=True,index=True)
    sender_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content=Column(Text,nullable=False)
    timestamp: datetime=Column(DateTime(timezone=True),default=datetime.now(timezone.utc))

    #relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender_id}, content={self.content[:20]})>"




