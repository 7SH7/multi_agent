"""Database models using SQLAlchemy."""

from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Float, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class ChatbotSession(Base):
    """챗봇 세션 테이블"""
    __tablename__ = 'ChatbotSession'

    chatbotSessionId = Column(String(50), primary_key=True)
    startedAt = Column(DateTime, nullable=False, default=func.now())
    endedAt = Column(DateTime)
    isReported = Column(Boolean, default=False)
    issue = Column(String(100))
    isTerminated = Column(Boolean, default=False)
    userId = Column(String(50))


class ChatMessage(Base):
    """대화 내역 테이블"""
    __tablename__ = 'ChatMessage'

    chatMessageId = Column(String(50), primary_key=True)
    chatMessage = Column(Text, nullable=False)
    chatbotSessionId = Column(String(50))
    sender = Column(Enum('bot', 'user', name='sender_enum'), nullable=False)
    sentAt = Column(DateTime, nullable=False, default=func.now())


class ChatbotIssue(Base):
    """챗봇 이슈 테이블"""
    __tablename__ = 'ChatbotIssue'

    issue = Column(String(100), primary_key=True)
    processType = Column(Enum('장애접수', '정기점검', name='process_type_enum'), nullable=False)
    modeType = Column(Enum('프레스', '용접기', '도장설비', '차량조립설비', name='mode_type_enum'), nullable=False)
    modeLogId = Column(String(50))


class PressDefectDetectionLog(Base):
    """프레스 결함 감지 로그"""
    __tablename__ = 'PressDefectDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    machineName = Column(String(100))
    itemNo = Column(String(50))
    pressTime = Column(Float)
    pressure1 = Column(Float)
    pressure2 = Column(Float)
    pressure3 = Column(Float)
    detectCluster = Column(BigInteger)
    detectType = Column(String(50))
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)


class PressFaultDetectionLog(Base):
    """프레스 고장 감지 로그"""
    __tablename__ = 'PressFaultDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    a0Vibration = Column(Float)
    a1Vibration = Column(Float)
    a2Current = Column(Float)
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)


class WeldingMachineDefectDetectionLog(Base):
    """용접기 결함 감지 로그"""
    __tablename__ = 'WeldingMachineDefectDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    sensorValue0_5ms = Column(Float)
    sensorValue1_2ms = Column(Float)
    sensorValue1_9ms = Column(Float)
    sensorValue2_6ms = Column(Float)
    sensorValue3_3ms = Column(Float)
    sensorValue4_0ms = Column(Float)
    sensorValue4_7ms = Column(Float)
    sensorValue5_4ms = Column(Float)
    sensorValue6_1ms = Column(Float)
    sensorValue6_8ms = Column(Float)
    sensorValue7_5ms = Column(Float)
    sensorValue8_2ms = Column(Float)
    sensorValue8_9ms = Column(Float)
    sensorValue9_6ms = Column(Float)
    sensorValue10_3ms = Column(Float)
    sensorValue11_0ms = Column(Float)
    sensorValue11_7ms = Column(Float)
    sensorValue12_4ms = Column(Float)
    sensorValue13_1ms = Column(Float)
    sensorValue13_8ms = Column(Float)
    sensorValue14_5ms = Column(Float)
    sensorValue15_2ms = Column(Float)
    sensorValue15_9ms = Column(Float)
    sensorValue16_6ms = Column(Float)
    sensorValue17_3ms = Column(Float)
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)


class PaintingSurfaceDefectDetectionLog(Base):
    """도장 표면 결함 감지 로그"""
    __tablename__ = 'PaintingSurfaceDefectDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    imageUrl = Column(String(255))
    label = Column(String(100))
    type = Column(String(50))
    x = Column(Float)
    y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    points = Column(String(500))
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)


class PaintingProcessEquipmentDefectDetectionLog(Base):
    """도장 공정 장비 결함 감지 로그"""
    __tablename__ = 'PaintingProcessEquipmentDefectDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    thick = Column(Float)
    voltage = Column(Float)
    ampere = Column(Float)
    temper = Column(Float)
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)


class VehicleAssemblyProcessDefectDetectionLog(Base):
    """차량 조립 공정 결함 감지 로그"""
    __tablename__ = 'VehicleAssemblyProcessDefectDetectionLog'

    id = Column(String(50), primary_key=True)
    machineId = Column(BigInteger)
    timeStamp = Column(DateTime)
    part = Column(String(100))
    work = Column(String(100))
    category = Column(String(100))
    imageUrl = Column(String(255))
    imageName = Column(String(100))
    imageWidth = Column(BigInteger)
    imageHeight = Column(BigInteger)
    issue = Column(String(100))
    isSolved = Column(Boolean, default=False)