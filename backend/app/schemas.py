"""Pydantic response models (they also document the API at /docs)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Regulatory(BaseModel):
    status: str = Field(description="permitted | restricted | prohibited (BPOM)")
    label: str
    note: str
    reference: str
    verified: bool = Field(description="False until the team has checked the note against the BPOM annex")


class IngredientInfo(BaseModel):
    id: str
    name: str
    alias: str | None = None
    inci: str | None = None
    function: str
    benefits: list[str]
    how_to_use: str
    caution: str | None = None
    evidence: list[str]
    regulatory: Regulatory
    suitability: dict[str, float]


class IngredientRecommendation(IngredientInfo):
    match: float = Field(ge=0, le=1, description="Expected suitability under the predicted class probabilities")
    match_percent: int
    personal_notes: list[str] = []


class RoutineStep(BaseModel):
    order: int
    key: str
    title: str
    goal: str
    ingredients: list[IngredientRecommendation]


class AvoidItem(BaseModel):
    name: str
    reason: str


class Recommendations(BaseModel):
    skin_type: str
    headline: str
    summary: str
    steps: list[RoutineStep]
    avoid: list[AvoidItem]
    notes: list[str]


class SkinTypeInfo(BaseModel):
    key: str
    label_en: str
    label_id: str
    description: str
    care_focus: str


class QualityCheck(BaseModel):
    name: str
    value: float | None = None
    status: str = Field(description="ok | warn | fail")
    message: str = ""


class QualityReport(BaseModel):
    passed: bool
    mode: str = Field(description="reject | warn")
    checks: list[QualityCheck]
    issues: list[str]


class AnalyzeResponse(BaseModel):
    request_id: str
    skin_type: str
    skin_type_label: str
    skin_type_label_id: str
    skin_type_description: str
    confidence: float
    probabilities: dict[str, float]
    low_confidence: bool
    face_detected: bool
    explanation: str
    face_image: str = Field(description="Base64 JPEG of the square face crop that the model analysed")
    heatmap_image: str = Field(description="Base64 JPEG of the Grad-CAM heat map (same size as face_image)")
    recommendations: Recommendations
    disclaimer: str
    model_version: str
    demo_mode: bool
    timings_ms: dict[str, float]
    quality: QualityReport | None = None


class HealthResponse(BaseModel):
    status: str
    api_version: str
    model_loaded: bool
    model_version: str | None = None
    demo_mode: bool = False
    classes: list[str] = []
    detail: str | None = None
