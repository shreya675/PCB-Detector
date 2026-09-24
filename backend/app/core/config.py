from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PCB AOI Research Prototype"
    app_env: str = "development"
    database_url: str = "sqlite:///./pcb_aoi.db"
    cors_origins: str = "http://localhost:5173"
    model_path: str = "models/weights/yolo11m_official_v4.pt"
    model_card_path: str = "models/model_card.json"
    confidence_threshold: float = Field(0.25, ge=0, le=1)
    max_upload_mb: int = Field(20, ge=1)
    storage_root: str = "reports/inspections"
    severity_policy_path: str = "backend/app/core/severity.yaml"
    enable_reference_analysis: bool = True
    enable_postprocess: bool = True
    postprocess_nms_iou: float = Field(0.2, ge=0, le=1)
    postprocess_box_scale: float = Field(1.15, ge=1, le=2)
    auto_create_schema: bool = True
    static_dir: str = "frontend/dist"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


settings = Settings()
