import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    # Get application settings
    settings = get_settings()
    
    # Start the uvicorn server
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )