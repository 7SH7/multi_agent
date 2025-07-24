ISSUE_DATABASE = {
    "ASBP-DOOR-SCRATCH": {
        "description": "도어 스크래치",
        "category": "표면 손상",
        "severity": "보통",
        "common_causes": [
            "조립 공정 중 충돌",
            "작업자 부주의",
            "장비 간섭",
            "운반 과정 중 손상"
        ],
        "standard_solutions": [
            "작업자 교육 강화",
            "조립 간 간섭 방지 설계",
            "보호 패드 설치",
            "운반 지그 개선"
        ],
        "affected_components": ["도어 외판", "도어 핸들", "도어 몰딩"],
        "search_keywords": ["도어", "스크래치", "표면손상", "조립공정", "외관불량"]
    },

    "ASBP-GRILL-GAP": {
        "description": "라디에이터 그릴 단차",
        "category": "치수 불량",
        "severity": "높음",
        "common_causes": [
            "고정 브래킷 사양 불일치",
            "조립 위치 정렬 오차",
            "브래킷 변형 또는 강성 부족",
            "볼트 체결 토크 부족"
        ],
        "standard_solutions": [
            "브래킷 사양 통일 및 검수",
            "정렬용 지그 도입",
            "정렬센서 보정",
            "체결 토크 관리 강화"
        ],
        "affected_components": ["라디에이터 그릴", "고정 브래킷", "범퍼"],
        "search_keywords": ["그릴", "단차", "정렬", "브래킷", "치수불량"]
    },

    "ASBP-BUMPER-CRACK": {
        "description": "범퍼 크랙",
        "category": "구조 손상",
        "severity": "높음",
        "common_causes": [
            "온도 변화에 의한 수축팽창",
            "충격 흡수 한계 초과",
            "재료 피로 누적",
            "설계 응력 집중"
        ],
        "standard_solutions": [
            "재료 강도 개선",
            "응력 집중 부위 보강",
            "온도 관리 강화",
            "충격 흡수 구조 개선"
        ],
        "affected_components": ["전면 범퍼", "후면 범퍼", "충격 흡수재"],
        "search_keywords": ["범퍼", "크랙", "균열", "구조손상", "충격"]
    },

    "ASBP-PAINT-DEFECT": {
        "description": "도장 불량",
        "category": "표면 품질",
        "severity": "보통",
        "common_causes": [
            "도장 부스 온습도 조건 불량",
            "스프레이 건 노즐 문제",
            "도료 점도 관리 불량",
            "전처리 공정 불완전"
        ],
        "standard_solutions": [
            "부스 환경 조건 최적화",
            "스프레이 장비 정비",
            "도료 품질 관리 강화",
            "전처리 공정 개선"
        ],
        "affected_components": ["차체 외판", "플라스틱 부품", "메탈 부품"],
        "search_keywords": ["도장", "페인트", "표면", "색상", "광택"]
    },

    "ASBP-ENGINE-NOISE": {
        "description": "엔진 이상음",
        "category": "성능 이상",
        "severity": "높음",
        "common_causes": [
            "베어링 마모",
            "밸브 간극 조정 불량",
            "연료 계통 문제",
            "점화 계통 불량"
        ],
        "standard_solutions": [
            "베어링 교체",
            "밸브 간극 재조정",
            "연료 계통 점검",
            "점화 계통 정비"
        ],
        "affected_components": ["엔진 블록", "밸브", "베어링", "연료 펌프"],
        "search_keywords": ["엔진", "소음", "진동", "성능", "이상음"]
    },

    "ASBP-BRAKE-FADE": {
        "description": "브레이크 페이드",
        "category": "안전 관련",
        "severity": "매우높음",
        "common_causes": [
            "브레이크 패드 과열",
            "브레이크 유압 부족",
            "디스크 변형",
            "냉각 시스템 불량"
        ],
        "standard_solutions": [
            "브레이크 패드 교체",
            "유압 시스템 점검",
            "디스크 교체",
            "냉각 성능 개선"
        ],
        "affected_components": ["브레이크 패드", "브레이크 디스크", "캘리퍼"],
        "search_keywords": ["브레이크", "페이드", "제동력", "안전", "열화"]
    }
}

# 이슈 카테고리별 분류
ISSUE_CATEGORIES = {
    "표면 손상": ["ASBP-DOOR-SCRATCH", "ASBP-PAINT-DEFECT"],
    "치수 불량": ["ASBP-GRILL-GAP"],
    "구조 손상": ["ASBP-BUMPER-CRACK"],
    "성능 이상": ["ASBP-ENGINE-NOISE"],
    "안전 관련": ["ASBP-BRAKE-FADE"]
}

# 심각도별 분류
SEVERITY_LEVELS = {
    "매우높음": ["ASBP-BRAKE-FADE"],
    "높음": ["ASBP-GRILL-GAP", "ASBP-BUMPER-CRACK", "ASBP-ENGINE-NOISE"],
    "보통": ["ASBP-DOOR-SCRATCH", "ASBP-PAINT-DEFECT"],
    "낮음": []
}