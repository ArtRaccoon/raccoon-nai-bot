import base64
import os
import secrets
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.services.nai_client import NovelAIClient, NovelAIError
from config_defaults import UserSettings

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN", "").strip()
NOVELAI_TOKEN = (os.getenv("NOVELAI_TOKEN") or os.getenv("NAI_TOKEN") or "").strip()
NAI_MODEL = os.getenv("NAI_MODEL", "").strip()
PROXY_URL = os.getenv("PROXY_URL", "").strip()

app = FastAPI(title="Raccoon NAI Bot Local API")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: Optional[str] = None
    width: int = Field(default=832, gt=0)
    height: int = Field(default=1216, gt=0)
    steps: int = Field(default=23, gt=0)
    scale: float = Field(default=4.0, gt=0)


class GenerateResponse(BaseModel):
    ok: bool
    image_base64: str
    mime_type: str


def require_api_token(authorization: str = Header(default="")) -> None:
    if not API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ok": False, "error": "API_TOKEN is not configured"},
        )

    scheme, _, provided_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not provided_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"ok": False, "error": "Bearer authorization is required"},
        )

    if not secrets.compare_digest(provided_token, API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"ok": False, "error": "Invalid authorization token"},
        )


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/generate", response_model=GenerateResponse)
async def generate_image(
    request: GenerateRequest,
    _: None = Depends(require_api_token),
) -> GenerateResponse:
    client = NovelAIClient(NOVELAI_TOKEN, default_model=NAI_MODEL, proxy_url=PROXY_URL)
    settings = UserSettings(
        width=request.width,
        height=request.height,
        steps=request.steps,
        scale=request.scale,
        negative_prompt=request.negative_prompt or "",
    )

    try:
        images = await client.generate(request.prompt, settings)
    except NovelAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"ok": False, "error": str(exc)},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"ok": False, "error": "Image generation failed"},
        ) from exc

    if not images:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"ok": False, "error": "NovelAI returned no images"},
        )

    return GenerateResponse(
        ok=True,
        image_base64=base64.b64encode(images[0]).decode("utf-8"),
        mime_type="image/png",
    )
