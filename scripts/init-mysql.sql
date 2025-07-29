-- ==========================================
-- Smart Factory MySQL 데이터베이스 초기화 스크립트
-- ==========================================

-- 데이터베이스 생성 (존재하지 않을 경우)
CREATE DATABASE IF NOT EXISTS chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE chatbot_db;

-- 챗봇 세션 테이블
CREATE TABLE IF NOT EXISTS ChatbotSession (
    chatbotSessionId VARCHAR(50) PRIMARY KEY,
    startedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endedAt DATETIME NULL,
    isReported BOOLEAN DEFAULT FALSE,
    issue VARCHAR(100) NULL,
    isTerminated BOOLEAN DEFAULT FALSE,
    userId VARCHAR(50) NULL,
    INDEX idx_user_id (userId),
    INDEX idx_started_at (startedAt),
    INDEX idx_issue (issue)
);

-- 대화 내역 테이블
CREATE TABLE IF NOT EXISTS ChatMessage (
    chatMessageId VARCHAR(50) PRIMARY KEY,
    chatMessage TEXT NOT NULL,
    chatbotSessionId VARCHAR(50) NOT NULL,
    sender ENUM('bot', 'user') NOT NULL,
    sentAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (chatbotSessionId),
    INDEX idx_sent_at (sentAt),
    FOREIGN KEY (chatbotSessionId) REFERENCES ChatbotSession(chatbotSessionId) ON DELETE CASCADE
);

-- 챗봇 이슈 테이블
CREATE TABLE IF NOT EXISTS ChatbotIssue (
    issue VARCHAR(100) PRIMARY KEY,
    processType ENUM('장애접수', '정기점검') NOT NULL,
    modeType ENUM('프레스', '용접기', '도장설비', '차량조립설비') NOT NULL,
    modeLogId VARCHAR(50) NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_process_type (processType),
    INDEX idx_mode_type (modeType)
);

-- 프레스 결함 감지 로그 테이블
CREATE TABLE IF NOT EXISTS PressDefectDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    machineName VARCHAR(100) NULL,
    itemNo VARCHAR(50) NULL,
    pressTime FLOAT NULL,
    pressure1 FLOAT NULL,
    pressure2 FLOAT NULL,
    pressure3 FLOAT NULL,
    detectCluster BIGINT NULL,
    detectType VARCHAR(50) NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue),
    INDEX idx_is_solved (isSolved)
);

-- 프레스 고장 감지 로그 테이블
CREATE TABLE IF NOT EXISTS PressFaultDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    a0Vibration FLOAT NULL,
    a1Vibration FLOAT NULL,
    a2Current FLOAT NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue)
);

-- 용접기 결함 감지 로그 테이블
CREATE TABLE IF NOT EXISTS WeldingMachineDefectDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    sensorValue0_5ms FLOAT NULL,
    sensorValue1_2ms FLOAT NULL,
    sensorValue1_9ms FLOAT NULL,
    sensorValue2_6ms FLOAT NULL,
    sensorValue3_3ms FLOAT NULL,
    sensorValue4_0ms FLOAT NULL,
    sensorValue4_7ms FLOAT NULL,
    sensorValue5_4ms FLOAT NULL,
    sensorValue6_1ms FLOAT NULL,
    sensorValue6_8ms FLOAT NULL,
    sensorValue7_5ms FLOAT NULL,
    sensorValue8_2ms FLOAT NULL,
    sensorValue8_9ms FLOAT NULL,
    sensorValue9_6ms FLOAT NULL,
    sensorValue10_3ms FLOAT NULL,
    sensorValue11_0ms FLOAT NULL,
    sensorValue11_7ms FLOAT NULL,
    sensorValue12_4ms FLOAT NULL,
    sensorValue13_1ms FLOAT NULL,
    sensorValue13_8ms FLOAT NULL,
    sensorValue14_5ms FLOAT NULL,
    sensorValue15_2ms FLOAT NULL,
    sensorValue15_9ms FLOAT NULL,
    sensorValue16_6ms FLOAT NULL,
    sensorValue17_3ms FLOAT NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue)
);

-- 도장 표면 결함 감지 로그 테이블
CREATE TABLE IF NOT EXISTS PaintingSurfaceDefectDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    imageUrl VARCHAR(255) NULL,
    label VARCHAR(100) NULL,
    type VARCHAR(50) NULL,
    x FLOAT NULL,
    y FLOAT NULL,
    width FLOAT NULL,
    height FLOAT NULL,
    points VARCHAR(500) NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue)
);

-- 도장 공정 장비 결함 감지 로그 테이블
CREATE TABLE IF NOT EXISTS PaintingProcessEquipmentDefectDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    thick FLOAT NULL,
    voltage FLOAT NULL,
    ampere FLOAT NULL,
    temper FLOAT NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue)
);

-- 차량 조립 공정 결함 감지 로그 테이블
CREATE TABLE IF NOT EXISTS VehicleAssemblyProcessDefectDetectionLog (
    id VARCHAR(50) PRIMARY KEY,
    machineId BIGINT NOT NULL,
    timeStamp DATETIME NOT NULL,
    part VARCHAR(100) NULL,
    work VARCHAR(100) NULL,
    category VARCHAR(100) NULL,
    imageUrl VARCHAR(255) NULL,
    imageName VARCHAR(100) NULL,
    imageWidth BIGINT NULL,
    imageHeight BIGINT NULL,
    issue VARCHAR(100) NULL,
    isSolved BOOLEAN DEFAULT FALSE,
    INDEX idx_machine_id (machineId),
    INDEX idx_timestamp (timeStamp),
    INDEX idx_issue (issue),
    INDEX idx_part (part),
    INDEX idx_category (category)
);

-- 초기 데이터 삽입
INSERT IGNORE INTO ChatbotIssue (issue, processType, modeType) VALUES
('프레스_압력_이상', '장애접수', '프레스'),
('프레스_진동_이상', '장애접수', '프레스'),
('용접_불량', '장애접수', '용접기'),
('도장_표면_결함', '장애접수', '도장설비'),
('조립_불량', '장애접수', '차량조립설비'),
('정기점검_프레스', '정기점검', '프레스'),
('정기점검_용접기', '정기점검', '용접기'),
('정기점검_도장설비', '정기점검', '도장설비'),
('정기점검_조립설비', '정기점검', '차량조립설비');

-- 권한 설정
GRANT ALL PRIVILEGES ON chatbot_db.* TO 'chatbot_user'@'%';
FLUSH PRIVILEGES;

-- 초기화 완료 메시지
SELECT 'Smart Factory 데이터베이스 초기화 완료' AS status;