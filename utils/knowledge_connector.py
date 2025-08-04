"""
Knowledge Base Connector
Agent들이 config/와 data/ 정보를 쉽게 사용할 수 있도록 하는 연결 모듈
"""

from typing import Dict, List, Any, Optional
from data import load_knowledge_data, get_available_datasets
from config.equipment_thresholds import (
    EQUIPMENT_THRESHOLDS, 
    EQUIPMENT_ROOT_CAUSES,
    EQUIPMENT_TRANSLATIONS,
    PROBLEM_TYPE_TRANSLATIONS
)
from config.issue_database import ISSUE_DATABASE

class KnowledgeConnector:
    """지식베이스 데이터에 대한 통합 접근 인터페이스"""
    
    def __init__(self):
        self.datasets = get_available_datasets()
        self._manual_cache = {}
    
    def get_equipment_info(self, equipment_type: str) -> Dict[str, Any]:
        """장비 타입에 대한 모든 정보를 통합하여 반환"""
        equipment_type = equipment_type.upper()
        
        result = {
            "equipment_type": equipment_type,
            "korean_name": EQUIPMENT_TRANSLATIONS.get(equipment_type, equipment_type),
            "thresholds": EQUIPMENT_THRESHOLDS.get(equipment_type, {}),
            "root_causes": EQUIPMENT_ROOT_CAUSES.get(equipment_type, {}),
            "manual": None,
            "related_issues": []
        }
        
        # 매뉴얼 데이터 찾기
        manual_file = self._find_manual_for_equipment(equipment_type)
        if manual_file:
            result["manual"] = self.get_manual(manual_file)
        
        # 관련 이슈 찾기
        for issue_code, issue_data in ISSUE_DATABASE.items():
            if equipment_type.lower() in issue_code.lower():
                result["related_issues"].append({
                    "issue_code": issue_code,
                    "description": issue_data.get("description"),
                    "category": issue_data.get("category"),
                    "severity": issue_data.get("severity")
                })
        
        return result
    
    def get_manual(self, filename: str) -> Optional[Dict[str, Any]]:
        """매뉴얼 데이터 조회 (캐싱 포함)"""
        if filename in self._manual_cache:
            return self._manual_cache[filename]
        
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            data = load_knowledge_data(filename)
            self._manual_cache[filename] = data
            return data
        except Exception:
            return None
    
    def find_threshold_info(self, equipment_type: str, parameter: str) -> Optional[Dict[str, Any]]:
        """특정 장비의 특정 파라미터 임계값 정보 조회"""
        equipment_type = equipment_type.upper()
        
        thresholds = EQUIPMENT_THRESHOLDS.get(equipment_type, {})
        if parameter.upper() in thresholds:
            return {
                "equipment_type": equipment_type,
                "parameter": parameter,
                "thresholds": thresholds[parameter.upper()],
                "korean_name": EQUIPMENT_TRANSLATIONS.get(equipment_type, equipment_type)
            }
        return None
    
    def search_solutions(self, issue_code: str) -> Dict[str, Any]:
        """이슈 코드에 대한 해결책 검색"""
        issue_data = ISSUE_DATABASE.get(issue_code, {})
        if not issue_data:
            return {"found": False, "message": f"Issue code '{issue_code}' not found"}
        
        # 관련 장비 정보 찾기
        equipment_info = None
        for eq_type in EQUIPMENT_TRANSLATIONS.keys():
            if eq_type.lower() in issue_code.lower():
                equipment_info = self.get_equipment_info(eq_type)
                break
        
        return {
            "found": True,
            "issue": issue_data,
            "equipment_info": equipment_info,
            "translated_problem": PROBLEM_TYPE_TRANSLATIONS.get(
                issue_code.split('-')[-1] if '-' in issue_code else issue_code, 
                "알 수 없는 문제"
            )
        }
    
    def get_context_for_agent(self, equipment_type: Optional[str] = None, issue_code: Optional[str] = None) -> str:
        """Agent에게 제공할 컨텍스트 정보 생성"""
        context_parts = []
        
        if equipment_type:
            eq_info = self.get_equipment_info(equipment_type)
            context_parts.append(f"[장비 정보: {eq_info['korean_name']} ({equipment_type})]")
            
            # 임계값 정보
            if eq_info['thresholds']:
                context_parts.append("임계값 정보:")
                for param, values in eq_info['thresholds'].items():
                    if isinstance(values, dict) and 'UNIT' in values:
                        context_parts.append(f"- {param}: {values.get('NORMAL_RANGE', 'N/A')} {values.get('UNIT', '')}")
            
            # 매뉴얼 정보
            if eq_info['manual']:
                manual = eq_info['manual']
                context_parts.append(f"매뉴얼: {manual.get('model', '')}")
                sections = manual.get('sections', [])
                if sections:
                    context_parts.append(f"주요 섹션: {', '.join([s.get('title', '') for s in sections[:3]])}")
        
        if issue_code:
            solution_info = self.search_solutions(issue_code)
            if solution_info['found']:
                issue = solution_info['issue']
                context_parts.append(f"[이슈 정보: {issue.get('description', '')}]")
                context_parts.append(f"심각도: {issue.get('severity', '')}")
                if issue.get('common_causes'):
                    context_parts.append(f"일반적 원인: {', '.join(issue['common_causes'][:3])}")
        
        return "\n".join(context_parts)
    
    def _find_manual_for_equipment(self, equipment_type: str) -> Optional[str]:
        """장비 타입에 해당하는 매뉴얼 파일 찾기"""
        equipment_type = equipment_type.lower()
        
        # 직접 매칭되는 파일 찾기
        for dataset in self.datasets:
            if equipment_type in dataset.lower():
                return dataset
        
        # 장비 타입별 매핑
        type_mapping = {
            'press_hydraulic': 'press_hydraulic_manual.json',
            'press_productivity': 'press_productivity_manual.json',
            'welding_robot_kamp': 'welding_robot_kamp_manual.json',
            'painting_coating': 'painting_coating_manual.json',
            'painting_equipment': 'painting_equipment_manual.json', 
            'assembly_parts': 'assembly_parts_manual.json'
        }
        
        return type_mapping.get(equipment_type)

# 전역 인스턴스
knowledge_connector = KnowledgeConnector()

def get_knowledge_connector() -> KnowledgeConnector:
    """Knowledge Connector 인스턴스 반환"""
    return knowledge_connector