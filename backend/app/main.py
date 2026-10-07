"""Glowrithm REST API (FastAPI).

  GET  /api/v1/health        service and model status (public, for monitoring)
  GET  /api/v1/skin-types    skin-type descriptions
  GET  /api/v1/ingredients   ingredient knowledge base, optionally ?skin_type=oily
  POST /api/v1/analyze       multipart form: image (JPEG/PNG), consent=true, age, sex
                             -> skin type, confidence, Grad-CAM heat map, ingredient recommendations
  GET  /app/                 web test build of the app (web/), when GLOWRITHM_SERVE_WEB=1 (default)

Privacy (UU PDP No. 27/2022): a photo is processed only after explicit consent, only in memory
for the duration of the request, and is never written to permanent storage or logged.
"""
from __future__ import annotations

import logging
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from glowrithm_ml.preprocessing import InvalidImageError

from .config import Settings, get_settings
from .inference import InferenceEngine, PhotoQualityError
from .recommender import Recommender
from .schemas import AnalyzeResponse, HealthResponse, IngredientInfo, SkinTypeInfo

API_VERSION = "1.0.0"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("glowrithm.api")
router = APIRouter(prefix="/api/v1")
# Headers for the web test build: camera only for this origin, no inline scripts, no embedding in other sites.
WEB_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                               "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' http: https:; "
                               "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-cache",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.recommender = Recommender.from_file(settings.kb_path)
    app.state.engine, app.state.model_error = None, None
    try:
        app.state.engine = await run_in_threadpool(InferenceEngine.from_settings, settings)
        logger.info("Model ready: %s (demo=%s)", app.state.engine.model_version, app.state.engine.demo)
    except Exception as exc:  # keep serving so /health can report the problem
        app.state.model_error = str(exc)
        logger.error("Model not loaded: %s", exc)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Glowrithm API", version=API_VERSION, description=__doc__, lifespan=lifespan)
    app.state.settings = settings or get_settings()
    app.add_middleware(CORSMiddleware, allow_origins=app.state.settings.cors_origins,
                       allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(router)
    settings = app.state.settings
    serve_web = settings.serve_web and (settings.web_dir / "index.html").is_file()
    if serve_web:
        app.mount("/app", StaticFiles(directory=settings.web_dir, html=True), name="web")

        @app.middleware("http")
        async def web_headers(request: Request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/app"):
                response.headers.update(WEB_HEADERS)
            return response

    @app.get("/", include_in_schema=False, response_model=None)
    def root() -> dict | RedirectResponse:
        if serve_web:
            return RedirectResponse("/app/")
        return {"name": "Glowrithm API", "version": API_VERSION, "docs": "/docs", "health": "/api/v1/health"}

    return app


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    expected = request.app.state.settings.api_key
    if expected and not (x_api_key and secrets.compare_digest(x_api_key, expected)):
        raise HTTPException(status_code=401, detail="Missing or invalid API key.")


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    engine = request.app.state.engine
    return HealthResponse(status="ok" if engine else "degraded", api_version=API_VERSION,
                          model_loaded=engine is not None, model_version=engine.model_version if engine else None,
                          demo_mode=bool(engine and engine.demo), classes=engine.class_names if engine else [],
                          detail=request.app.state.model_error)


@router.get("/skin-types", response_model=list[SkinTypeInfo], dependencies=[Depends(require_api_key)])
def skin_types(request: Request) -> list[dict]:
    return request.app.state.recommender.skin_types()


@router.get("/ingredients", response_model=list[IngredientInfo], dependencies=[Depends(require_api_key)])
def ingredients(request: Request, skin_type: Literal["dry", "normal", "oily"] | None = Query(None)) -> list[dict]:
    return request.app.state.recommender.ingredients(skin_type)


def _explanation(label: str, confidence: float, low: bool, face: bool) -> str:
    text = (f"The model is {confidence:.0%} confident that your skin type is {label.lower()}. "
            "Warmer areas of the heat map influenced this prediction the most.")
    if low:
        text += " Confidence is low: retake the photo in soft, even light without makeup before relying on it."
    if not face:
        text += " No face was detected, so the centre of the photo was analysed."
    return text


@router.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(require_api_key)])
async def analyze(
    request: Request,
    response: Response,
    image: UploadFile = File(..., description="Frontal face photo (JPEG or PNG)"),
    consent: bool = Form(..., description="Must be true: explicit consent to process the photo (UU PDP)"),
    age: int | None = Form(None, ge=13, le=100),
    sex: Literal["female", "male"] | None = Form(None),
) -> AnalyzeResponse:
    settings: Settings = request.app.state.settings
    if not consent:
        raise HTTPException(status_code=400, detail="Explicit consent is required before a photo can be processed.")
    engine: InferenceEngine | None = request.app.state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail=f"The model is not loaded: {request.app.state.model_error}")

    limit = int(settings.max_upload_mb * 1024 * 1024)
    data = await image.read(limit + 1)
    await image.close()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"The photo is larger than {settings.max_upload_mb:g} MB.")

    started = time.perf_counter()
    try:
        result = await run_in_threadpool(engine.analyze, data, settings.display_size, settings.quality_gate,
                                         settings.require_face)
    except InvalidImageError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except PhotoQualityError as exc:  # quality gate: tell the user how to retake the photo
        raise HTTPException(status_code=422, detail=f"Photo quality is too low. {exc}") from exc
    finally:
        del data  # drop the only reference to the photo bytes
    if settings.require_face and not result["face_detected"]:
        raise HTTPException(status_code=422, detail="No face was detected. Face the camera in good light and try again.")

    recommender: Recommender = request.app.state.recommender
    info = recommender.skin_type_info(result["skin_type"])
    low = result["confidence"] < settings.low_confidence
    recommendations = recommender.recommend(result["probabilities"], result["skin_type"], age=age, sex=sex)
    request_id = uuid.uuid4().hex
    result["timings_ms"]["total"] = round((time.perf_counter() - started) * 1000, 1)
    # Log only non-personal metadata: no image, age or sex.
    logger.info("analyze id=%s class=%s confidence=%.3f face=%s total_ms=%.0f", request_id[:8],
                result["skin_type"], result["confidence"], result["face_detected"], result["timings_ms"]["total"])
    response.headers["Cache-Control"] = "no-store"
    return AnalyzeResponse(
        request_id=request_id, skin_type=result["skin_type"], skin_type_label=info["label_en"],
        skin_type_label_id=info["label_id"], skin_type_description=info["description"],
        confidence=round(result["confidence"], 4), probabilities=result["probabilities"], low_confidence=low,
        face_detected=result["face_detected"],
        explanation=_explanation(info["label_en"], result["confidence"], low, result["face_detected"]),
        face_image=result["face_image"], heatmap_image=result["heatmap_image"], recommendations=recommendations,
        disclaimer=recommender.disclaimer, model_version=engine.model_version, demo_mode=engine.demo,
        timings_ms=result["timings_ms"], quality=result.get("quality"))


app = create_app()
