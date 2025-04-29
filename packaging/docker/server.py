"""
Telert Server API - FastAPI application to expose telert notification functionality via HTTP.
Allows sending notifications to any configured provider via a simple REST API.
"""

from typing import Dict, List, Optional, Union, Any
import os
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from telert import send, is_configured, list_providers, get_config

app = FastAPI(
    title="Telert API",
    description="Send notifications from HTTP requests to various messaging services",
    version="0.1.0"
)

# Configure CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be restricted to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NotificationRequest(BaseModel):
    """Model for notification request data."""
    message: str = Field(..., description="The message to send in the notification")
    provider: Optional[Union[str, List[str]]] = Field(
        None, description="Specific provider(s) to use. If not specified, default provider(s) will be used"
    )
    all_providers: Optional[bool] = Field(
        False, description="If true, send to all configured providers"
    )

class ProviderInfo(BaseModel):
    """Model for provider configuration information."""
    name: str
    is_default: bool
    config: Dict[str, Any]

@app.get("/", tags=["Info"])
async def root():
    """Get API information and status."""
    return {"status": "ok", "message": "Telert API is running"}

@app.get("/status", tags=["Info"])
async def status():
    """Check if any messaging providers are configured."""
    providers_list = list_providers()
    
    if not providers_list:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "unconfigured", "message": "No messaging providers configured"}
        )
    
    # Format providers list for response
    providers_info = []
    for provider in providers_list:
        # Filter out sensitive information
        config = provider["config"].copy()
        if "token" in config:
            config["token"] = "••••••••" 
        if "webhook_url" in config:
            config["webhook_url"] = "••••••••"
            
        providers_info.append({
            "name": provider["name"],
            "is_default": provider["is_default"],
            "config": config
        })
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "configured", 
            "providers": providers_info,
            "message": f"{len(providers_info)} provider(s) configured"
        }
    )

@app.post("/send", tags=["Notifications"])
async def send_notification(request: NotificationRequest):
    """Send a notification using configured providers."""
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No messaging providers configured. Configure providers using environment variables."
        )
    
    try:
        # Send the notification
        results = send(
            message=request.message,
            provider=request.provider,
            all_providers=request.all_providers
        )
        
        # Format the response
        successful = all(results.values())
        successful_providers = [p for p, success in results.items() if success]
        failed_providers = [p for p, success in results.items() if not success]
        
        return {
            "status": "success" if successful else "partial_success",
            "message": f"Notification sent successfully to {len(successful_providers)} provider(s)",
            "successful": successful_providers,
            "failed": failed_providers
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@app.get("/providers", tags=["Configuration"])
async def get_providers():
    """List all configured providers."""
    providers_list = list_providers()
    
    # Format providers for response
    providers_info = []
    for provider in providers_list:
        # Filter out sensitive information
        config = provider["config"].copy()
        if "token" in config:
            config["token"] = "••••••••" 
        if "webhook_url" in config:
            config["webhook_url"] = "••••••••"
            
        providers_info.append({
            "name": provider["name"],
            "is_default": provider["is_default"],
            "config": config
        })
    
    return {
        "providers": providers_info,
        "default_providers": [p["name"] for p in providers_info if p["is_default"]]
    }

# Additional healthcheck endpoint for container health monitoring
@app.get("/health", tags=["Info"])
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}