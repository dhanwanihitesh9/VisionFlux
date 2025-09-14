#!/usr/bin/env python3
"""
VisionFlux Test Script
Quick test to verify the installation and basic functionality
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import Settings
from app.services.ai_detector import AIDetector
from app.services.camera_manager import CameraManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic VisionFlux functionality"""
    logger.info("🧪 Testing VisionFlux basic functionality...")
    
    try:
        # Test configuration
        logger.info("Testing configuration...")
        settings = Settings()
        logger.info(f"✅ Configuration loaded - Server: {settings.host}:{settings.port}")
        
        # Test AI detector initialization
        logger.info("Testing AI detector...")
        ai_detector = AIDetector()
        logger.info("✅ AI detector created")
        
        # Note: We won't fully initialize AI models in test as they're large
        logger.info("⚠️ Skipping full AI model loading (use --full-test to enable)")
        
        # Test camera manager
        logger.info("Testing camera manager...")
        camera_manager = CameraManager(ai_detector)
        logger.info("✅ Camera manager created")
        
        # Test adding a dummy camera
        camera_id = camera_manager.add_camera("Test Camera", "rtsp://test")
        logger.info(f"✅ Added test camera with ID: {camera_id}")
        
        # Test getting cameras
        cameras = camera_manager.get_cameras()
        logger.info(f"✅ Retrieved {len(cameras)} cameras")
        
        # Clean up
        camera_manager.remove_camera(camera_id)
        logger.info("✅ Cleaned up test camera")
        
        logger.info("🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_full_functionality():
    """Test full VisionFlux functionality including AI models"""
    logger.info("🧪 Testing VisionFlux full functionality...")
    
    try:
        # Test AI detector with model loading
        logger.info("Testing AI detector with model loading...")
        ai_detector = AIDetector()
        await ai_detector.initialize()
        logger.info("✅ AI models loaded successfully")
        
        # Test custom prompt
        from app.models.schemas import CustomPrompt
        prompt = CustomPrompt(
            id="test-prompt",
            name="Test Prompt",
            prompt="person wearing red shirt",
            confidence_threshold=0.7
        )
        ai_detector.add_custom_prompt(prompt)
        logger.info("✅ Custom prompt added")
        
        prompts = ai_detector.get_custom_prompts()
        logger.info(f"✅ Retrieved {len(prompts)} custom prompts")
        
        logger.info("🎉 Full functionality test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Full test failed: {e}")
        return False


def test_imports():
    """Test if all required packages can be imported"""
    logger.info("🔍 Testing package imports...")
    
    packages = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'PIL': 'Pillow',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'ultralytics': 'Ultralytics'
    }
    
    failed = []
    for package, name in packages.items():
        try:
            __import__(package)
            logger.info(f"✅ {name} imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import {name}: {e}")
            failed.append(name)
    
    if failed:
        logger.error(f"❌ Failed to import: {', '.join(failed)}")
        return False
    
    logger.info("✅ All packages imported successfully")
    return True


async def main():
    """Main test function"""
    print("🚀 VisionFlux Test Suite")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed")
        sys.exit(1)
    
    # Test basic functionality
    if not await test_basic_functionality():
        print("\n❌ Basic functionality test failed")
        sys.exit(1)
    
    # Ask if user wants to run full test
    if len(sys.argv) > 1 and sys.argv[1] == '--full-test':
        if not await test_full_functionality():
            print("\n❌ Full functionality test failed")
            sys.exit(1)
    else:
        print("\n💡 Run with --full-test to test AI model loading")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("\nVisionFlux is ready to use!")
    print("Run 'python main.py' to start the application")


if __name__ == "__main__":
    asyncio.run(main())
