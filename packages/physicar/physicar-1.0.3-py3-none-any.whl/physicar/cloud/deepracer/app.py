from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import os
import re
import yaml
import json
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import aiohttp
import pytz

# 설정
from physicar.cloud.deepracer.config import (
    SUPPORTED_LANGUAGES, SUPPORTED_TIMEZONES,
    DEFAULT_LANG, DEFAULT_TZ, SECRET_KEY,
    TRACKS_INFO_PATH, USER_INPUT_LIMITS, 
    get_max_sub_simulation_count,
    STREAM_QUALITY,
)

# 스키마
from physicar.cloud.deepracer import schemas
from physicar.cloud.deepracer.schemas import CreateModelRequest, CloneModelRequest

# 파일 생성
from physicar.cloud.deepracer.drfc_writer import create_model_files, validate_model_name_available

# 작업 관리
from physicar.cloud.deepracer import jobs

# 다국어 지원
from physicar.cloud.deepracer.i18n import create_gettext, load_translations

# 경로 설정
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# MinIO 설정
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "physicar"
MINIO_SECRET_KEY = "physicar"
MINIO_BUCKET = "bucket"


def _get_minio_client():
    """MinIO 클라이언트 생성"""
    from minio import Minio
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)


def minio_object_exists(key: str) -> bool:
    """MinIO에서 객체 존재 여부 확인"""
    try:
        client = _get_minio_client()
        client.stat_object(MINIO_BUCKET, key)
        return True
    except Exception:
        return False


def minio_prefix_exists(prefix: str) -> bool:
    """MinIO에서 prefix로 시작하는 객체가 있는지 확인"""
    try:
        client = _get_minio_client()
        # list_objects는 iterator 반환, 첫 번째 항목만 확인
        for _ in client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=False):
            return True
        return False
    except Exception:
        return False


def minio_read_text(key: str) -> Optional[str]:
    """MinIO에서 텍스트 파일 읽기"""
    try:
        client = _get_minio_client()
        response = client.get_object(MINIO_BUCKET, key)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        return content
    except Exception:
        return None


def minio_read_json(key: str) -> Optional[dict]:
    """MinIO에서 JSON 파일 읽기"""
    content = minio_read_text(key)
    if content is None:
        return None
    try:
        return json.loads(content)
    except Exception:
        return None


def minio_read_yaml(key: str) -> Optional[dict]:
    """MinIO에서 YAML 파일 읽기"""
    content = minio_read_text(key)
    if content is None:
        return None
    try:
        return yaml.safe_load(content)
    except Exception:
        return None

# static 폴더 없으면 생성
STATIC_DIR.mkdir(exist_ok=True)

# 번역 데이터 로드
load_translations()

# aiohttp 세션
http_session: aiohttp.ClientSession = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_session
    timeout = aiohttp.ClientTimeout(total=None, connect=5)
    http_session = aiohttp.ClientSession(timeout=timeout)
    
    # 백그라운드 훈련 모니터 시작
    from physicar.cloud.deepracer.jobs import start_monitor, stop_monitor
    start_monitor()
    
    yield
    
    # 정리
    stop_monitor()
    await http_session.close()

app = FastAPI(lifespan=lifespan, redirect_slashes=False)

# Session Middleware (쿠키 기반 세션)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static files & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ============ Helper Functions ============

def parse_accept_language(accept_language: str) -> str:
    """Accept-Language 헤더에서 지원되는 언어 추출"""
    if not accept_language:
        return DEFAULT_LANG
    
    # Accept-Language 파싱: "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    languages = []
    for part in accept_language.split(","):
        part = part.strip()
        if ";q=" in part:
            lang, q = part.split(";q=")
            q = float(q)
        else:
            lang = part
            q = 1.0
        # ko-KR -> ko
        lang = lang.split("-")[0].lower()
        languages.append((lang, q))
    
    # 우선순위대로 정렬
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # 지원되는 언어 중 첫 번째 반환
    for lang, _ in languages:
        if lang in SUPPORTED_LANGUAGES:
            return lang
    
    return DEFAULT_LANG

def get_session_lang(request: Request) -> str:
    """세션에서 언어 가져오기 (없으면 브라우저 언어 감지)"""
    if "lang" in request.session:
        return request.session["lang"]
    
    # 브라우저 Accept-Language에서 언어 감지
    accept_language = request.headers.get("accept-language", "")
    detected_lang = parse_accept_language(accept_language)
    
    # 감지된 언어를 세션에 저장
    request.session["lang"] = detected_lang
    
    return detected_lang

def get_session_tz(request: Request) -> str:
    """세션에서 시간대 가져오기"""
    return request.session.get("tz", DEFAULT_TZ)

def get_common_context(request: Request) -> dict:
    """모든 페이지에 공통으로 전달할 컨텍스트"""
    lang = get_session_lang(request)
    return {
        "request": request,
        "lang": lang,
        "tz": get_session_tz(request),
        "supported_languages": SUPPORTED_LANGUAGES,
        "supported_timezones": SUPPORTED_TIMEZONES,
        "_": create_gettext(lang),  # 번역 함수
    }


# ============ Language/Timezone Switch Routes ============

@app.get("/lang/{code}", name="switch_language")
async def switch_language(request: Request, code: str):
    """언어 전환"""
    if code in SUPPORTED_LANGUAGES:
        request.session["lang"] = code
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=302)

@app.get("/tz/{code:path}", name="switch_timezone")
async def switch_timezone(request: Request, code: str):
    """시간대 전환"""
    if code in pytz.all_timezones:
        request.session["tz"] = code
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=302)


# ============ Pages ============

@app.get("/", name="home")
async def home(request: Request):
    """Home page - 임시로 Your Models로 리다이렉션"""
    return RedirectResponse(url="/pages/models/list", status_code=302)


@app.get("/pages/{name:path}", response_class=HTMLResponse, name="pages")
async def pages(request: Request, name: str):
    """Dynamic page routing"""
    template_path = f"pages/{name}.html"
    context = get_common_context(request)
    context.update({
        "title": name.replace("_", " ").title(),
        "user": None,
        "current_page": name,
    })
    
    # models/create 페이지 전용 컨텍스트
    if name == "models/create":
        # tracks_info 로드
        if TRACKS_INFO_PATH.exists():
            with open(TRACKS_INFO_PATH, "r") as f:
                tracks_info = yaml.safe_load(f) or {}
            # track_direction을 npy 키에서 추출 (값이 있는 방향만)
            for track_id, info in tracks_info.items():
                if "npy" in info and "track_direction" not in info:
                    # npy 값이 있는 방향만 포함 (None이나 빈 문자열 제외)
                    info["track_direction"] = [
                        direction for direction, npy_file in info["npy"].items()
                        if npy_file  # None이나 빈 문자열이 아닌 경우만
                    ]
        else:
            tracks_info = {}
        
        context.update({
            "tracks_info": tracks_info,
            "max_sub_simulation_count": get_max_sub_simulation_count(),
        })
    
    # models/clone 페이지 전용 컨텍스트 (모델 복제)
    if name == "models/clone":
        from physicar.cloud.deepracer.settings_manager import is_model_clonable
        from physicar.cloud.deepracer.jobs import active_jobs
        
        pretrained_model_name = request.query_params.get("model_name", "")
        
        # model_name 파라미터 필수 체크
        if not pretrained_model_name:
            raise HTTPException(status_code=400, detail="model_name query parameter is required")
        
        # Clone 가능 여부 확인 (존재 + 상태 + 체크포인트)
        clonable, reason = is_model_clonable(pretrained_model_name, active_jobs)
        if not clonable:
            raise HTTPException(status_code=400, detail=reason)
        
        # tracks_info 로드 (create와 동일)
        if TRACKS_INFO_PATH.exists():
            with open(TRACKS_INFO_PATH, "r") as f:
                tracks_info = yaml.safe_load(f) or {}
            for track_id, info in tracks_info.items():
                if "npy" in info and "track_direction" not in info:
                    info["track_direction"] = [
                        direction for direction, npy_file in info["npy"].items()
                        if npy_file
                    ]
        else:
            tracks_info = {}
        
        context.update({
            "tracks_info": tracks_info,
            "max_sub_simulation_count": get_max_sub_simulation_count(),
            "pretrained_model_name": pretrained_model_name,
            "is_clone": True,
            "title": f"Clone Model - {pretrained_model_name}",
        })
    
    # models/model 페이지 전용 컨텍스트 (모델 상세/모니터링)
    if name == "models/model":
        model_name = request.query_params.get("model_name", "")
        context.update({
            "model_name": model_name,
            "title": model_name or "Model",
        })
    
    # models/evaluation 페이지 전용 컨텍스트 (평가 시작)
    if name == "models/evaluation":
        from physicar.cloud.deepracer.settings_manager import get_model_status, get_model_main_simulation_config
        
        model_name = request.query_params.get("model_name", "")
        
        # model_name 파라미터 필수 체크
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name query parameter is required")
        
        # 모델 상태 확인 - ready 상태만 평가 가능
        model_status = get_model_status(model_name)
        if model_status != "ready":
            raise HTTPException(
                status_code=400, 
                detail=f"Model '{model_name}' is not ready for evaluation. Current status: {model_status}"
            )
        
        # tracks_info 로드
        if TRACKS_INFO_PATH.exists():
            with open(TRACKS_INFO_PATH, "r") as f:
                tracks_info = yaml.safe_load(f) or {}
            for track_id, info in tracks_info.items():
                if "npy" in info and "track_direction" not in info:
                    info["track_direction"] = [
                        direction for direction, npy_file in info["npy"].items()
                        if npy_file
                    ]
        else:
            tracks_info = {}
        
        # 모델의 main 시뮬레이션 설정 가져오기 (기본값으로 사용)
        main_sim_config = get_model_main_simulation_config(model_name)
        
        context.update({
            "model_name": model_name,
            "tracks_info": tracks_info,
            "main_simulation": main_sim_config,
            "title": f"Evaluate Model - {model_name}",
        })
    
    return templates.TemplateResponse(template_path, context)


# ============ API Endpoints ============

@app.get("/api/tracks", name="api_tracks")
async def api_tracks():
    """트랙 목록 API"""
    if not TRACKS_INFO_PATH.exists():
        return JSONResponse({"tracks": []})
    
    with open(TRACKS_INFO_PATH, "r") as f:
        tracks_info = yaml.safe_load(f) or {}
    
    tracks = []
    for track_id, info in tracks_info.items():
        tracks.append({
            "id": track_id,
            "name": info.get("name", track_id),
            "length": info.get("length"),
            "width": info.get("width"),
            "directions": list(info.get("npy", {}).keys()),
            "thumbnail": f"/static/tracks/thumbnail/{track_id}.png",
        })
    
    return JSONResponse({"tracks": tracks})


@app.get("/api/models", name="api_models_list")
async def api_models_list():
    """모델 목록 API"""
    from physicar.cloud.deepracer.settings_manager import get_model_list
    from physicar.cloud.deepracer.jobs import active_jobs
    
    models = get_model_list(active_jobs)
    return JSONResponse({
        "models": models,
        "total": len(models),
    })


@app.get("/api/config/limits", name="api_config_limits")
async def api_config_limits():
    """사용자 입력 제한 및 옵션 API"""
    return JSONResponse({
        "limits": USER_INPUT_LIMITS,
        "max_sub_simulations": get_max_sub_simulation_count(),
    })


# ============ 설정 로드/저장 API ============

@app.get("/api/settings", name="api_settings_load")
async def api_settings_load():
    """모든 설정 로드 API"""
    from physicar.cloud.deepracer.settings_manager import load_settings
    settings = load_settings()
    return JSONResponse(settings)


@app.post("/api/settings/simulation/main", name="api_settings_simulation_main")
async def api_settings_simulation_main(request: Request):
    """메인 시뮬레이션 설정 저장 API"""
    from physicar.cloud.deepracer.settings_manager import save_simulation_main
    data = await request.json()
    save_simulation_main(data)
    return JSONResponse({"status": "ok"})


@app.post("/api/settings/simulation/sub/{index}", name="api_settings_simulation_sub")
async def api_settings_simulation_sub(index: int, request: Request):
    """서브 시뮬레이션 설정 저장 API"""
    from physicar.cloud.deepracer.settings_manager import save_simulation_sub
    data = await request.json()
    save_simulation_sub(index, data)
    return JSONResponse({"status": "ok"})


@app.post("/api/settings/simulation/count", name="api_settings_simulation_count")
async def api_settings_simulation_count(request: Request):
    """서브 시뮬레이션 수 설정 API"""
    from physicar.cloud.deepracer.settings_manager import save_sub_simulation_count
    data = await request.json()
    count = data.get("count", 0)
    save_sub_simulation_count(count)
    return JSONResponse({"status": "ok"})


@app.post("/api/settings/model-name", name="api_settings_model_name")
async def api_settings_model_name(request: Request):
    """모델명 저장 API (run.env에 저장)"""
    from physicar.cloud.deepracer.settings_manager import save_model_name
    data = await request.json()
    model_name = data.get("model_name", "").strip()
    if model_name:
        save_model_name(model_name)
    return JSONResponse({"status": "ok"})


@app.get("/api/settings/model-name", name="api_get_model_name")
async def api_get_model_name():
    """모델명 조회 API"""
    from physicar.cloud.deepracer.settings_manager import load_model_name
    model_name = load_model_name()
    return JSONResponse({"model_name": model_name})


@app.post("/api/settings/vehicles", name="api_settings_vehicles")
async def api_settings_vehicles(request: Request):
    """차량/액션 스페이스 설정 저장 API"""
    from physicar.cloud.deepracer.settings_manager import save_vehicles_settings
    data = await request.json()
    save_vehicles_settings(data)
    return JSONResponse({"status": "ok"})


@app.post("/api/settings/hyperparameters", name="api_settings_hyperparameters")
async def api_settings_hyperparameters(request: Request):
    """하이퍼파라미터 저장 API"""
    from physicar.cloud.deepracer.settings_manager import save_hyperparameters, load_simulation_settings
    data = await request.json()
    sim_settings = load_simulation_settings()
    sub_sim_count = sim_settings.get("sub_simulation_count", 0)
    save_hyperparameters(data, sub_sim_count)
    return JSONResponse({"status": "ok"})


@app.post("/api/settings/reward-function", name="api_settings_reward_function")
async def api_settings_reward_function(request: Request):
    """보상 함수 저장 API"""
    from physicar.cloud.deepracer.settings_manager import save_reward_function
    data = await request.json()
    code = data.get("code", "")
    save_reward_function(code)
    return JSONResponse({"status": "ok"})


@app.post("/api/reward-function/generate", name="api_generate_reward_function")
async def api_generate_reward_function(request: Request):
    """AI를 사용하여 보상 함수 생성 API (GitHub Models)"""
    import os
    import requests as req
    from physicar.cloud.deepracer.config import REWARD_FUNCTION_SYSTEM_PROMPT
    
    data = await request.json()
    prompt = data.get("prompt", "").strip()
    race_type = data.get("race_type", "TIME_TRIAL")
    
    if not prompt:
        return JSONResponse({
            "status": "error",
            "error": "프롬프트가 비어있습니다."
        }, status_code=400)
    
    # GitHub Models API 호출
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        return JSONResponse({
            "status": "error",
            "error": "GITHUB_TOKEN이 설정되지 않았습니다."
        }, status_code=500)
    
    # 레이스 타입별 컨텍스트
    race_context = ""
    if race_type == "OBJECT_AVOIDANCE":
        race_context = "\nThis is for OBJECT_AVOIDANCE race type, so consider obstacle avoidance using objects_* parameters."
    elif race_type == "HEAD_TO_BOT":
        race_context = "\nThis is for HEAD_TO_BOT race type, consider racing against bot cars using objects_* parameters."
    
    user_message = f"Race type: {race_type}{race_context}\n\nUser request: {prompt}\n\nGenerate a reward function:"
    
    try:
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        # 요청에서 모델 가져오기 (기본값: gpt-4o)
        ai_model = data.get("model", "gpt-4o")
        # 허용된 모델만 사용
        allowed_models = ["gpt-4o", "gpt-4o-mini"]
        if ai_model not in allowed_models:
            ai_model = "gpt-4o"
        
        payload = {
            "model": ai_model,
            "messages": [
                {"role": "system", "content": REWARD_FUNCTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 8000,
            "temperature": 0.7
        }
        
        resp = req.post(url, headers=headers, json=payload, timeout=30)
        
        if resp.status_code != 200:
            return JSONResponse({
                "status": "error",
                "error": f"GitHub Models API 오류: {resp.status_code}"
            }, status_code=500)
        
        result = resp.json()
        content = result["choices"][0]["message"]["content"]
        
        # 코드 블록 추출 (```python ... ``` 형식일 경우)
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        return JSONResponse({
            "status": "success",
            "code": code
        })
        
    except req.exceptions.Timeout:
        return JSONResponse({
            "status": "error",
            "error": "API 요청 시간 초과"
        }, status_code=504)
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": f"오류 발생: {str(e)}"
        }, status_code=500)


@app.post("/api/reward-function/validate", name="api_run_debug_reward_function")
async def api_run_debug_reward_function(request: Request):
    """Reward Function 검증 API - Docker 컨테이너에서 실제 실행하여 검증"""
    from physicar.cloud.deepracer.debug_reward import (
        run_debug_reward_function,
        DebugRewardFunctionError,
    )
    
    try:
        data = await request.json()
        code = data.get("reward_function", "")
        race_type = data.get("race_type", "TT")
        action_space_type = data.get("action_space_type", "discrete")
        
        if not code.strip():
            return JSONResponse({
                "status": "error",
                "error": {
                    "error_type": "EmptyCode",
                    "error_message": "Reward function code is empty",
                    "error_line": None,
                }
            }, status_code=400)
        
        # Docker 컨테이너에서 실행하여 검증
        run_debug_reward_function(
            reward_function_script=code,
            race_type=race_type,
            action_space_type=action_space_type,
        )
        
        return JSONResponse({
            "status": "success",
            "reward_function": code,
        })
    
    except DebugRewardFunctionError as e:
        return JSONResponse({
            "status": "error",
            "error": {
                "error_type": "DebugRewardFunctionError",
                "error_message": str(e).strip(),
                "error_line": e.error_line,
            }
        }, status_code=400)
    
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": {
                "error_type": type(e).__name__,
                "error_message": str(e).strip(),
                "error_line": None,
            }
        }, status_code=400)


@app.get("/api/models/{model_name}/check", name="api_model_check")
async def api_model_check(model_name: str):
    """모델명 중복 체크 API"""
    available, suggestion = validate_model_name_available(model_name)
    return JSONResponse({
        "available": available,
        "model_name": model_name,
        "suggestion": suggestion if not available else None,
    })


@app.get("/api/models/{model_name}/info", name="api_model_info")
async def api_model_info(model_name: str):
    """모델 정보 API - 모델 설정 정보 반환 (MinIO API 사용)"""
    
    # models/ prefix 처리
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    result = {"model_name": model_name}
    
    # 트랙 정보 로드 (track_id -> track_name 변환용) - 로컬 파일 (변경 드묾)
    tracks_info = {}
    if TRACKS_INFO_PATH.exists():
        with open(TRACKS_INFO_PATH) as f:
            tracks_info = yaml.safe_load(f) or {}
    
    def get_track_display_info(world_name: str):
        """WORLD_NAME에서 track display name, thumbnail, direction 추출"""
        # 2024_reinvent_champ_cw -> track_id: 2024_reinvent_champ, direction: clockwise
        direction = None
        if world_name.endswith('_cw'):
            track_id = world_name[:-3]
            direction = "clockwise"
        elif world_name.endswith('_ccw'):
            track_id = world_name[:-4]
            direction = "counterclockwise"
        else:
            track_id = world_name
            # _cw/_ccw가 없으면 tracks_info의 npy에서 지원하는 방향 확인
            track_info = tracks_info.get(track_id, {})
            npy_info = track_info.get("npy", {})
            if npy_info:
                # clockwise 우선, 없으면 counterclockwise
                if "clockwise" in npy_info and npy_info["clockwise"]:
                    direction = "clockwise"
                elif "counterclockwise" in npy_info and npy_info["counterclockwise"]:
                    direction = "counterclockwise"
        
        track_info = tracks_info.get(track_id, {})
        return {
            "track_id": track_id,
            "track_name": track_info.get("track_name", world_name),
            "thumbnail": track_info.get("thumbnail", ""),
            "direction": direction or "clockwise",
        }
    
    def parse_simulation_from_params(params: dict):
        """training-params에서 simulation 정보 추출"""
        world_name = params.get("WORLD_NAME", "")
        track_info = get_track_display_info(world_name)
        
        # randomize 여부
        randomize = params.get("RANDOMIZE_OBSTACLE_LOCATIONS", "False") == "True"
        
        # OBJECT_POSITIONS 파싱 (randomize가 false일 때만)
        object_positions = []
        if not randomize:
            raw_positions = params.get("OBJECT_POSITIONS", [])
            if isinstance(raw_positions, list):
                for pos in raw_positions:
                    if isinstance(pos, str) and ',' in pos:
                        parts = pos.split(',')
                        if len(parts) == 2:
                            progress = float(parts[0])  # 0.2 그대로 (JS에서 * 100)
                            lane = 1 if parts[1].strip() == "1" else -1
                            object_positions.append({"progress": progress, "lane": lane})
        
        return {
            "track_id": track_info["track_id"],
            "track_name": track_info["track_name"],
            "thumbnail": track_info["thumbnail"],
            "direction": track_info["direction"],
            "alternate_direction": params.get("ALTERNATE_DRIVING_DIRECTION", "False") == "True",
            "race_type": params.get("RACE_TYPE", "TIME_TRIAL"),
            "obstacle_type": params.get("OBSTACLE_TYPE", ""),
            "number_of_obstacles": int(params.get("NUMBER_OF_OBSTACLES", 0)),
            "randomize_obstacles": randomize,
            "object_positions": object_positions,
        }
    
    # 모든 시뮬레이션 정보 로드 (main + sub1~6) - MinIO API 사용
    # 파일명 패턴:
    #   - training-params/main.yaml (main)
    #   - training-params/sub1.yaml ~ training-params/sub6.yaml (sub)
    simulations = {}
    
    # Main simulation - training-params/main.yaml
    main_params = minio_read_yaml(f"models/{model_name}/training-params/main.yaml")
    
    if main_params:
        simulations["main"] = parse_simulation_from_params(main_params)
        result["best_model_metric"] = main_params.get("BEST_MODEL_METRIC", "reward")
        result["vehicle"] = {
            "body_shell_type": main_params.get("BODY_SHELL_TYPE", "deepracer"),
        }
    
    # Sub simulations - training-params/sub1.yaml ~ training-params/sub6.yaml
    for i in range(1, 7):
        sub_params = minio_read_yaml(f"models/{model_name}/training-params/sub{i}.yaml")
        if sub_params:
            simulations[f"sub{i}"] = parse_simulation_from_params(sub_params)
    
    result["simulations"] = simulations
    result["sub_simulation_count"] = len(simulations) - 1 if "main" in simulations else 0
    
    # models/{model}/model/model_metadata.json - vehicle, action_space (MinIO API)
    # 없으면 custom_files/model_metadata.json fallback
    mm_key = f"models/{model_name}/model/model_metadata.json"
    model_metadata = minio_read_json(mm_key)
    if not model_metadata:
        model_metadata = minio_read_json("custom_files/model_metadata.json")
    
    if model_metadata:
        # Vehicle 정보 업데이트
        if "vehicle" not in result:
            result["vehicle"] = {}
        # vehicle_type은 training-params.yaml의 BODY_SHELL_TYPE에서 이미 읽음 (body_shell_type)
        # metadata.json에서는 저장하지 않으므로 읽지 않음
        if "body_shell_type" in result.get("vehicle", {}):
            result["vehicle"]["vehicle_type"] = result["vehicle"]["body_shell_type"]
        result["vehicle"]["sensor"] = model_metadata.get("sensor", ["FRONT_FACING_CAMERA"])
        result["vehicle"]["action_space_type"] = model_metadata.get("action_space_type", "discrete")
        result["vehicle"]["action_space"] = model_metadata.get("action_space", [])
        result["max_training_time"] = model_metadata.get("max_training_time")
    
    # models/{model}/ip/hyperparameters.json (MinIO API)
    # 없으면 custom_files/hyperparameters.json fallback
    hp_key = f"models/{model_name}/ip/hyperparameters.json"
    hyperparameters = minio_read_json(hp_key)
    if not hyperparameters:
        hyperparameters = minio_read_json("custom_files/hyperparameters.json")
    if hyperparameters:
        result["hyperparameters"] = hyperparameters
    
    # reward_function.py (MinIO API)
    rf_key = f"models/{model_name}/reward_function.py"
    reward_function = minio_read_text(rf_key)
    if reward_function:
        result["reward_function"] = reward_function
    
    return JSONResponse(result)


# ============ Model Monitoring APIs ============

def get_training_time_from_minio(model_name: str) -> Optional[dict]:
    """
    MinIO에서 모델 폴더의 첫 번째/마지막 파일 시간으로 훈련 시간 계산
    Returns: {"start_time": datetime, "end_time": datetime, "elapsed_seconds": float} or None
    """
    try:
        from datetime import datetime, timezone
        
        client = _get_minio_client()
        
        objects = list(client.list_objects(MINIO_BUCKET, prefix=f'models/{model_name}/', recursive=True))
        if not objects:
            return None
        
        sorted_objs = sorted(objects, key=lambda x: x.last_modified)
        first = sorted_objs[0]
        last = sorted_objs[-1]
        
        elapsed = (last.last_modified - first.last_modified).total_seconds()
        
        return {
            "start_time": first.last_modified,
            "end_time": last.last_modified,
            "elapsed_seconds": elapsed
        }
    except Exception as e:
        print(f"MinIO training time error: {e}")
        return None

def get_max_training_time_from_metadata(model_name: str) -> int | None:
    """model_metadata.json에서 max_training_time(분) 가져오기 (MinIO API)
    
    1. models/{model}/model/model_metadata.json 확인 (훈련 후)
    2. custom_files/model_metadata.json 확인 (훈련 전)
    3. 둘 다 없으면 None 반환
    """
    # 먼저 모델별 metadata 확인
    key = f"models/{model_name}/model/model_metadata.json"
    data = minio_read_json(key)
    if data and "max_training_time" in data:
        return data["max_training_time"]
    
    # 없으면 custom_files 확인
    data = minio_read_json("custom_files/model_metadata.json")
    if data and "max_training_time" in data:
        return data["max_training_time"]
    
    return None

@app.get("/api/models/{model_name}/status", name="api_model_status")
async def api_model_status(model_name: str):
    """
    모델 상태 API - Docker 기반 훈련/평가 상태 확인 (MinIO API 사용)
    
    status 값:
    - training: 훈련 중
    - evaluating: 평가 중
    - stopping: 정지 중
    - ready: 준비됨 (체크포인트 있음)
    - failed: 실패 (체크포인트 없음)
    """
    from physicar.cloud.deepracer.jobs import (
        get_training_status, get_run_id_by_model_name, get_job, JobType
    )
    
    # models/ prefix가 있으면 제거
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    # MinIO에서 훈련 시간 정보 가져오기
    minio_time = get_training_time_from_minio(model_name)
    training_time_seconds = minio_time["elapsed_seconds"] if minio_time else None
    max_training_time_minutes = get_max_training_time_from_metadata(model_name)
    
    # Docker에서 훈련 상태 확인
    run_id = get_run_id_by_model_name(model_name)
    
    if run_id is not None:
        status_info = get_training_status(run_id)
        docker_status = status_info.get("status", "unknown")
        
        # 작업 유형 확인 (training vs evaluation)
        job = get_job(run_id)
        job_type = job.job_type if job else None
        
        # status 매핑: docker_status → 우리 status
        if docker_status == "running":
            if job_type == JobType.EVALUATION:
                status = "evaluating"
            else:
                status = "training"
        else:
            # failed, stopped, stopping, error 등 → training (정지 중에도 training 유지)
            if job_type == JobType.EVALUATION:
                status = "evaluating"
            else:
                status = "training"
        
        # 훈련 중: MinIO에서 실시간 경과 시간 계산
        should_stop = False
        elapsed_seconds = None
        started_at = None
        
        if minio_time:
            from datetime import datetime, timezone
            started_at = minio_time["start_time"].isoformat()
            # 현재 시간과 시작 시간으로 경과 시간 계산
            now_dt = datetime.now(timezone.utc)
            elapsed_seconds = (now_dt - minio_time["start_time"]).total_seconds()
            
            # 자동 중지 필요 여부만 반환 (훈련 중일 때만)
            if status == "training" and max_training_time_minutes:
                elapsed_minutes = elapsed_seconds / 60
                if elapsed_minutes >= max_training_time_minutes:
                    should_stop = True
        
        return JSONResponse({
            "model_name": model_name,
            "status": status,
            "run_id": run_id,
            "is_training": status == "training",
            "is_evaluating": status == "evaluating",
            "robomaker_running": status_info.get("robomaker_running", 0),
            "containers": status_info.get("containers", []),
            "started_at": started_at,
            "elapsed_seconds": elapsed_seconds,
            "training_time_seconds": training_time_seconds,
            "max_training_time_minutes": max_training_time_minutes,
            "should_stop": should_stop,
        })
    else:
        # 훈련 중이 아님 - 체크포인트 존재 여부로 ready/failed 판단
        checkpoints = minio_read_json(f"models/{model_name}/model/deepracer_checkpoints.json")
        has_checkpoints = bool(checkpoints and checkpoints.get("best_checkpoint"))
        
        return JSONResponse({
            "model_name": model_name,
            "status": "ready" if has_checkpoints else "failed",
            "run_id": None,
            "is_training": False,
            "is_evaluating": False,
            "training_time_seconds": training_time_seconds,
            "max_training_time_minutes": max_training_time_minutes,
        })


@app.get("/api/models/{model_name}/training/metrics", name="api_model_training_metrics")
async def api_model_training_metrics(model_name: str, worker: int = 0):
    """
    훈련 메트릭 API - TrainingMetrics.json 반환 (MinIO API 사용)
    
    Args:
        model_name: 모델 이름
        worker: 워커 번호 (0=main, 1=sub1, ...)
    """
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    # training-metrics/main.json or training-metrics/sub1.json (MinIO API)
    worker_name = 'main' if worker == 0 else f'sub{worker}'
    metrics_key = f"models/{model_name}/training-metrics/{worker_name}.json"
    
    data = minio_read_json(metrics_key)
    if not data:
        return JSONResponse({
            "model_name": model_name,
            "worker": worker,
            "metrics": [],
            "exists": False,
            "best_model_metric": "reward",
            "num_episodes_between_training": 10,
        })
    
    try:
        # config.training.yml에서 num_episodes_between_training 가져오기 (MinIO API)
        num_episodes_between_training = 10
        config_key = f"models/{model_name}/config.training.yml"
        config_data = minio_read_yaml(config_key)
        if config_data and 'training' in config_data:
            num_episodes_between_training = config_data['training'].get('num_episodes_between_training', 10)
        
        return JSONResponse({
            "model_name": model_name,
            "worker": worker,
            "metrics": data.get("metrics", []),
            "exists": True,
            "best_model_metric": data.get("best_model_metric", "reward"),
            "num_episodes_between_training": num_episodes_between_training,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read metrics: {str(e)}")


@app.get("/api/models/{model_name}/training/config", name="api_model_training_config")
async def api_model_training_config(model_name: str, worker: int = 1):
    """
    훈련 설정 API - training-params/{worker}.yaml 반환 (MinIO API 사용)
    """
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    # training-params/{worker_name}.yaml (MinIO API)
    worker_name = 'main' if worker == 1 else f'sub{worker-1}'
    config_key = f"models/{model_name}/training-params/{worker_name}.yaml"
    config = minio_read_yaml(config_key)
    
    if not config:
        return JSONResponse({
            "model_name": model_name,
            "worker": worker,
            "config": {},
            "exists": False,
        })
    
    return JSONResponse({
        "model_name": model_name,
        "worker": worker,
        "config": config,
        "exists": True,
    })


@app.get("/api/models/{model_name}/reward_function", name="api_model_reward_function")
async def api_model_reward_function(model_name: str):
    """보상 함수 API (MinIO API 사용)"""
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    rf_key = f"models/{model_name}/reward_function.py"
    content = minio_read_text(rf_key)
    
    if not content:
        return JSONResponse({
            "model_name": model_name,
            "content": "",
            "exists": False,
        })
    
    return JSONResponse({
        "model_name": model_name,
        "content": content,
        "exists": True,
    })


@app.get("/api/models/{model_name}/clone-config", name="api_model_clone_config")
async def api_model_clone_config(model_name: str):
    """
    Clone 설정 API - 기존 모델 설정을 CreateModelRequest 형태로 반환
    
    training-params/*.yaml, model/model_metadata.json, reward_function.py 조합
    """
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    # 1. main 훈련 설정 로드
    main_config = minio_read_yaml(f"models/{model_name}/training-params/main.yaml") or {}
    
    # 2. sub 시뮬레이션 설정 로드 (sub1~sub6)
    sub_configs = []
    for i in range(1, 7):
        sub_config = minio_read_yaml(f"models/{model_name}/training-params/sub{i}.yaml")
        if sub_config:
            sub_configs.append(sub_config)
    
    # 3. model_metadata.json 로드
    model_metadata = minio_read_json(f"models/{model_name}/model/model_metadata.json") or {}
    
    # 4. hyperparameters.json 로드 (모델 전용 → custom_files 폴백)
    hyperparams = minio_read_json(f"models/{model_name}/ip/hyperparameters.json") or minio_read_json(f"custom_files/hyperparameters.json") or {}
    
    # 5. reward_function.py 로드
    reward_function = minio_read_text(f"models/{model_name}/reward_function.py") or ""
    
    # 6. 응답 구성
    def extract_simulation(config: dict) -> dict:
        """training-params/*.yaml에서 시뮬레이션 설정 추출"""
        sim = {
            "track_id": config.get("WORLD_NAME", "reInvent2019_wide").replace("_cw", "").replace("_ccw", ""),
            "direction": "clockwise" if "_cw" in config.get("WORLD_NAME", "") else "counterclockwise",
            "alternate_direction": config.get("ALTERNATE_DRIVING_DIRECTION", False),
            "race_type": config.get("RACE_TYPE", "TIME_TRIAL"),
        }
        
        # Object Avoidance 설정
        if sim["race_type"] == "OBJECT_AVOIDANCE":
            sim["object_avoidance"] = {
                "object_type": config.get("OBJECT_TYPE", "box_obstacle"),
                "number_of_obstacles": config.get("NUMBER_OF_OBSTACLES", 3),
                "randomize_locations": config.get("RANDOMIZE_OBSTACLE_LOCATIONS", True),
            }
            # 고정 위치가 있으면 추가
            object_positions = config.get("OBJECT_POSITIONS")
            if object_positions and not sim["object_avoidance"]["randomize_locations"]:
                positions = []
                for pos in object_positions.split(";"):
                    if "," in pos:
                        progress, lane = pos.split(",")
                        positions.append({
                            "progress": float(progress) * 100,
                            "lane": "inside" if int(lane) == 1 else "outside"
                        })
                sim["object_avoidance"]["object_positions"] = positions
        
        return sim
    
    # 메인 시뮬레이션
    main_sim = extract_simulation(main_config)
    
    # 서브 시뮬레이션
    sub_sims = [extract_simulation(sc) for sc in sub_configs]
    
    # 차량 설정
    sensors = model_metadata.get("sensor", ["FRONT_FACING_CAMERA"])
    action_space = model_metadata.get("action_space", [])
    
    vehicle = {
        "vehicle_type": "deepracer",  # TODO: 메타데이터에서 추출
        "lidar": "SECTOR_LIDAR" in sensors,
        "action_space": [
            {"steering_angle": int(a.get("steering_angle", 0)), "speed": float(a.get("speed", 1.0))}
            for a in action_space
        ] if action_space else None,
    }
    
    # 하이퍼파라미터
    hyperparameters = {
        "batch_size": hyperparams.get("batch_size", 64),
        "discount_factor": hyperparams.get("discount_factor", 0.999),
        "learning_rate": hyperparams.get("lr", 0.0003),
        "loss_type": hyperparams.get("loss_type", "huber"),
        "entropy": hyperparams.get("beta_entropy", 0.01),
    }
    
    # 훈련 설정
    training = {
        "best_model_metric": main_config.get("BEST_MODEL_METRIC", "progress"),
        "hyperparameters": hyperparameters,
    }
    
    return JSONResponse({
        "model_name": model_name,
        "simulation": main_sim,
        "sub_simulations": sub_sims,
        "sub_simulation_count": len(sub_configs),
        "vehicle": vehicle,
        "training": training,
        "reward_function": reward_function,
    })


@app.get("/api/models/{model_name}/download/physical-car-model/{model_type}", name="api_model_download_physical_car_model")
async def api_model_download_physical_car_model(model_name: str, model_type: str):
    """
    Physical Car Model 다운로드 API
    
    Args:
        model_name: 모델 이름
        model_type: 'best' 또는 'last'
    
    Returns:
        StreamingResponse로 tar.gz 파일 스트리밍
        파일명: {model_name}-{model_type}.tar.gz
    """
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    # model_type 유효성 검사
    if model_type not in ("best", "last"):
        raise HTTPException(status_code=400, detail="model_type must be 'best' or 'last'")
    
    # S3 키
    s3_key = f"models/{model_name}/physical-car-model/{model_type}.tar.gz"
    
    # 파일 존재 확인
    if not minio_object_exists(s3_key):
        raise HTTPException(
            status_code=404, 
            detail=f"Physical car model '{model_type}.tar.gz' not found for model '{model_name}'"
        )
    
    # MinIO에서 파일 스트리밍
    try:
        client = _get_minio_client()
        response = client.get_object(MINIO_BUCKET, s3_key)
        
        # 파일 크기 가져오기
        stat = client.stat_object(MINIO_BUCKET, s3_key)
        file_size = stat.size
        
        # 다운로드 파일명 생성 (모델명-타입.tar.gz)
        download_filename = f"{model_name}-{model_type}.tar.gz"
        
        def iter_file():
            try:
                for chunk in response.stream(32 * 1024):  # 32KB chunks
                    yield chunk
            finally:
                response.close()
                response.release_conn()
        
        return StreamingResponse(
            iter_file(),
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(file_size),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@app.get("/api/models/{model_name}/physical-car-model/status", name="api_model_physical_car_status")
async def api_model_physical_car_status(model_name: str):
    """
    Physical Car Model 상태 확인 API
    
    Returns:
        best와 last 파일의 존재 여부
    """
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    best_key = f"models/{model_name}/physical-car-model/best.tar.gz"
    last_key = f"models/{model_name}/physical-car-model/last.tar.gz"
    
    return JSONResponse({
        "model_name": model_name,
        "best_exists": minio_object_exists(best_key),
        "last_exists": minio_object_exists(last_key),
    })


@app.get("/api/models/{model_name}/download/logs", name="api_model_download_logs")
async def api_model_download_logs(model_name: str):
    """
    모델 로그 다운로드 API
    training-logs, training-metrics, training-simtrace, evaluation 폴더를 tar.gz로 압축
    MinIO API 사용 (s3fs 마운트 의존 X)
    """
    import tarfile
    from io import BytesIO
    
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # 압축할 폴더 목록
    folders_to_include = ["training-logs/", "training-metrics/", "training-simtrace/", "evaluation/"]
    
    # MinIO에서 파일 목록 가져오기
    client = _get_minio_client()
    files_to_download = []
    
    for folder in folders_to_include:
        prefix = model_prefix + folder
        try:
            for obj in client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True):
                key = obj.object_name
                # mp4 파일은 용량이 크므로 제외
                if not key.lower().endswith('.mp4'):
                    files_to_download.append(key)
        except Exception:
            pass
    
    if not files_to_download:
        raise HTTPException(status_code=404, detail="No log files found for this model")
    
    # tar.gz 생성 (메모리 효율적으로)
    tar_buffer = BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for s3_key in files_to_download:
            try:
                response = client.get_object(MINIO_BUCKET, s3_key)
                file_data = response.read()
                response.close()
                response.release_conn()
                
                # 상대 경로 계산 (models/{model_name}/ 제거)
                arcname = s3_key[len(model_prefix):]
                
                # tarfile에 추가 (BytesIO 재사용하여 메모리 절약)
                tarinfo = tarfile.TarInfo(name=arcname)
                tarinfo.size = len(file_data)
                tar.addfile(tarinfo, BytesIO(file_data))
                
                # 명시적으로 메모리 해제
                del file_data
            except Exception as e:
                logger.warning(f"Failed to add {s3_key} to archive: {e}")
    
    download_filename = f"{model_name}-logs.tar.gz"
    
    # getbuffer() 사용하여 복사 없이 전송
    tar_buffer.seek(0)
    content = tar_buffer.getvalue()
    tar_buffer.close()  # 원본 버퍼 해제
    
    return Response(
        content=content,
        media_type="application/gzip",
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
        }
    )


@app.delete("/api/models/{model_name}", name="api_model_delete")
async def api_model_delete(model_name: str):
    """
    모델 삭제 API
    - 훈련/평가 중인 모델은 삭제 불가
    - S3(MinIO)에서 모델 폴더 전체 삭제
    """
    from minio.deleteobjects import DeleteObject
    from physicar.cloud.deepracer.jobs import get_run_id_by_model_name, get_active_jobs
    
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    model_prefix = f"models/{model_name}/"
    
    # MinIO에서 모델 존재 여부 확인
    if not minio_prefix_exists(model_prefix):
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    # 훈련/평가 중인지 확인
    run_id = get_run_id_by_model_name(model_name)
    if run_id is not None:
        raise HTTPException(status_code=400, detail="Cannot delete model while training/evaluation is running")
    
    # 활성 작업 중 해당 모델이 있는지 확인
    active_jobs = get_active_jobs()
    for job in active_jobs:
        if job.model_name == model_name:
            raise HTTPException(status_code=400, detail="Cannot delete model while training/evaluation is running")
    
    try:
        # MinIO에서 모든 객체 삭제
        client = _get_minio_client()
        objects_to_delete = [DeleteObject(obj.object_name) for obj in client.list_objects(MINIO_BUCKET, prefix=model_prefix, recursive=True)]
        
        if objects_to_delete:
            errors = list(client.remove_objects(MINIO_BUCKET, objects_to_delete))
            if errors:
                raise Exception(f"Failed to delete some objects: {errors}")
        
        return JSONResponse({
            "success": True,
            "model_name": model_name,
            "message": f"Model '{model_name}' deleted successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@app.get("/api/models/{model_name}/training/view", name="api_model_training_view")
async def api_model_training_view(model_name: str, quality: int = STREAM_QUALITY):
    """
    훈련 뷰 URL API - 실시간 훈련 영상 스트림 URL 반환
    
    프록시를 통해 로컬 ROS 스트림에 접근
    - /proxy/{port}/stream?topic=... 형식으로 제공
    
    Returns:
        - is_training: 컨테이너가 실행 중인지 (Docker 기준)
        - is_complete: 훈련이 확실히 완료되었는지 (run_id 없고 메트릭 있음)
        - streams_ready: 실제 스트림이 준비되었는지 (포트가 할당됨)
        - view_urls: 스트림 URL (streams_ready=true일 때만 유효)
    """
    from physicar.cloud.deepracer.jobs import (
        get_run_id_by_model_name, get_training_status,
        get_robomaker_containers_with_rollout
    )
    
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    # 훈련 중인지 확인 - 해당 모델로 실행 중인 컨테이너가 있으면 training
    run_id = get_run_id_by_model_name(model_name)
    
    if run_id is None:
        # 컨테이너 없음 - 완료 여부는 메트릭 존재 여부로 판단
        # 메트릭이 있으면 완료, 없으면 아직 시작 전이거나 데이터 없음
        metrics_key = f"models/{model_name}/training-metrics/main.json"
        has_metrics = minio_object_exists(metrics_key)
        
        return JSONResponse(
            {
                "model_name": model_name,
                "is_training": False,
                "is_complete": has_metrics,  # 메트릭 있어야 진정한 완료
                "streams_ready": False,
                "view_urls": None,
            },
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    # 훈련 상태 상세 확인
    training_status = get_training_status(run_id)
    
    # Docker에서 robomaker 컨테이너 포트 찾기 (ROLLOUT_IDX 기준 정렬됨)
    view_urls = {}
    streams_ready = False
    
    try:
        # robomaker 컨테이너 목록 조회 (ROLLOUT_IDX 기준 정렬)
        # ⚠️ 컨테이너 이름의 번호(robomaker-1, robomaker-2)는 ROLLOUT_IDX와 무관함!
        containers = get_robomaker_containers_with_rollout(run_id)
        
        for container in containers:
            container_name = container["name"]
            ports_str = container["ports"]
            rollout_idx = container["rollout_idx"]
            
            # 8083, 8084 등 포트 추출
            # 예: "0.0.0.0:8083->8080/tcp"
            import re
            port_match = re.search(r'0\.0\.0\.0:(\d+)->8080/tcp', ports_str)
            if port_match:
                port = int(port_match.group(1))
            else:
                # 포트를 찾지 못하면 스킵
                continue
            
            # main / sub 키 결정 (ROLLOUT_IDX 기반)
            # ROLLOUT_IDX=0 → main, ROLLOUT_IDX=1 → sub1, ROLLOUT_IDX=2 → sub2
            if rollout_idx == 0:
                sim_key = 'main'
            elif rollout_idx == 999:
                # ROLLOUT_IDX를 확인하지 못한 경우 스킵
                continue
            else:
                sim_key = f'sub{rollout_idx}'
            
            # 프록시 URL 생성
            view_urls[sim_key] = {
                'front': f'/proxy/{port}/stream?topic=/racecar/camera/zed/rgb/image_rect_color&quality={quality}',
                'chase': f'/proxy/{port}/stream?topic=/racecar/main_camera/zed/rgb/image_rect_color&quality={quality}',
                'chase_overlay': f'/proxy/{port}/stream?topic=/racecar/deepracer/kvs_stream&quality={quality}',
            }
            streams_ready = True  # 최소 하나의 스트림이 준비됨
        
    except Exception as e:
        print(f"Error getting training view ports: {e}")
    
    return JSONResponse(
        {
            "model_name": model_name,
            "is_training": True,
            "is_complete": False,
            "streams_ready": streams_ready,
            "training_status": training_status.get("status", "unknown"),
            "run_id": run_id,
            "view_urls": view_urls if view_urls else None,
        },
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.post("/api/models/create", name="api_models_create")
async def api_models_create(request: CreateModelRequest):
    """모델 생성 API"""
    try:
        # 모델명 중복 체크
        available, suggestion = validate_model_name_available(request.model_name)
        if not available:
            raise HTTPException(
                status_code=400,
                detail=f"Model name '{request.model_name}' already exists. Suggestion: {suggestion}"
            )
        
        # 파일 생성
        files = create_model_files(request)
        
        return JSONResponse({
            "success": True,
            "model_name": request.model_name,
            "files": {name: str(path) for name, path in files.items()},
            "message": f"Model '{request.model_name}' created successfully",
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Jobs API (Training/Evaluation) ============

@app.get("/api/system/cpu", name="api_system_cpu")
async def api_system_cpu():
    """CPU 상태 API"""
    return JSONResponse(jobs.get_cpu_status())


@app.get("/api/system/storage", name="api_system_storage")
async def api_system_storage():
    """Storage 상태 API (하드디스크 기준)"""
    import shutil
    try:
        # 홈 디렉토리 기준 디스크 사용량
        total, used, free = shutil.disk_usage("/home")
        return JSONResponse({
            "total_gb": round(total / (1024 ** 3)),
            "used_gb": round(used / (1024 ** 3)),
            "free_gb": round(free / (1024 ** 3)),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/jobs", name="api_jobs")
async def api_jobs():
    """활성 작업 목록 API"""
    return JSONResponse(jobs.get_jobs_summary())


@app.post("/api/training/quick-start", name="api_training_quick_start")
async def api_training_quick_start():
    """
    간단한 훈련 시작 API
    - 파라미터 없음
    - 모델명, worker_count, training_minutes 모두 저장된 파일에서 읽음
    """
    from physicar.cloud.deepracer.settings_manager import (
        load_simulation_settings,
        load_vehicles_settings,
        parse_env_file,
        RUN_ENV_PATH,
        SYSTEM_ENV_PATH,
    )
    
    try:
        # 1. run.env에서 모델명 읽기
        run_env = parse_env_file(RUN_ENV_PATH)
        model_prefix = run_env.get("DR_LOCAL_S3_MODEL_PREFIX", "")
        
        # "models/model-name" 형식에서 모델명 추출
        if model_prefix.startswith("models/"):
            model_name = model_prefix[7:]  # "models/" 제거
        else:
            model_name = model_prefix
        
        # 2. 모델명 유효성 검사
        pattern = r"^[a-zA-Z0-9_.-]+$"
        if not model_name or not re.match(pattern, model_name):
            raise HTTPException(
                status_code=400,
                detail="Invalid model name in run.env. Please set a valid model name first."
            )
        
        # 3. 모델명 중복 체크
        available, suggestion = validate_model_name_available(model_name)
        if not available:
            raise HTTPException(
                status_code=400,
                detail=f"Model name '{model_name}' already exists. Suggestion: {suggestion}"
            )
        
        # 4. 저장된 설정에서 worker_count, training_minutes 읽기
        system_env = parse_env_file(SYSTEM_ENV_PATH)
        dr_workers = int(system_env.get("DR_WORKERS", "1"))
        worker_count = dr_workers  # DR_WORKERS = main + sub
        
        vehicle_settings = load_vehicles_settings()
        training_minutes = vehicle_settings.get("max_training_time", 60)
        
        # 5. CPU 사전 체크
        can_start, message, required_cpu = jobs.can_start_job(jobs.JobType.TRAINING, worker_count)
        if not can_start:
            cpu_status = jobs.get_cpu_status()
            raise HTTPException(
                status_code=503,
                detail={
                    "message": message,
                    "required_cpu": required_cpu,
                    "available_cpu": cpu_status["available"],
                    "total_cpu": cpu_status["total"],
                }
            )
        
        # 6. 훈련 시작
        success, message, job_info = await jobs.start_training(
            model_name=model_name,
            worker_count=worker_count,
            training_minutes=training_minutes,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "model_name": model_name,
            "run_id": job_info.run_id,
            "worker_count": worker_count,
            "training_minutes": training_minutes,
            "cpu_usage": job_info.cpu_usage,
            "message": message,
            "redirect_url": f"/pages/models/model?model_name={model_name}",
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/start", name="api_training_start")
async def api_training_start(request: CreateModelRequest):
    """훈련 시작 API (모델 생성 + 훈련 시작)"""
    from physicar.cloud.deepracer.debug_reward import (
        run_debug_reward_function,
        DebugRewardFunctionError,
    )
    
    # DEBUG: API가 받은 데이터 로그
    print("=== API RECEIVED DATA ===")
    print(f"model_name: {request.model_name}")
    print(f"action_space: {[{'steering_angle': a.steering_angle, 'speed': a.speed} for a in request.vehicle.action_space]}")
    print(f"hyperparameters: batch_size={request.training.hyperparameters.batch_size}, "
          f"discount_factor={request.training.hyperparameters.discount_factor}, "
          f"learning_rate={request.training.hyperparameters.learning_rate}, "
          f"loss_type={request.training.hyperparameters.loss_type}, "
          f"entropy={request.training.hyperparameters.entropy}")
    print("=========================")
    
    try:
        # 1. 모델명 중복 체크
        available, suggestion = validate_model_name_available(request.model_name)
        if not available:
            raise HTTPException(
                status_code=400,
                detail=f"Model name '{request.model_name}' already exists. Suggestion: {suggestion}"
            )
        
        # 2. 보상함수 검증 (Docker 기반)
        try:
            race_type = request.simulation.race_type or "TIME_TRIAL"
            # race_type 변환: TIME_TRIAL -> TT, OBJECT_AVOIDANCE -> OA
            race_type_short = "TT" if race_type == "TIME_TRIAL" else "OA" if race_type == "OBJECT_AVOIDANCE" else "TT"
            run_debug_reward_function(
                reward_function_script=request.reward_function,
                race_type=race_type_short,
                action_space_type="discrete",  # 기본값
            )
        except DebugRewardFunctionError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Reward function validation failed: {str(e)}"
            )
        
        # 3. CPU 사전 체크
        worker_count = request.get_worker_count()
        can_start, message, required_cpu = jobs.can_start_job(jobs.JobType.TRAINING, worker_count)
        if not can_start:
            raise HTTPException(status_code=503, detail=message)
        
        # 4. 파일 생성
        files = create_model_files(request)
        
        # 5. 훈련 시작
        training_minutes = request.training.training_time_minutes
        success, message, job_info = await jobs.start_training(
            model_name=request.model_name,
            worker_count=worker_count,
            training_minutes=training_minutes,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "model_name": request.model_name,
            "run_id": job_info.run_id,
            "worker_count": worker_count,
            "training_minutes": training_minutes,
            "cpu_usage": job_info.cpu_usage,
            "message": message,
            "redirect_url": f"/pages/models/model?model_name={request.model_name}",
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/clone", name="api_training_clone")
async def api_training_clone(request: CloneModelRequest):
    """Clone 훈련 시작 API (전체 설정 + pretrained)"""
    from physicar.cloud.deepracer.settings_manager import is_model_clonable
    from physicar.cloud.deepracer.debug_reward import (
        run_debug_reward_function,
        DebugRewardFunctionError,
    )
    
    try:
        # 1. 모델명 중복 체크
        available, suggestion = validate_model_name_available(request.model_name)
        if not available:
            raise HTTPException(
                status_code=400,
                detail=f"Model name '{request.model_name}' already exists. Suggestion: {suggestion}"
            )
        
        # 2. pretrained 모델 Clone 가능 여부 확인
        clonable, reason = is_model_clonable(request.pretrained_model_name, jobs.active_jobs)
        if not clonable:
            raise HTTPException(status_code=400, detail=reason)
        
        # 3. 보상함수 검증 (Docker 기반)
        try:
            race_type = request.simulation.race_type or "TIME_TRIAL"
            race_type_short = "TT" if race_type == "TIME_TRIAL" else "OA" if race_type == "OBJECT_AVOIDANCE" else "TT"
            run_debug_reward_function(
                reward_function_script=request.reward_function,
                race_type=race_type_short,
                action_space_type="discrete",
            )
        except DebugRewardFunctionError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Reward function validation failed: {str(e)}"
            )
        
        # 4. CPU 사전 체크
        worker_count = request.get_worker_count()
        can_start, message, required_cpu = jobs.can_start_job(jobs.JobType.TRAINING, worker_count)
        if not can_start:
            raise HTTPException(status_code=503, detail=message)
        
        # 5. 파일 생성 (CreateModelRequest와 동일)
        files = create_model_files(request)
        
        # 6. 훈련 시작 (pretrained 설정 포함)
        training_minutes = request.training.training_time_minutes
        success, message, job_info = await jobs.start_training(
            model_name=request.model_name,
            worker_count=worker_count,
            training_minutes=training_minutes,
            pretrained_model_name=request.pretrained_model_name,
            pretrained_checkpoint=request.pretrained_checkpoint,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "model_name": request.model_name,
            "pretrained_model_name": request.pretrained_model_name,
            "pretrained_checkpoint": request.pretrained_checkpoint,
            "run_id": job_info.run_id,
            "worker_count": worker_count,
            "training_minutes": training_minutes,
            "cpu_usage": job_info.cpu_usage,
            "message": message,
            "redirect_url": f"/pages/models/model?model_name={request.model_name}",
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/{model_name}/stop", name="api_model_stop")
async def api_model_stop(model_name: str):
    """모델 이름으로 훈련 중지 API"""
    from physicar.cloud.deepracer.jobs import get_run_id_by_model_name
    
    if model_name.startswith("models/"):
        model_name = model_name[7:]
    
    run_id = get_run_id_by_model_name(model_name)
    if run_id is None:
        raise HTTPException(status_code=404, detail=f"No running training found for model '{model_name}'")
    
    try:
        success, message = await jobs.stop_training(run_id)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "model_name": model_name,
            "run_id": run_id,
            "message": message,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/{run_id}/stop", name="api_training_stop")
async def api_training_stop(run_id: int):
    """훈련 중지 API"""
    try:
        success, message = await jobs.stop_training(run_id)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "run_id": run_id,
            "message": message,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluation/start", name="api_evaluation_start")
async def api_evaluation_start(request: schemas.StartEvaluationRequest):
    """평가 시작 API
    
    Request Body:
        model_name: 모델 이름
        simulation: 시뮬레이션 설정 (트랙, 방향, 레이스 타입 등)
        evaluation: 평가 설정 (시도 횟수, 체크포인트, 패널티)
    """
    from physicar.cloud.deepracer.settings_manager import get_model_status
    
    try:
        model_name = request.model_name
        sim = request.simulation
        eval_cfg = request.evaluation
        
        # 모델 상태 확인 - ready 상태만 평가 가능
        model_status = get_model_status(model_name)
        if model_status != "ready":
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_name}' is not ready for evaluation. Current status: {model_status}"
            )
        
        # CPU 사전 체크
        can_start, message, _ = jobs.can_start_job(jobs.JobType.EVALUATION)
        if not can_start:
            raise HTTPException(status_code=503, detail=message)
        
        success, message, job_info = await jobs.start_evaluation(
            model_name=model_name,
            track_name=sim.track_id,
            direction=sim.track_direction,
            race_type=sim.race_type,
            object_avoidance=sim.object_avoidance.model_dump() if sim.object_avoidance else None,
            number_of_trials=eval_cfg.number_of_trials,
            checkpoint=eval_cfg.checkpoint,
            offtrack_penalty=eval_cfg.offtrack_penalty,
            collision_penalty=eval_cfg.collision_penalty,
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "model_name": model_name,
            "run_id": job_info.run_id,
            "redirect_url": f"/pages/models/model?model_name={model_name}#evaluation",
            "message": message,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluation/{run_id}/stop", name="api_evaluation_stop")
async def api_evaluation_stop(run_id: int):
    """평가 중지 API"""
    try:
        success, message = await jobs.stop_evaluation(run_id)
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return JSONResponse({
            "success": True,
            "run_id": run_id,
            "message": message,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_name}/evaluation/status", name="api_evaluation_status")
async def api_evaluation_status(model_name: str, quality: int = STREAM_QUALITY):
    """평가 상태 조회 API - 현재 진행 중인 평가 정보 + 스트림 URL (training/view와 동일 구조)"""
    import re
    import subprocess
    
    try:
        # 1. 먼저 활성 작업에서 찾기
        active_jobs = jobs.get_active_jobs()
        eval_job = None
        for job in active_jobs:
            if job.job_type == jobs.JobType.EVALUATION and job.model_name == model_name:
                eval_job = job
                break
        
        # 2. 활성 작업에 없으면 실행 중인 eval 컨테이너 직접 확인
        run_id = None
        container_name = None
        if eval_job:
            run_id = eval_job.run_id
            container_name = f"deepracer-eval-{run_id}-robomaker-1"
        else:
            # 존재하는 eval 컨테이너 검색 (종료된 것 포함 - docker ps -a)
            # 컨테이너가 완전히 삭제될 때까지 "진행 중"으로 간주
            try:
                result = subprocess.run(
                    ["docker", "ps", "-a", "--format", "{{.Names}}"],
                    capture_output=True, text=True, timeout=5
                )
                for name in result.stdout.strip().split('\n'):
                    if name.startswith('deepracer-eval-') and name.endswith('-robomaker-1'):
                        # 컨테이너의 MODEL_S3_PREFIX로 모델명 확인
                        inspect_result = subprocess.run(
                            ["docker", "inspect", name, "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
                            capture_output=True, text=True, timeout=5
                        )
                        for line in inspect_result.stdout.strip().split('\n'):
                            if line.startswith('MODEL_S3_PREFIX='):
                                prefix = line.split('=', 1)[1]
                                # models/test1 -> test1
                                container_model = prefix.split('/')[-1] if '/' in prefix else prefix
                                if container_model == model_name:
                                    container_name = name
                                    # deepracer-eval-0-robomaker-1 -> 0
                                    match = re.match(r'deepracer-eval-(\d+)-robomaker-1', name)
                                    if match:
                                        run_id = int(match.group(1))
                                    break
                    if container_name:
                        break
            except Exception:
                pass
        
        if not container_name or run_id is None:
            return JSONResponse({
                "running": False,
                "model_name": model_name,
            })
        
        # 컨테이너가 실행 중인지 확인 (스트림 가능 여부)
        container_running = False
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}", "--filter", f"name={container_name}"],
                capture_output=True, text=True, timeout=5
            )
            container_running = container_name in result.stdout
        except Exception:
            pass
        
        # 평가 컨테이너에서 포트 조회
        stream_url = None
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Ports}}", "--filter", f"name={container_name}"],
                capture_output=True, text=True, timeout=5
            )
            ports_str = result.stdout.strip()
            
            # 포트 추출: "0.0.0.0:8085->8080/tcp"
            port_match = re.search(r'0\.0\.0\.0:(\d+)->8080/tcp', ports_str)
            if port_match:
                port = int(port_match.group(1))
                stream_url = f'/proxy/{port}/stream?topic=/racecar/deepracer/kvs_stream&quality={quality}'
        except Exception:
            pass
        
        return JSONResponse({
            "running": True,
            "model_name": model_name,
            "run_id": run_id,
            "eval_id": eval_job.eval_id if eval_job else None,
            "started_at": eval_job.started_at.isoformat() if eval_job and eval_job.started_at else None,
            "stream_url": stream_url,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_name}/evaluations", name="api_evaluation_list")
async def api_evaluation_list(model_name: str):
    """평가 히스토리 목록 API (MinIO API 사용)"""
    try:
        eval_prefix = f"models/{model_name}/evaluation/"
        client = _get_minio_client()
        
        # 평가 폴더 목록 가져오기 (timestamp 폴더들)
        eval_folders = set()
        for obj in client.list_objects(MINIO_BUCKET, prefix=eval_prefix, recursive=True):
            # models/{model}/evaluation/20260125071646/metrics.json -> 20260125071646
            rel_path = obj.object_name[len(eval_prefix):]
            parts = rel_path.split('/')
            if parts and parts[0].isdigit():
                eval_folders.add(parts[0])
        
        if not eval_folders:
            return JSONResponse({
                "model_name": model_name,
                "evaluations": [],
            })
        
        evaluations = []
        for eval_id in sorted(eval_folders, reverse=True):
            eval_info = {
                "eval_id": eval_id,
                "timestamp": f"{eval_id[:4]}-{eval_id[4:6]}-{eval_id[6:8]} {eval_id[8:10]}:{eval_id[10:12]}:{eval_id[12:14]}",
                "has_params": minio_object_exists(f"{eval_prefix}{eval_id}/evaluation_params.yaml"),
                "has_metrics": minio_object_exists(f"{eval_prefix}{eval_id}/metrics.json"),
                "has_video": minio_object_exists(f"{eval_prefix}{eval_id}/video.mp4"),
                "has_simtrace": minio_object_exists(f"{eval_prefix}{eval_id}/simtrace.csv"),
            }
            
            # 메트릭 상세 정보 포함 (구버전 호환)
            if eval_info["has_metrics"]:
                try:
                    response = client.get_object(MINIO_BUCKET, f"{eval_prefix}{eval_id}/metrics.json")
                    metrics_data = json.loads(response.read().decode('utf-8'))
                    response.close()
                    response.release_conn()
                    
                    if "metrics" in metrics_data and len(metrics_data["metrics"]) > 0:
                        trials = metrics_data["metrics"]
                        eval_info["trial_count"] = len(trials)
                        
                        # 상세 metrics (구버전 호환 형태로 변환)
                        metrics_detail = {
                            "trial": {},
                            "total_lap_time": {},
                            "lap_time": {},
                            "off_track_count": {},
                            "crash_count": {},
                            "trial_status": {},
                        }
                        
                        cumulative_time = 0
                        for i, trial in enumerate(trials):
                            lap_time = trial.get("elapsed_time_in_milliseconds", 0) / 1000
                            cumulative_time += lap_time
                            
                            metrics_detail["trial"][str(i)] = i + 1
                            metrics_detail["lap_time"][str(i)] = lap_time
                            metrics_detail["total_lap_time"][str(i)] = cumulative_time
                            metrics_detail["off_track_count"][str(i)] = trial.get("off_track_count", 0)
                            metrics_detail["crash_count"][str(i)] = trial.get("crash_count", 0)
                            # episode_status: "Lap complete", "In progress", "Off_track", etc.
                            episode_status = trial.get("episode_status", "Unknown")
                            # "Lap complete" -> "Complete" 로 변환
                            if episode_status == "Lap complete":
                                episode_status = "Complete"
                            metrics_detail["trial_status"][str(i)] = episode_status
                        
                        eval_info["metrics"] = metrics_detail
                        
                        # 완주 시간들 계산 (요약용)
                        completion_times = [
                            t.get("elapsed_time_in_milliseconds", 0) / 1000 
                            for t in trials 
                            if t.get("trial_status") == "Complete"
                        ]
                        if completion_times:
                            eval_info["best_time"] = min(completion_times)
                            eval_info["avg_time"] = sum(completion_times) / len(completion_times)
                except:
                    pass
            
            evaluations.append(eval_info)
        
        return JSONResponse({
            "model_name": model_name,
            "evaluations": evaluations,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_name}/evaluation/{eval_id}", name="api_evaluation_detail")
async def api_evaluation_detail(model_name: str, eval_id: str):
    """특정 평가 결과 상세 조회 API (MinIO API 사용)"""
    try:
        eval_prefix = f"models/{model_name}/evaluation/{eval_id}/"
        client = _get_minio_client()
        
        # 평가 폴더 존재 여부 확인
        if not minio_prefix_exists(eval_prefix):
            raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found")
        
        result = {
            "model_name": model_name,
            "eval_id": eval_id,
            "timestamp": f"{eval_id[:4]}-{eval_id[4:6]}-{eval_id[6:8]} {eval_id[8:10]}:{eval_id[10:12]}:{eval_id[12:14]}",
        }
        
        # 메트릭 로드
        metrics_key = f"{eval_prefix}metrics.json"
        if minio_object_exists(metrics_key):
            try:
                response = client.get_object(MINIO_BUCKET, metrics_key)
                result["metrics"] = json.loads(response.read().decode('utf-8'))
                response.close()
                response.release_conn()
            except:
                pass
        
        # simtrace 파일 확인 (단순화된 구조: simtrace.csv)
        if minio_object_exists(f"{eval_prefix}simtrace.csv"):
            result["simtrace_files"] = ["simtrace.csv"]
        
        # video 파일 확인 (단순화된 구조: video.mp4)
        if minio_object_exists(f"{eval_prefix}video.mp4"):
            result["video_files"] = ["video.mp4"]
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/stop-all", name="api_stop_all_jobs")
async def api_stop_all_jobs():
    """모든 작업 중지 API"""
    try:
        results = await jobs.stop_all_jobs()
        return JSONResponse({
            "status": "success",
            "results": results,
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
        }, status_code=500)


@app.post("/api/system/cleanup", name="api_cleanup_containers")
async def api_cleanup_containers():
    """고아 컨테이너 수동 정리 API"""
    try:
        count = await jobs.cleanup_orphaned_containers()
        return JSONResponse({
            "status": "success",
            "cleaned": count,
            "message": f"{count} orphaned containers removed",
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
        }, status_code=500)


# ============ Proxy ============


async def stream_proxy(url: str, method: str, headers: dict, body: bytes):
    """스트리밍 프록시 제너레이터 - 버퍼링 최소화"""
    import asyncio
    try:
        timeout = aiohttp.ClientTimeout(total=None, sock_read=5)  # 5초 동안 데이터 없으면 타임아웃
        async with http_session.request(
            method=method,
            url=url,
            headers=headers,
            data=body if body else None,
            timeout=timeout,
        ) as response:
            # 작은 청크로 읽어서 버퍼링 최소화
            async for chunk in response.content.iter_chunked(8192):
                if chunk:
                    yield chunk
    except asyncio.TimeoutError:
        print(f"Stream timeout: {url}")
    except Exception as e:
        print(f"Stream error: {e}")


@app.api_route("/proxy/{port:int}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/proxy/{port:int}/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/proxy/{port:int}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(port: int, request: Request, path: str = ""):
    """
    /proxy/8080/stream?topic=xxx 
    → http://localhost:8080/stream?topic=xxx 로 프록시
    """
    # 대상 URL 구성
    target_url = f"http://localhost:{port}/{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"
    
    # 요청 헤더 필터링
    headers = {}
    skip_headers = {"host", "content-length", "transfer-encoding", "connection"}
    for key, value in request.headers.items():
        if key.lower() not in skip_headers:
            headers[key] = value
    
    body = await request.body()
    
    try:
        # HEAD 요청인 경우 - 원본 서버의 헤더를 그대로 전달
        if request.method == "HEAD":
            async with http_session.request(
                method="HEAD",
                url=target_url,
                headers=headers,
            ) as resp:
                # 중요한 헤더들 전달 (비디오 재생에 필요)
                response_headers = {}
                for h in ["content-length", "content-type", "accept-ranges", "etag", "last-modified"]:
                    if h in resp.headers:
                        response_headers[h] = resp.headers[h]
                response_headers["Access-Control-Allow-Origin"] = "*"
                
                return Response(
                    content=b"",
                    status_code=resp.status,
                    headers=response_headers,
                )
        
        # GET 요청 - 먼저 content-type 확인 (MJPEG 스트림 여부)
        if request.method == "GET":
            async with http_session.request(
                method="HEAD",
                url=target_url,
                headers=headers,
            ) as head_resp:
                content_type = head_resp.headers.get("content-type", "")
            
            # MJPEG 스트림인 경우 - 스트리밍 응답
            if "multipart/x-mixed-replace" in content_type:
                return StreamingResponse(
                    stream_proxy(target_url, request.method, headers, body),
                    status_code=200,
                    media_type=content_type,
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Access-Control-Allow-Origin": "*",
                    },
                )
        
        # 일반 응답
        async with http_session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body if body else None,
        ) as resp:
            content = await resp.read()
            resp_content_type = resp.headers.get("content-type", "")
            
            # 응답 헤더 구성 (비디오 재생에 필요한 헤더 포함)
            response_headers = {"Access-Control-Allow-Origin": "*"}
            for h in ["accept-ranges", "content-range", "etag", "last-modified"]:
                if h in resp.headers:
                    response_headers[h] = resp.headers[h]
            
            # HTML 응답인 경우 링크 경로 rewrite
            if "text/html" in resp_content_type:
                try:
                    html = content.decode("utf-8")
                    # 절대 경로를 /proxy/{port}/... 로 변환
                    import re
                    base_path = f"/proxy/{port}"
                    # href="/" src="/" action="/"
                    html = re.sub(r'(href|src|action)="/', rf'\1="{base_path}/', html)
                    html = re.sub(r"(href|src|action)='/", rf"\1='{base_path}/", html)
                    content = html.encode("utf-8")
                except:
                    pass
            
            return Response(
                content=content,
                status_code=resp.status,
                media_type=resp_content_type,
                headers=response_headers,
            )
            
    except aiohttp.ClientConnectorError:
        return Response(
            content=f"Cannot connect to localhost:{port}",
            status_code=502,
        )
    except Exception as e:
        return Response(
            content=f"Proxy error: {str(e)}",
            status_code=500,
        )