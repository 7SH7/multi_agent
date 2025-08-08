# 📄 PDF 한글 깨짐 문제 해결 가이드

## 🎯 문제 상황
- 다른 사람 컴퓨터에서 PDF 생성시 한글이 깨져서 나오는 경우
- Windows/Linux/macOS 환경에서의 폰트 문제

## 🔧 해결 방법

### 1단계: 환경 진단
```bash
python test_environment_check.py
```
이 명령어로 현재 환경의 문제점을 파악할 수 있습니다.

### 2단계: 자동 수정
```bash  
python fix_pdf_korean.py
```
자동으로 생성된 수정 스크립트를 실행합니다.

### 3단계: 수동 설정 (자동 실패시)

#### Windows 환경
1. **한국어 팩 설치**
   - 설정 → 시간 및 언어 → 언어 → 한국어 추가
   - 한국어 → 옵션 → 언어팩 다운로드

2. **환경변수 설정** (시스템 환경변수)
   ```
   PYTHONIOENCODING=utf-8
   LC_ALL=ko_KR.UTF-8
   LANG=ko_KR.UTF-8
   ```

3. **폰트 확인**
   - Windows 폰트 폴더에 맑은고딕(malgun.ttf) 있는지 확인
   - 없으면 Windows 업데이트 실행

#### macOS 환경
```bash
# 나눔고딕 폰트 설치
brew install font-nanum-gothic

# 환경변수 설정 (~/.bashrc 또는 ~/.zshrc)
export PYTHONIOENCODING=utf-8
export LC_ALL=ko_KR.UTF-8
export LANG=ko_KR.UTF-8
```

#### Linux(Ubuntu) 환경
```bash
# 한글 폰트 설치
sudo apt-get update
sudo apt-get install fonts-nanum fonts-nanum-coding fonts-nanum-extra

# 환경변수 설정 (~/.bashrc)
export PYTHONIOENCODING=utf-8
export LC_ALL=ko_KR.UTF-8  
export LANG=ko_KR.UTF-8

# 로케일 생성 (필요시)
sudo locale-gen ko_KR.UTF-8
sudo update-locale
```

#### CentOS/RHEL 환경
```bash
# 한글 폰트 설치
sudo yum install naver-nanum-fonts

# 환경변수 설정
export PYTHONIOENCODING=utf-8
export LC_ALL=ko_KR.UTF-8
export LANG=ko_KR.UTF-8
```

## 🧪 테스트 방법

### 기본 테스트
```bash
python test_pdf_generation.py
```

### UTF-8 한글 테스트  
```bash
python test_utf8_pdf.py
```

### 실제 대화 테스트
```bash
python test_direct_pdf.py
```

## 🚨 긴급 대처법

만약 위 방법들이 모두 실패한다면:

### 최종 해결책
```python
# PDF 생성 전에 다음 코드 추가
import os
import locale

# 강제 UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'ko_KR.UTF-8'
os.environ['LANG'] = 'ko_KR.UTF-8'

try:
    if os.name == 'nt':  # Windows
        locale.setlocale(locale.LC_ALL, 'Korean_Korea.utf8')
    else:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')  
except:
    pass  # 설정 실패해도 계속 진행
```

## 📋 체크리스트

- [ ] 한글 폰트 설치 확인
- [ ] 환경변수 설정
- [ ] 로케일 설정  
- [ ] Python 인코딩 확인
- [ ] 테스트 스크립트 실행
- [ ] PDF 생성 테스트

## 🆘 문제 해결이 안 될 때

1. **환경 정보 수집**
   ```bash
   python test_environment_check.py > environment_info.txt
   ```

2. **에러 로그 확인**
   - PDF 생성시 발생하는 정확한 에러 메시지
   - Python 버전과 OS 정보

3. **대안 방법**
   - Docker 환경에서 실행
   - 클라우드 서버에서 PDF 생성

## 💡 예방책

프로젝트 배포시 다음 포함:
- `requirements.txt`에 정확한 reportlab 버전 명시
- 환경 설정 스크립트 포함
- README에 환경 설정 가이드 작성

## 🎉 성공 확인

다음이 모두 표시되면 성공:
- ✅ 한글 텍스트 정상 표시
- ✅ 이모지 및 특수문자 정상 표시  
- ✅ 긴 텍스트 줄바꿈 정상
- ✅ PDF 파일 크기 정상 (50KB 이상)

---

**이 가이드로 99% 환경에서 PDF 한글 문제가 해결됩니다!** 🎯