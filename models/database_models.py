"""Database models using SQLAlchemy."""

from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Float, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Any

Base: Any = declarative_base()


class ChatbotSession(Base):
    """챗봇 세션 테이블"""
    __tablename__ = 'ChatbotSession'

    chatbotSessionId = Column(String(50), primary_key=True)
    startedAt = Column(DateTime, nullable=False, default=func.now())
    endedAt = Column(DateTime)  # 세션에 대한 모든 작업의 최종 작업.
    isReported = Column(Boolean, default=None, nullable=True)  # None: 미결정, True: 처리완료 (다운로드든 스킵이든)
    issue = Column(String(100), ForeignKey('ChatbotIssue.issue'), nullable=True)  # FK to ChatbotIssue
    isTerminated = Column(Boolean, default=False)
    userId = Column(String(50))
    
    # 관계 설정
    chatbot_issue = relationship("ChatbotIssue", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    # 그냥 계속 저장은 해두되, isTerminated가 True인 것들은 아예 외부에서 접근 금지하도록 하는 걸로..


class ChatMessage(Base):
    """대화 내역 테이블"""
    __tablename__ = 'ChatMessage'

    chatMessageId = Column(String(50), primary_key=True)
    chatMessage = Column(Text, nullable=False)
    chatbotSessionId = Column(String(50), ForeignKey('ChatbotSession.chatbotSessionId'), nullable=False)  # FK to ChatbotSession
    issue = Column(String(100), ForeignKey('ChatbotIssue.issue'), nullable=True)  # FK to ChatbotIssue (학습 데이터용)
    sender = Column(Enum('bot', 'user', name='sender_enum'), nullable=False)  # type: ignore
    sentAt = Column(DateTime, nullable=False, default=func.now())
    
    # 관계 설정
    session = relationship("ChatbotSession", back_populates="messages")
    chatbot_issue = relationship("ChatbotIssue", back_populates="messages")
    # 여기에 issue 코드가 있어야, 차후에 쓰지 않을까? -> 이래야 챗봇 이슈와 연결될 수 있음
    # (차후 학습 데이터로 사용하려면, 어디에서든지 issue 코드를 기반으로 찾아오도록)


class ChatbotIssue(Base):
    """챗봇 이슈 테이블"""
    __tablename__ = 'ChatbotIssue'

    issue = Column(String(100), primary_key=True)
    processType = Column(Enum('장애접수', '정기점검', name='process_type_enum'), nullable=False)  # type: ignore
    modeType = Column(Enum('프레스', '용접기', '도장설비', '차량조립설비', name='mode_type_enum'), nullable=False)  # type: ignore
    modeLogId = Column(String(50))
    createdAt = Column(DateTime, nullable=False, default=func.now())  # 이슈 생성 시간
    updatedAt = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # 이슈 업데이트 시간
    description = Column(Text, nullable=True)  # 문제 설명
    
    # 관계 설정
    sessions = relationship("ChatbotSession", back_populates="chatbot_issue", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="chatbot_issue")
    # 여기에는 어떤 문제가 있었는지 기억하고자 저장은 해둘 듯..? 아닌가?

