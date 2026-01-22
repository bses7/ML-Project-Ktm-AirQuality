import shutil
import os
import subprocess
from src.config.settings import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def sync_models_to_app():
    artifacts = ["voting_ensemble.pkl", "scaler.pkl", "features.pkl"]
    os.makedirs(Config.DEPLOY_ARTIFACT_DIR, exist_ok=True)
    
    for filename in artifacts:
        src = os.path.join(Config.MODEL_DIR, filename)
        dst = os.path.join(Config.DEPLOY_ARTIFACT_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            logger.info(f"Synced {filename} to backend artifacts.")
        else:
            logger.warning(f"Artifact {filename} missing. Deployment might fail.")

def run_docker_containers():
    """Step 2: Trigger docker-compose build and up."""
    logger.info("Initiating Docker Deployment (Build & Up)...")
    try:
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
        logger.info("Docker containers are running in detached mode (-d).")
        logger.info("Backend: http://localhost:8000 | Frontend: http://localhost:3000")
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker deployment failed: {e}")
    except FileNotFoundError:
        logger.error("docker-compose command not found. Is Docker installed?")

def deploy_pipeline():
    """The full deployment sequence."""
    sync_models_to_app()
    run_docker_containers()