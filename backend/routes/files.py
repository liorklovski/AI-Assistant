"""
File upload and processing endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File

from services import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload file and create processing job"""
    try:
        # Validate file
        validation_error = FileService.validate_file(file)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)
        
        # Save file and get details
        stored_filename, file_type, file_size = await FileService.save_file(file)
        
        # Create processing job
        job_id = await FileService.create_file_job(
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_type=file_type,
            file_size=file_size
        )
        
        return {"job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
