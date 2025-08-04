"""
Knowledge Base API 엔드포인트
config/와 data/ 폴더의 데이터를 API로 제공
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from data import load_knowledge_data, get_available_datasets, validate_data_structure
from config.equipment_thresholds import (
    EQUIPMENT_THRESHOLDS, 
    EQUIPMENT_ROOT_CAUSES,
    EQUIPMENT_TRANSLATIONS,
    PROBLEM_TYPE_TRANSLATIONS
)
from config.issue_database import ISSUE_DATABASE

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.get("/datasets")
async def get_datasets():
    """사용 가능한 모든 데이터셋 목록 조회"""
    try:
        datasets = get_available_datasets()
        validation = validate_data_structure()
        
        return {
            "available_datasets": datasets,
            "total_datasets": len(datasets),
            "validation_status": validation["overall_valid"],
            "total_documents": validation["total_documents"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {str(e)}")

@router.get("/manual/{filename}")
async def get_manual(filename: str):
    """특정 매뉴얼 파일 조회"""
    try:
        if not filename.endswith('.json'):
            filename += '.json'
            
        data = load_knowledge_data(filename)
        return {
            "filename": filename,
            "equipment_type": data.get("equipment_type"),
            "model": data.get("model"), 
            "sections_count": len(data.get("sections", [])),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Manual not found: {str(e)}")

@router.get("/equipment/thresholds")
async def get_equipment_thresholds(equipment_type: Optional[str] = None):
    """장비별 임계값 조회"""
    try:
        if equipment_type:
            equipment_type = equipment_type.upper()
            if equipment_type not in EQUIPMENT_THRESHOLDS:
                raise HTTPException(status_code=404, detail=f"Equipment type '{equipment_type}' not found")
            
            return {
                "equipment_type": equipment_type,
                "korean_name": EQUIPMENT_TRANSLATIONS.get(equipment_type, equipment_type),
                "thresholds": EQUIPMENT_THRESHOLDS[equipment_type]
            }
        else:
            return {
                "total_equipment_types": len(EQUIPMENT_THRESHOLDS),
                "available_types": list(EQUIPMENT_THRESHOLDS.keys()),
                "translations": EQUIPMENT_TRANSLATIONS,
                "all_thresholds": EQUIPMENT_THRESHOLDS
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thresholds: {str(e)}")

@router.get("/equipment/root-causes")
async def get_root_causes(equipment_type: Optional[str] = None):
    """장비별 근본 원인 분석 데이터 조회"""
    try:
        if equipment_type:
            equipment_type = equipment_type.upper()
            if equipment_type not in EQUIPMENT_ROOT_CAUSES:
                return {"equipment_type": equipment_type, "root_causes": {}, "message": "No root cause data available"}
            
            return {
                "equipment_type": equipment_type,
                "korean_name": EQUIPMENT_TRANSLATIONS.get(equipment_type, equipment_type),
                "root_causes": EQUIPMENT_ROOT_CAUSES[equipment_type]
            }
        else:
            return {
                "total_equipment_types": len(EQUIPMENT_ROOT_CAUSES),
                "available_types": list(EQUIPMENT_ROOT_CAUSES.keys()),
                "all_root_causes": EQUIPMENT_ROOT_CAUSES
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get root causes: {str(e)}")

@router.get("/issues")
async def get_issues(category: Optional[str] = None, severity: Optional[str] = None):
    """이슈 데이터베이스 조회"""
    try:
        filtered_issues = ISSUE_DATABASE.copy()
        
        if category:
            filtered_issues = {k: v for k, v in filtered_issues.items() if v.get("category") == category}
        
        if severity:
            filtered_issues = {k: v for k, v in filtered_issues.items() if v.get("severity") == severity}
        
        return {
            "total_issues": len(filtered_issues),
            "filters": {"category": category, "severity": severity},
            "issues": filtered_issues,
            "problem_translations": PROBLEM_TYPE_TRANSLATIONS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get issues: {str(e)}")

@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="검색 키워드"),
    equipment_type: Optional[str] = None,
    category: Optional[str] = None
):
    """지식베이스 통합 검색"""
    try:
        results = {
            "query": query,
            "manuals": [],
            "issues": [],
            "thresholds": []
        }
        
        # 1. 매뉴얼 검색
        datasets = get_available_datasets()
        for dataset in datasets:
            try:
                data = load_knowledge_data(dataset)
                if equipment_type and data.get("equipment_type") != equipment_type.upper():
                    continue
                    
                # 키워드가 포함된 섹션 찾기
                for section in data.get("sections", []):
                    content = str(section.get("content", "")).lower()
                    keywords = section.get("keywords", [])
                    
                    if (query.lower() in content or 
                        any(query.lower() in str(keyword).lower() for keyword in keywords)):
                        results["manuals"].append({
                            "dataset": dataset,
                            "equipment_type": data.get("equipment_type"),
                            "section_title": section.get("title"),
                            "content_preview": content[:200] + "..." if len(content) > 200 else content
                        })
            except:
                continue
        
        # 2. 이슈 검색  
        for issue_code, issue_data in ISSUE_DATABASE.items():
            if (query.lower() in issue_data.get("description", "").lower() or
                any(query.lower() in str(keyword).lower() for keyword in issue_data.get("search_keywords", []))):
                
                if category and issue_data.get("category") != category:
                    continue
                    
                results["issues"].append({
                    "issue_code": issue_code,
                    "description": issue_data.get("description"),
                    "category": issue_data.get("category"),
                    "severity": issue_data.get("severity")
                })
        
        # 3. 임계값 검색
        for eq_type, thresholds in EQUIPMENT_THRESHOLDS.items():
            if equipment_type and eq_type != equipment_type.upper():
                continue
                
            for param_name, param_data in thresholds.items():
                if query.lower() in param_name.lower():
                    results["thresholds"].append({
                        "equipment_type": eq_type,
                        "parameter": param_name,
                        "thresholds": param_data
                    })
        
        return {
            "search_results": results,
            "total_found": {
                "manuals": len(results["manuals"]),
                "issues": len(results["issues"]), 
                "thresholds": len(results["thresholds"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary():
    """전체 지식베이스 분석 요약"""
    try:
        # 데이터셋 통계
        datasets = get_available_datasets()
        validation = validate_data_structure()
        
        # 장비 타입별 통계
        equipment_stats = {}
        for dataset in datasets:
            try:
                data = load_knowledge_data(dataset)
                eq_type = data.get("equipment_type", "UNKNOWN")
                if eq_type not in equipment_stats:
                    equipment_stats[eq_type] = {"manuals": 0, "sections": 0}
                equipment_stats[eq_type]["manuals"] += 1
                equipment_stats[eq_type]["sections"] += len(data.get("sections", []))
            except:
                continue
        
        # 이슈 통계
        issue_stats = {}
        for issue_data in ISSUE_DATABASE.values():
            category = issue_data.get("category", "기타")
            severity = issue_data.get("severity", "보통")
            
            if category not in issue_stats:
                issue_stats[category] = {}
            if severity not in issue_stats[category]:
                issue_stats[category][severity] = 0
            issue_stats[category][severity] += 1
        
        return {
            "dataset_summary": {
                "total_datasets": len(datasets),
                "total_documents": validation["total_documents"],
                "validation_status": validation["overall_valid"]
            },
            "equipment_statistics": equipment_stats,
            "issue_statistics": issue_stats,
            "threshold_coverage": {
                "total_equipment_types": len(EQUIPMENT_THRESHOLDS),
                "equipment_types": list(EQUIPMENT_THRESHOLDS.keys())
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")