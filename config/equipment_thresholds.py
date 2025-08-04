# config/equipment_thresholds.py
"""EDA 팀 박스분석 기반 장비별 기준값 및 번역 정보"""

EQUIPMENT_THRESHOLDS = {
    "PRESS": {
        "PRESSURE": {
            "Q1": 75,
            "Q2": 85,  # 중위수 추가
            "Q3": 95,
            "NORMAL_RANGE": (75, 95),
            "WARNING_RANGE": (65, 105),
            "CRITICAL_MAX": 125,
            "UNIT": "bar"
        },
        "VIBRATION": {
            "Q1": 3.2,
            "Q2": 5.8,
            "Q3": 8.5,
            "NORMAL_RANGE": (3.2, 8.5),
            "WARNING_MAX": 12.0,
            "CRITICAL_MAX": 15.0,
            "UNIT": "mm/s"
        },
        "CURRENT": {
            "Q1": 4.8,
            "Q2": 5.5,
            "Q3": 6.2,
            "NORMAL_RANGE": (4.8, 6.2),
            "WARNING_MAX": 8.0,
            "CRITICAL_MAX": 10.0,
            "UNIT": "A"
        },
        "AI0_VIBRATION": {
            "Q1": 0.020397,
            "Q2": 0.025,
            "Q3": 0.030,
            "NORMAL_RANGE": (0.010, 0.030),
            "WARNING_MAX": 0.050,
            "CRITICAL_MAX": 0.070,
            "UNIT": "g",
            "DESCRIPTION": "프레스 상부진동 센서 (VIB1 이상 진단용)"
        }
    },

    "WELD": {
        "SENSOR_VALUE": {
            "Q1": 8.5,
            "Q2": 10.4,
            "Q3": 12.3,
            "NORMAL_RANGE": (8.5, 12.3),
            "WARNING_MIN": 7.0,
            "CRITICAL_MIN": 5.0,
            "UNIT": "V"
        },
        "TEMPERATURE": {
            "Q1": 180,
            "Q2": 200,
            "Q3": 220,
            "NORMAL_RANGE": (180, 220),
            "WARNING_MAX": 250,
            "CRITICAL_MAX": 300,
            "UNIT": "°C"
        },
        "ROBOT_CURRENT": {
            "Q1": 150,
            "Q2": 175,
            "Q3": 200,
            "NORMAL_RANGE": (150, 200),
            "WARNING_MAX": 220,
            "CRITICAL_MAX": 250,
            "UNIT": "A",
            "DESCRIPTION": "용접 로봇 전류 (KAMP 시스템)"
        },
        "ROBOT_VIBRATION": {
            "Q1": 0.5,
            "Q2": 1.0,
            "Q3": 1.5,
            "NORMAL_RANGE": (0.5, 1.5),
            "WARNING_MAX": 2.0,
            "CRITICAL_MAX": 3.0,
            "UNIT": "m/s²",
            "DESCRIPTION": "용접 로봇 진동 (KAMP 시스템)"
        }
    },

    "PAINT": {
        "THICKNESS": {
            "Q1": 22,
            "Q2": 25,
            "Q3": 28,
            "NORMAL_RANGE": (22, 28),
            "WARNING_MIN": 18,
            "CRITICAL_MIN": 15,
            "UNIT": "μm"
        },
        "VOLTAGE": {
            "Q1": 215,
            "Q2": 225,
            "Q3": 235,
            "NORMAL_RANGE": (215, 235),
            "WARNING_RANGE": (200, 250),
            "CRITICAL_RANGE": (180, 270),
            "UNIT": "V"
        },
        "TEMPERATURE": {
            "Q1": 60,
            "Q2": 70,
            "Q3": 80,
            "NORMAL_RANGE": (60, 80),
            "WARNING_MAX": 90,
            "CRITICAL_MAX": 100,
            "UNIT": "°C"
        },
        "PAINT_VISCOSITY": {
            "Q1": 18,
            "Q2": 20,
            "Q3": 22,
            "NORMAL_RANGE": (18, 22),
            "WARNING_RANGE": (16, 24),
            "CRITICAL_RANGE": (14, 26),
            "UNIT": "초 (Ford Cup #4)",
            "DESCRIPTION": "도료 점도 측정값"
        },
        "SPRAY_PRESSURE": {
            "Q1": 2.5,
            "Q2": 3.0,
            "Q3": 3.5,
            "NORMAL_RANGE": (2.5, 3.5),
            "WARNING_RANGE": (2.0, 4.0),
            "CRITICAL_RANGE": (1.5, 4.5),
            "UNIT": "bar",
            "DESCRIPTION": "스프레이 압력"
        },
        "SURFACE_ROUGHNESS": {
            "Q1": 0.3,
            "Q2": 0.4,
            "Q3": 0.5,
            "NORMAL_RANGE": (0.3, 0.5),
            "WARNING_MAX": 0.7,
            "CRITICAL_MAX": 1.0,
            "UNIT": "μm Ra",
            "DESCRIPTION": "도장면 표면 거칠기"
        },
        "DEFECT_DENSITY": {
            "Q1": 0.1,
            "Q2": 0.3,
            "Q3": 0.5,
            "NORMAL_RANGE": (0.0, 0.5),
            "WARNING_MAX": 1.0,
            "CRITICAL_MAX": 2.0,
            "UNIT": "개/m²",
            "DESCRIPTION": "단위면적당 결함 개수"
        }
    },

    "VEHICLE": {
        "ASSEMBLY_FORCE": {
            "Q1": 150,
            "Q2": 175,
            "Q3": 200,
            "NORMAL_RANGE": (150, 200),
            "WARNING_MAX": 250,
            "CRITICAL_MAX": 300,
            "UNIT": "N"
        }
    },

    "PRESS_HYDRAULIC": {
        "HYDRAULIC_PRESSURE": {
            "Q1": 150,
            "Q2": 175,
            "Q3": 200,
            "NORMAL_RANGE": (150, 200),
            "WARNING_RANGE": (130, 220),
            "CRITICAL_RANGE": (110, 250),
            "UNIT": "bar",
            "DESCRIPTION": "유압 시스템 압력"
        },
        "OIL_TEMPERATURE": {
            "Q1": 40,
            "Q2": 50,
            "Q3": 60,
            "NORMAL_RANGE": (40, 60),
            "WARNING_MAX": 70,
            "CRITICAL_MAX": 80,
            "UNIT": "°C",
            "DESCRIPTION": "유압 오일 온도"
        },
        "FLOW_RATE": {
            "Q1": 80,
            "Q2": 100,
            "Q3": 120,
            "NORMAL_RANGE": (80, 120),
            "WARNING_RANGE": (70, 130),
            "CRITICAL_RANGE": (60, 140),
            "UNIT": "L/min",
            "DESCRIPTION": "유압 오일 유량"
        }
    },

    "WELDING_ROBOT_KAMP": {
        "ROBOT_CURRENT": {
            "Q1": 150,
            "Q2": 175,
            "Q3": 200,
            "NORMAL_RANGE": (150, 200),
            "WARNING_MAX": 220,
            "CRITICAL_MAX": 250,
            "UNIT": "A",
            "DESCRIPTION": "용접 로봇 전류 (KAMP 시스템)"
        },
        "ROBOT_VIBRATION": {
            "Q1": 0.5,
            "Q2": 1.0,
            "Q3": 1.5,
            "NORMAL_RANGE": (0.5, 1.5),
            "WARNING_MAX": 2.0,
            "CRITICAL_MAX": 3.0,
            "UNIT": "m/s²",
            "DESCRIPTION": "용접 로봇 진동 (KAMP 시스템)"
        },
        "TORCH_TEMPERATURE": {
            "Q1": 180,
            "Q2": 200,
            "Q3": 220,
            "NORMAL_RANGE": (180, 220),
            "WARNING_MAX": 250,
            "CRITICAL_MAX": 300,
            "UNIT": "°C",
            "DESCRIPTION": "용접 토치 온도"
        },
        "WIRE_FEED_SPEED": {
            "Q1": 8,
            "Q2": 10,
            "Q3": 12,
            "NORMAL_RANGE": (8, 12),
            "WARNING_RANGE": (6, 14),
            "CRITICAL_RANGE": (4, 16),
            "UNIT": "m/min",
            "DESCRIPTION": "와이어 공급 속도"
        }
    },


    "PAINTING_EQUIPMENT": {
        "VOLTAGE": {
            "Q1": 220,
            "Q2": 230,
            "Q3": 240,
            "NORMAL_RANGE": (220, 240),
            "WARNING_RANGE": (210, 250),
            "CRITICAL_RANGE": (200, 260),
            "UNIT": "V",
            "DESCRIPTION": "전압 모니터링 (예지보전)"
        },
        "CURRENT": {
            "Q1": 15,
            "Q2": 25,
            "Q3": 35,
            "NORMAL_RANGE": (15, 35),
            "WARNING_RANGE": (10, 45),
            "CRITICAL_RANGE": (5, 60),
            "UNIT": "A",
            "DESCRIPTION": "전류 모니터링 (예지보전)"
        },
        "TEMPERATURE": {
            "Q1": 40,
            "Q2": 60,
            "Q3": 80,
            "NORMAL_RANGE": (40, 80),
            "WARNING_RANGE": (30, 90),
            "CRITICAL_RANGE": (20, 100),
            "UNIT": "°C",
            "DESCRIPTION": "온도 모니터링 (예지보전)"
        },
        "VIBRATION": {
            "Q1": 2.5,
            "Q2": 4.2,
            "Q3": 6.8,
            "NORMAL_RANGE": (2.5, 6.8),
            "WARNING_RANGE": (1.5, 8.5),
            "CRITICAL_RANGE": (0.5, 12.0),
            "UNIT": "mm/s",
            "DESCRIPTION": "진동 레벨 (기계적 상태)"
        },
        "PRESSURE": {
            "Q1": 2.0,
            "Q2": 3.0,
            "Q3": 4.0,
            "NORMAL_RANGE": (2.0, 4.0),
            "WARNING_RANGE": (1.5, 4.5),
            "CRITICAL_RANGE": (1.0, 5.0),
            "UNIT": "bar",
            "DESCRIPTION": "시스템 압력"
        }
    },

    "PAINTING_COATING": {
        "DEFECT_SIZE_WIDTH": {
            "Q1": 10,
            "Q2": 31,
            "Q3": 126.25,
            "NORMAL_RANGE": (0, 31),
            "WARNING_RANGE": (31, 126.25),
            "CRITICAL_RANGE": (126.25, 500),
            "UNIT": "pixels",
            "DESCRIPTION": "컬링 탐지 결함 크기 - 폭"
        },
        "DEFECT_SIZE_HEIGHT": {
            "Q1": 16,
            "Q2": 47,
            "Q3": 165,
            "NORMAL_RANGE": (0, 47),
            "WARNING_RANGE": (47, 165),
            "CRITICAL_RANGE": (165, 600),
            "UNIT": "pixels",
            "DESCRIPTION": "컬링 탐지 결함 크기 - 높이"
        },
        "DEFECT_SIZE_AREA": {
            "Q1": 164,
            "Q2": 1626,
            "Q3": 20146,
            "NORMAL_RANGE": (0, 1626),
            "WARNING_RANGE": (1626, 20146),
            "CRITICAL_RANGE": (20146, 100000),
            "UNIT": "pixels²",
            "DESCRIPTION": "컬링 탐지 결함 크기 - 면적"
        },
        "DETECTION_ACCURACY": {
            "Q1": 92.0,
            "Q2": 95.2,
            "Q3": 97.8,
            "NORMAL_RANGE": (95.0, 100.0),
            "WARNING_RANGE": (90.0, 95.0),
            "CRITICAL_MIN": 85.0,
            "UNIT": "%",
            "DESCRIPTION": "컬링 탐지 시스템 정확도"
        },
        "PROCESSING_SPEED": {
            "Q1": 30,
            "Q2": 50,
            "Q3": 80,
            "NORMAL_RANGE": (0, 50),
            "WARNING_RANGE": (50, 100),
            "CRITICAL_MAX": 150,
            "UNIT": "ms",
            "DESCRIPTION": "프레임당 처리 시간"
        },
        "SURFACE_ROUGHNESS": {
            "Q1": 0.2,
            "Q2": 0.4,
            "Q3": 0.8,
            "NORMAL_RANGE": (0.1, 0.5),
            "WARNING_RANGE": (0.5, 1.0),
            "CRITICAL_MAX": 2.0,
            "UNIT": "μm Ra",
            "DESCRIPTION": "도장 표면 거칠기"
        }
    },

    "PRESS_PRODUCTIVITY": {
        "PRESS_TIME": {
            "Q1": 530,
            "Q2": 550,
            "Q3": 570,
            "MEAN": 550.13,
            "STD_DEV": 18.5,
            "NORMAL_RANGE": (530, 570),
            "WARNING_RANGE": (512, 588),
            "CRITICAL_RANGE": (495, 605),
            "UNIT": "ms",
            "DESCRIPTION": "프레스 작업 사이클 시간"
        },
        "FORMING_PRESSURE_1": {
            "Q1": 262,
            "Q2": 275,
            "Q3": 288,
            "MEAN": 275.07,
            "STD_DEV": 12.3,
            "NORMAL_RANGE": (262, 288),
            "WARNING_RANGE": (250, 300),
            "CRITICAL_RANGE": (238, 312),
            "UNIT": "bar",
            "DESCRIPTION": "주 성형 압력"
        },
        "FORMING_PRESSURE_2": {
            "Q1": 258,
            "Q2": 270,
            "Q3": 282,
            "MEAN": 269.79,
            "STD_DEV": 11.8,
            "NORMAL_RANGE": (258, 282),
            "WARNING_RANGE": (245, 295),
            "CRITICAL_RANGE": (233, 307),
            "UNIT": "bar",
            "DESCRIPTION": "보조 성형 압력"
        },
        "BLANK_HOLDER_PRESSURE": {
            "Q1": 520,
            "Q2": 545,
            "Q3": 570,
            "MEAN": 544.85,
            "STD_DEV": 25.2,
            "NORMAL_RANGE": (520, 570),
            "WARNING_RANGE": (490, 600),
            "CRITICAL_RANGE": (470, 620),
            "UNIT": "bar",
            "DESCRIPTION": "블랭크 홀더 압력"
        },
        "DIE_CLEARANCE": {
            "Q1": 0.05,
            "Q2": 0.065,
            "Q3": 0.08,
            "NORMAL_RANGE": (0.05, 0.08),
            "WARNING_RANGE": (0.03, 0.10),
            "CRITICAL_RANGE": (0.02, 0.12),
            "UNIT": "mm",
            "DESCRIPTION": "다이 클리어런스 (재료 두께 대비 비율)"
        },
        "DEFECT_RATE": {
            "Q1": 0.5,
            "Q2": 1.0,
            "Q3": 2.0,
            "NORMAL_RANGE": (0.0, 2.0),
            "WARNING_MAX": 5.0,
            "CRITICAL_MAX": 10.0,
            "UNIT": "%",
            "DESCRIPTION": "제품 결함률"
        }
    },

    "ASSEMBLY_PARTS": {
        "TORQUE": {
            "Q1": 40,
            "Q2": 45,
            "Q3": 50,
            "NORMAL_RANGE": (40, 50),
            "WARNING_RANGE": (35, 55),
            "CRITICAL_RANGE": (30, 60),
            "UNIT": "N·m",
            "DESCRIPTION": "체결 토크 (도어, 범퍼 등)"
        },
        "INSERTION_FORCE": {
            "Q1": 12,
            "Q2": 15,
            "Q3": 18,
            "NORMAL_RANGE": (12, 18),
            "WARNING_RANGE": (10, 20),
            "CRITICAL_RANGE": (8, 25),
            "UNIT": "N",
            "DESCRIPTION": "커넥터 삽입력"
        },
        "CLIP_FORCE": {
            "Q1": 20,
            "Q2": 25,
            "Q3": 30,
            "NORMAL_RANGE": (20, 30),
            "WARNING_RANGE": (15, 35),
            "CRITICAL_RANGE": (10, 40),
            "UNIT": "N",
            "DESCRIPTION": "클립 체결력"
        },
        "PANEL_GAP": {
            "Q1": 1.0,
            "Q2": 1.5,
            "Q3": 2.0,
            "NORMAL_RANGE": (1.0, 2.0),
            "WARNING_RANGE": (0.5, 2.5),
            "CRITICAL_RANGE": (0.0, 3.0),
            "UNIT": "mm",
            "DESCRIPTION": "패널 간 유격 (테일 램프, 그릴 등)"
        },
        "SEALING_COMPRESSION": {
            "Q1": 15,
            "Q2": 20,
            "Q3": 25,
            "NORMAL_RANGE": (15, 25),
            "WARNING_RANGE": (10, 30),
            "CRITICAL_RANGE": (5, 35),
            "UNIT": "%",
            "DESCRIPTION": "실링 압축률"
        },
        "CONTACT_RESISTANCE": {
            "Q1": 5,
            "Q2": 10,
            "Q3": 15,
            "NORMAL_RANGE": (5, 15),
            "WARNING_RANGE": (0, 20),
            "CRITICAL_MAX": 50,
            "UNIT": "mΩ",
            "DESCRIPTION": "전기 접촉 저항"
        },
        "ASSEMBLY_TIME": {
            "Q1": 30,
            "Q2": 45,
            "Q3": 60,
            "NORMAL_RANGE": (30, 60),
            "WARNING_RANGE": (20, 75),
            "CRITICAL_MAX": 120,
            "UNIT": "초",
            "DESCRIPTION": "부품 조립 시간"
        },
        "POSITION_ACCURACY": {
            "Q1": 0.2,
            "Q2": 0.5,
            "Q3": 0.8,
            "NORMAL_RANGE": (0.0, 0.8),
            "WARNING_RANGE": (0.8, 1.2),
            "CRITICAL_MAX": 2.0,
            "UNIT": "mm",
            "DESCRIPTION": "위치 정확도 (클립, 체결점 등)"
        }
    }
}

# 장비별 문제 원인 데이터베이스
EQUIPMENT_ROOT_CAUSES = {
    "PRESS": {
        "PRESSURE_HIGH": [
            {
                "cause": "유압 릴리프 밸브 설정값 이상 또는 고착",
                "probability": 0.75,
                "evidence_template": "압력이 Q3({q3}) 초과",
                "inspection_points": [
                    "릴리프 밸브 설정 압력 확인",
                    "밸브 시트 마모 상태 점검",
                    "밸브 스프링 장력 측정"
                ],
                "urgency": "높음",
                "estimated_fix_time": "2-4시간"
            },
            {
                "cause": "유압 펌프 과부하 또는 제어 시스템 오류",
                "probability": 0.60,
                "evidence_template": "시스템 압력 지속적 상승",
                "inspection_points": [
                    "펌프 토출 압력 측정",
                    "모터 전류값 확인",
                    "압력 센서 정확도 점검"
                ],
                "urgency": "보통",
                "estimated_fix_time": "4-8시간"
            }
        ],
        "VIBRATION_ABNORMAL": [
            {
                "cause": "주축 베어링 마모 또는 손상",
                "probability": 0.80,
                "evidence_template": "진동값이 Q3({q3}) 초과",
                "inspection_points": [
                    "주축 베어링 상태 점검",
                    "윤활유 상태 확인",
                    "베어링 클리어런스 측정"
                ],
                "urgency": "높음",
                "estimated_fix_time": "4-6시간"
            }
        ],
        "CURRENT_HIGH": [
            {
                "cause": "모터 과부하 또는 기계적 저항 증가",
                "probability": 0.70,
                "evidence_template": "전류값이 Q3({q3}) 초과",
                "inspection_points": [
                    "모터 절연 저항 측정",
                    "기계적 구속 여부 확인",
                    "유압 시스템 부하 점검"
                ],
                "urgency": "높음",
                "estimated_fix_time": "3-6시간"
            }
        ]
    },

    "WELD": {
        "SENSOR_DECLINE": [
            {
                "cause": "전극 마모 진행으로 인한 성능 저하",
                "probability": 0.85,
                "evidence_template": "센서값이 Q1({q1}) 미만",
                "inspection_points": [
                    "전극 마모 상태 육안 점검",
                    "전극 교체 주기 확인",
                    "용접 품질 샘플 검사"
                ],
                "urgency": "보통",
                "estimated_fix_time": "1-2시간"
            }
        ],
        "TEMPERATURE_HIGH": [
            {
                "cause": "냉각 시스템 효율 저하",
                "probability": 0.75,
                "evidence_template": "온도가 Q3({q3}) 초과",
                "inspection_points": [
                    "냉각수 순환 상태",
                    "냉각 팬 작동 상태",
                    "열교환기 청결 상태"
                ],
                "urgency": "높음",
                "estimated_fix_time": "3-5시간"
            }
        ]
    },

    "PAINT": {
        "THICKNESS_LOW": [
            {
                "cause": "스프레이 노즐 막힘 또는 압력 부족",
                "probability": 0.80,
                "evidence_template": "도장 두께가 Q1({q1}) 미만",
                "inspection_points": [
                    "노즐 구멍 막힘 상태",
                    "공기 압력 게이지 확인",
                    "도료 공급 압력 측정"
                ],
                "urgency": "보통",
                "estimated_fix_time": "1-3시간"
            }
        ],
        "SURFACE_BUBBLE": [
            {
                "cause": "도료 내 수분 또는 공기 혼입",
                "probability": 0.75,
                "evidence_template": "표면 기포 발생",
                "inspection_points": [
                    "도료 혼합 상태",
                    "교반기 작동 상태",
                    "도료 저장 환경"
                ],
                "urgency": "보통",
                "estimated_fix_time": "2-4시간"
            }
        ]
    },

    "VEHICLE": {
        "ASSEMBLY_FORCE_HIGH": [
            {
                "cause": "부품 치수 공차 초과 또는 이물질 끼임",
                "probability": 0.70,
                "evidence_template": "조립력이 Q3({q3}) 초과",
                "inspection_points": [
                    "부품 치수 측정",
                    "조립 부위 청결도",
                    "지그 정렬 상태"
                ],
                "urgency": "보통",
                "estimated_fix_time": "2-4시간"
            }
        ]
    }
}

# 번역 데이터
EQUIPMENT_TRANSLATIONS = {
    "PRESS": "프레스",
    "WELD": "용접기",
    "PAINT": "도장설비",
    "VEHICLE": "차량조립설비",
    "PRESS_HYDRAULIC": "프레스 유압시스템",
    "WELDING_ROBOT_KAMP": "용접 로봇 KAMP",
    "PAINTING_COATING": "도장포막 컬링 탐지",
    "PRESS_PRODUCTIVITY": "프레스 생산성",
    "PAINTING_EQUIPMENT": "도장설비 예지보전",
    "ASSEMBLY_PARTS": "조립 부품 품질관리"
}

PROBLEM_TYPE_TRANSLATIONS = {
    # 프레스 관련
    "PRESSURE_HIGH": "압력 과다",
    "PRESSURE_LOW": "압력 부족",
    "VIBRATION_ABNORMAL": "진동 이상",
    "VIBRATION_HIGH": "과도한 진동",
    "CURRENT_HIGH": "전류 과다",
    "CURRENT_LOW": "전류 부족",

    # 용접 관련
    "SENSOR_DECLINE": "센서값 하락",
    "SENSOR_SPIKE": "센서값 급상승",
    "SENSOR_UNSTABLE": "센서값 불안정",
    "TEMPERATURE_HIGH": "온도 과열",
    "TEMPERATURE_LOW": "온도 부족",

    # 도장 관련
    "SURFACE_BUBBLE": "표면 기포",
    "SURFACE_SCRATCH": "표면 긁힘",
    "THICKNESS_LOW": "두께 부족",
    "THICKNESS_HIGH": "두께 과다",
    "VOLTAGE_UNSTABLE": "전압 불안정",

    # 차량 조립 관련
    "ASSEMBLY_FORCE_HIGH": "조립력 과다",
    "ASSEMBLY_DEFECT": "조립 불량",
    "PART_MISALIGN": "부품 정렬 불량"
}
