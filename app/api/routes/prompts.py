"""
Custom prompts API routes
"""

from typing import List
import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.schemas import CustomPrompt

router = APIRouter()


class CustomPromptCreate(BaseModel):
    name: str
    prompt: str
    confidence_threshold: float = 0.7
    enabled: bool = True
    camera_ids: List[str] = None


class CustomPromptUpdate(BaseModel):
    name: str = None
    prompt: str = None
    confidence_threshold: float = None
    enabled: bool = None
    camera_ids: List[str] = None


@router.get("/")
async def get_custom_prompts(request: Request):
    """Get all custom prompts"""
    ai_detector = request.app.state.ai_detector
    prompts = ai_detector.get_custom_prompts()
    return [prompt.to_dict() for prompt in prompts]


@router.post("/")
async def create_custom_prompt(request: Request, prompt_data: CustomPromptCreate):
    """Create a new custom prompt"""
    ai_detector = request.app.state.ai_detector
    
    prompt = CustomPrompt(
        id=str(uuid.uuid4()),
        name=prompt_data.name,
        prompt=prompt_data.prompt,
        confidence_threshold=prompt_data.confidence_threshold,
        enabled=prompt_data.enabled,
        camera_ids=prompt_data.camera_ids
    )
    
    ai_detector.add_custom_prompt(prompt)
    return prompt.to_dict()


@router.put("/{prompt_id}")
async def update_custom_prompt(request: Request, prompt_id: str, prompt_data: CustomPromptUpdate):
    """Update a custom prompt"""
    ai_detector = request.app.state.ai_detector
    prompts = ai_detector.get_custom_prompts()
    
    # Find the prompt
    prompt = None
    for p in prompts:
        if p.id == prompt_id:
            prompt = p
            break
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Custom prompt not found")
    
    # Update fields
    if prompt_data.name is not None:
        prompt.name = prompt_data.name
    if prompt_data.prompt is not None:
        prompt.prompt = prompt_data.prompt
    if prompt_data.confidence_threshold is not None:
        prompt.confidence_threshold = prompt_data.confidence_threshold
    if prompt_data.enabled is not None:
        prompt.enabled = prompt_data.enabled
    if prompt_data.camera_ids is not None:
        prompt.camera_ids = prompt_data.camera_ids
    
    return prompt.to_dict()


@router.delete("/{prompt_id}")
async def delete_custom_prompt(request: Request, prompt_id: str):
    """Delete a custom prompt"""
    ai_detector = request.app.state.ai_detector
    ai_detector.remove_custom_prompt(prompt_id)
    return {"message": "Custom prompt deleted successfully"}
