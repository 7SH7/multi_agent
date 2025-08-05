"""
Data 패키지 초기화
지식베이스 데이터와 임베딩 관리를 담당합니다.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, cast

# 패키지 메타데이터
__version__ = "1.0.0"

# 데이터 경로 설정
DATA_ROOT = Path(__file__).parent
KNOWLEDGE_BASE_PATH = DATA_ROOT / "knowledge_base"
EMBEDDINGS_PATH = DATA_ROOT / "embeddings"

# 공개 API
__all__ = [
    "DATA_ROOT",
    "KNOWLEDGE_BASE_PATH",
    "EMBEDDINGS_PATH",
    "load_knowledge_data",
    "get_available_datasets",
    "validate_data_structure",
    "DataError"
]


# 사용자 정의 예외
class DataError(Exception):
    """데이터 관련 오류"""
    pass


# 지식베이스 데이터 로딩
def load_knowledge_data(filename: str) -> Dict[str, Any]:
    """지식베이스 JSON 파일을 로드합니다."""
    file_path = KNOWLEDGE_BASE_PATH / filename

    if not file_path.exists():
        raise DataError(f"Knowledge base file not found: {filename}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)

        if not isinstance(data, dict):
            raise DataError(f"Invalid data format in {filename}: expected dict")

        return data

    except json.JSONDecodeError as e:
        raise DataError(f"Invalid JSON in {filename}: {e}")
    except Exception as e:
        raise DataError(f"Failed to load {filename}: {e}")


# 사용 가능한 데이터셋 목록
def get_available_datasets() -> List[str]:
    """사용 가능한 지식베이스 데이터셋 목록을 반환합니다."""
    if not KNOWLEDGE_BASE_PATH.exists():
        return []

    json_files = []
    for file_path in KNOWLEDGE_BASE_PATH.glob("*.json"):
        json_files.append(file_path.name)

    return sorted(json_files)


# 데이터 구조 검증
def validate_data_structure() -> Dict[str, Any]:
    """데이터 폴더 구조와 파일들을 검증합니다."""
    validation_results: Dict[str, Any] = {
        "knowledge_base_exists": KNOWLEDGE_BASE_PATH.exists(),
        "embeddings_exists": EMBEDDINGS_PATH.exists(),
        "datasets": [],
        "total_documents": 0,
        "validation_errors": []
    }

    try:
        # 지식베이스 파일들 검증
        if validation_results["knowledge_base_exists"]:
            datasets = get_available_datasets()
            validation_results["datasets"] = datasets

            for dataset in datasets:
                try:
                    data: Dict[str, Any] = load_knowledge_data(dataset)
                    # Dict 형태이므로 sections의 개수를 세어봄
                    sections: List[Dict[str, Any]] = data.get('sections', [])
                    doc_count: int = len(sections)
                    validation_results["total_documents"] += doc_count
                except DataError as e:
                    validation_results["validation_errors"].append(str(e))

        # 임베딩 폴더 구조 확인
        if validation_results["embeddings_exists"]:
            chromadb_path = EMBEDDINGS_PATH / "chromadb"
            validation_results["chromadb_ready"] = chromadb_path.exists()

        # 전체 검증 결과
        validation_results["overall_valid"] = (
                validation_results["knowledge_base_exists"] and
                validation_results["embeddings_exists"] and
                len(validation_results["validation_errors"]) == 0 and
                validation_results["total_documents"] > 0
        )

    except Exception as e:
        validation_results["validation_errors"].append(f"Validation failed: {e}")
        validation_results["overall_valid"] = False

    return validation_results


# 데이터 통계
def get_data_statistics() -> Dict[str, Any]:
    """데이터 통계 정보를 반환합니다."""
    stats: Dict[str, Any] = {
        "total_files": 0,
        "total_documents": 0,
        "file_details": {},
        "data_size_mb": 0.0
    }

    try:
        datasets = get_available_datasets()
        stats["total_files"] = len(datasets)

        for dataset in datasets:
            try:
                data: Dict[str, Any] = load_knowledge_data(dataset)
                # Dict 형태이므로 sections의 개수를 세어봄
                sections: List[Dict[str, Any]] = data.get('sections', [])
                doc_count: int = len(sections)
                stats["total_documents"] += doc_count

                file_path = KNOWLEDGE_BASE_PATH / dataset
                file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                stats["data_size_mb"] += file_size

                stats["file_details"][dataset] = {
                    "documents": doc_count,
                    "size_mb": round(file_size, 2)
                }

            except Exception as e:
                stats["file_details"][dataset] = {"error": str(e)}

        stats["data_size_mb"] = round(stats["data_size_mb"], 2)

    except Exception as e:
        stats["error"] = str(e)

    return stats


# 초기화 시 데이터 구조 검증
try:
    validation_result = validate_data_structure()
    if not validation_result["overall_valid"]:
        import warnings

        warnings.warn(f"Data validation failed: {validation_result['validation_errors']}")
except Exception:
    import warnings

    warnings.warn("Data package initialization failed")