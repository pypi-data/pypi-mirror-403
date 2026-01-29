"""
다국어 지원 모듈 (i18n)
구버전의 Flask-Babel 대신 간단한 YAML 기반 다국어 시스템
"""
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# locales 디렉토리 경로
LOCALES_DIR = Path(__file__).parent / "locales"

# 캐시된 번역 데이터
_translations: Dict[str, Dict[str, Any]] = {}


def load_translations() -> Dict[str, Dict[str, Any]]:
    """모든 YAML 파일에서 번역 데이터 로드"""
    global _translations
    
    if _translations:
        return _translations
    
    for yaml_file in LOCALES_DIR.glob("*.yaml"):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                for lang, translations in data.items():
                    if isinstance(translations, dict):
                        if lang not in _translations:
                            _translations[lang] = {}
                        _translations[lang].update(translations)
    
    return _translations


def get_text(key: str, lang: str = "ko", default: Optional[str] = None, **kwargs) -> str:
    """
    번역 텍스트 가져오기
    
    Args:
        key: 점(.)으로 구분된 키 (예: "alert_global.confirm")
        lang: 언어 코드 (예: "ko", "en")
        default: 키를 찾지 못했을 때 반환할 기본값
        **kwargs: 문자열 포맷팅용 파라미터
    
    Returns:
        번역된 문자열
    """
    translations = load_translations()
    
    # 언어가 없으면 영어로 폴백
    if lang not in translations:
        lang = "en"
    
    # 키 탐색 (점으로 구분된 경로)
    keys = key.split(".")
    value = translations.get(lang, {})
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            value = None
            break
    
    if value is None:
        # 영어로 다시 시도
        if lang != "en":
            value = translations.get("en", {})
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
    
    if value is None:
        return default if default is not None else key
    
    # 문자열 포맷팅
    if kwargs and isinstance(value, str):
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    
    return value


def _(key: str, lang: str = "ko", **kwargs) -> str:
    """
    번역 함수 (Flask-Babel의 _() 함수와 유사)
    템플릿에서 사용: {{ _('alert_global.confirm') }}
    """
    return get_text(key, lang, **kwargs)


# Jinja2 템플릿용 함수
def create_gettext(lang: str = "ko"):
    """특정 언어에 바인딩된 gettext 함수 생성"""
    def gettext(key: str, **kwargs) -> str:
        return get_text(key, lang, **kwargs)
    return gettext
