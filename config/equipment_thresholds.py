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
    "VEHICLE": "차량조립설비"
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
