import json
import os
import uuid
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.params import Body, Path
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Optional, TYPE_CHECKING, Dict, Any
from pydantic import BaseModel
from omegaconf import OmegaConf
from service_forge.current_service import get_service

service_router = APIRouter(prefix="/sdk/service", tags=["service"])

class WorkflowStatusResponse(BaseModel):
    name: str
    version: str
    description: str
    workflows: list[dict]

class WorkflowActionResponse(BaseModel):
    workflow_id: Optional[str] = None
    success: bool
    message: str
    task_id: Optional[str] = None

@service_router.get("/status", response_model=WorkflowStatusResponse)
async def get_service_status():
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    # 排除调试版本
    try:
        status = service.get_service_status(exclude_debug=True)
        return status
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@service_router.get("/workflow/{workflow_id}/status", response_model=dict)
def get_workflow_data(workflow_id: str):
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        status = service.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@service_router.post("/workflow/{workflow_id}/start", response_model=WorkflowActionResponse)
async def start_workflow(workflow_id: str):
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        success = service.start_workflow_by_id(workflow_id)
        if success:
            return WorkflowActionResponse(success=True, message=f"Workflow {workflow_id} started successfully")
        else:
            return WorkflowActionResponse(success=False, message=f"Failed to start workflow {workflow_id}")
    except Exception as e:
        logger.error(f"Error starting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@service_router.post("/workflow/{workflow_id}/stop", response_model=WorkflowActionResponse)
async def stop_workflow(workflow_id: str):
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        success = await service.stop_workflow_by_id(workflow_id)
        if success:
            return WorkflowActionResponse(success=True, message=f"Workflow {workflow_id} stopped successfully")
        else:
            return WorkflowActionResponse(success=False, message=f"Failed to stop workflow {workflow_id}")
    except Exception as e:
        logger.error(f"Error stopping workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TriggerWorkflowRequest(BaseModel):
    kwargs: Optional[Dict[str, Any]] = {}

@service_router.post("/workflow/{workflow_id}/trigger", response_model=WorkflowActionResponse)
async def trigger_workflow(workflow_id: str = Path(...), request_body: TriggerWorkflowRequest = Body(...)):
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        task_id = service.trigger_workflow_by_id(workflow_id, "", None, **request_body.kwargs)   # Trigger Name实际上没有使用
        if task_id is not None:
            return WorkflowActionResponse(workflow_id=workflow_id, task_id=str(task_id), success=True, message=f"Workflow {workflow_id} triggered successfully with task_id {task_id}")
        else:
            return WorkflowActionResponse(workflow_id=workflow_id, success=False, message=f"Failed to trigger workflow {workflow_id}")
    except Exception as e:
        logger.error(f"Error triggering workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@service_router.post("/workflow/upload", response_model=WorkflowActionResponse)
async def upload_workflow_config(
    file: Optional[UploadFile] = File(None),
    config_content: Optional[str] = Form(None),
):
    service = get_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if file is None and config_content is None:
        raise HTTPException(status_code=400, detail="Either file or config_content must be provided")
    
    if file is not None and config_content is not None:
        raise HTTPException(status_code=400, detail="Cannot provide both file and config_content")
    
    temp_file_path = None
    try:
        if file is not None:
            if not file.filename or not file.filename.endswith(('.yaml', '.yml')):
                raise HTTPException(status_code=400, detail="Only YAML files are supported")
            
            suffix = '.yaml' if file.filename.endswith('.yaml') else '.yml'
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=suffix) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
           
            workflow_id = await service.load_workflow_from_config(config_path=temp_file_path)
        else:
            try:
                config = OmegaConf.to_object(OmegaConf.create(config_content))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
            
            workflow_id = await service.load_workflow_from_config(config=config)
        
        if workflow_id:
            return WorkflowActionResponse(
                workflow_id=str(workflow_id),
                success=True,
                message=f"Workflow configuration uploaded and loaded successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to load workflow configuration")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading workflow config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")

