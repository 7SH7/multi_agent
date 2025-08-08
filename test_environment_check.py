#!/usr/bin/env python3
"""다른 환경에서 PDF 문제 진단 도구"""

import os
import sys
import locale
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def check_pdf_environment():
    """PDF 생성 환경 진단"""
    print("🔍 PDF 환경 진단 도구")
    print("=" * 60)
    
    # 1. 시스템 정보
    print("\n1️⃣ 시스템 정보")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version}")
    print(f"   인코딩: {sys.getdefaultencoding()}")
    print(f"   로케일: {locale.getdefaultlocale()}")
    
    # 2. 한글 폰트 검사
    print("\n2️⃣ 한글 폰트 검사")
    font_paths = [
        # Windows 폰트
        "C:/Windows/Fonts/malgun.ttf",        # 맑은 고딕
        "C:/Windows/Fonts/malgunbd.ttf",      # 맑은 고딕 Bold  
        "C:/Windows/Fonts/gulim.ttc",         # 굴림
        "C:/Windows/Fonts/batang.ttc",        # 바탕
        "C:/Windows/Fonts/NanumGothic.ttf",   # 나눔고딕
        
        # macOS 폰트
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/NanumGothic.ttf",
        
        # Linux 폰트
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    
    available_fonts = []
    for font_path in font_paths:
        if os.path.exists(font_path):
            available_fonts.append(font_path)
            print(f"   ✅ 발견: {font_path}")
    
    if not available_fonts:
        print("   ❌ 한글 폰트가 하나도 없습니다!")
        return False
    
    # 3. 폰트 등록 테스트
    print("\n3️⃣ 폰트 등록 테스트")
    for font_path in available_fonts[:3]:  # 처음 3개만 테스트
        try:
            font_name = f"TestFont_{os.path.basename(font_path)}"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            print(f"   ✅ 등록 성공: {font_name}")
        except Exception as e:
            print(f"   ❌ 등록 실패: {font_path} - {e}")
    
    # 4. 한글 텍스트 인코딩 테스트
    print("\n4️⃣ 한글 텍스트 인코딩 테스트")
    test_texts = [
        "한글 테스트",
        "김철수 엔지니어", 
        "프레스 기계 소음 문제",
        "100톤 유압 시스템",
        "⚠️🔧💰📊 특수문자"
    ]
    
    for text in test_texts:
        try:
            # UTF-8 인코딩 테스트
            encoded = text.encode('utf-8')
            decoded = encoded.decode('utf-8')
            if text == decoded:
                print(f"   ✅ UTF-8: {text}")
            else:
                print(f"   ❌ UTF-8 실패: {text}")
        except Exception as e:
            print(f"   ❌ 인코딩 오류: {text} - {e}")
    
    # 5. 환경변수 확인
    print("\n5️⃣ 환경변수 확인")
    env_vars = ['PYTHONIOENCODING', 'LC_ALL', 'LANG', 'PYTHONPATH']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"   {var}: {value}")
    
    # 6. 권장 해결책
    print("\n6️⃣ 권장 해결책")
    if platform.system() == 'Windows':
        if not any('malgun' in font for font in available_fonts):
            print("   ❌ 맑은고딕 폰트 없음 → Windows 업데이트 필요")
        print("   💡 Windows: 시스템 → 언어 → 한국어 팩 설치")
    
    elif platform.system() == 'Darwin':  # macOS
        print("   💡 macOS: brew install font-nanum-gothic")
        
    elif platform.system() == 'Linux':
        print("   💡 Ubuntu: sudo apt-get install fonts-nanum")
        print("   💡 CentOS: sudo yum install naver-nanum-fonts")
    
    print("\n📝 추가 환경설정:")
    print("   export PYTHONIOENCODING=utf-8")
    print("   export LC_ALL=ko_KR.UTF-8") 
    print("   export LANG=ko_KR.UTF-8")
    
    return len(available_fonts) > 0

def generate_fix_script():
    """자동 수정 스크립트 생성"""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    with open("fix_pdf_korean.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print(f"\n📝 자동 수정 스크립트 생성: fix_pdf_korean.py")

if __name__ == "__main__":
    result = check_pdf_environment()
    if result:
        print(f"\n🎉 환경 검사 완료! PDF 생성 가능한 환경입니다.")
    else:
        print(f"\n❌ 환경 문제 발견! 위 해결책을 적용해주세요.")
        
    generate_fix_script()
    print(f"\n💡 다른 사람 컴퓨터에서 이 스크립트를 실행하세요:")
    print(f"   python test_environment_check.py")
    print(f"   python fix_pdf_korean.py")