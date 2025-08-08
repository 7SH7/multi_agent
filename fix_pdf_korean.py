#!/usr/bin/env python3
"""PDF 한글 문제 자동 수정 도구"""

import os
import sys

def fix_pdf_korean_issues():
    """PDF 한글 문제 자동 수정"""
    
    print("🔧 PDF 한글 문제 자동 수정 시작...")
    
    # 1. 환경변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LC_ALL'] = 'ko_KR.UTF-8'
    os.environ['LANG'] = 'ko_KR.UTF-8'
    
    # 2. sys 기본 인코딩 확인
    if sys.getdefaultencoding() != 'utf-8':
        print("⚠️ 시스템 기본 인코딩이 UTF-8이 아닙니다")
    
    # 3. 로케일 설정 (Windows)
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'Korean_Korea.utf8')
        print("✅ 로케일 설정 완료")
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
            print("✅ 로케일 설정 완료 (Linux/Mac)")
        except:
            print("⚠️ 로케일 설정 실패 - 수동 설정 필요")
    
    print("🎉 자동 수정 완료!")
    
if __name__ == "__main__":
    fix_pdf_korean_issues()
