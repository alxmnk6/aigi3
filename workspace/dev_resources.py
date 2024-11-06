from os import getenv

from phi.docker.app.fastapi import FastApi
from phi.docker.app.postgres import PgVectorDb
from phi.docker.app.streamlit import Streamlit
from phi.docker.resource.image import DockerImage
from phi.docker.resources import DockerResources
from phi.docker.app.redis import Redis
from phi.docker.app.qdrant import QdrantDb

from workspace.settings import ws_settings

#
# -*- Resources for the Development Environment
#

# -*- Dev image
dev_image = DockerImage(
    name=f"{ws_settings.image_repo}/{ws_settings.image_name}",
    tag=ws_settings.dev_env,
    enabled=ws_settings.build_images,
    path=str(ws_settings.ws_root),
    push_image=False,
)

# -*- Redis for caching and session management
dev_redis = Redis(
    name=f"{ws_settings.ws_name}-redis",
    enabled=True,
    host_port=6379,
    environment={
        "REDIS_PASSWORD": "ai_redis_password",  # Set a secure password
    },
)

# -*- Qdrant for vector search
dev_qdrant = QdrantDb(
    name=f"{ws_settings.ws_name}-qdrant",
    enabled=True,
    host_port=6333,
)

# -*- Dev database running on port 5433
dev_db = PgVectorDb(
    name=f"{ws_settings.ws_name}-db",
    enabled=ws_settings.dev_db_enabled,
    pg_user="ai",
    pg_password="ai",
    pg_database="ai",
    host_port=5433,
)

# -*- Build container environment
container_env = {
    "RUNTIME_ENV": "dev",
    "OPENAI_API_KEY": getenv("OPENAI_API_KEY"),
    "PHI_MONITORING": "True",
    "PHI_API_KEY": getenv("PHI_API_KEY"),
    # Database configuration
    "DB_HOST": dev_db.get_db_host(),
    "DB_PORT": dev_db.get_db_port(),
    "DB_USER": dev_db.get_db_user(),
    "DB_PASS": dev_db.get_db_password(),
    "DB_DATABASE": dev_db.get_db_database(),
    # Redis configuration
    "REDIS_HOST": dev_redis.get_host(),
    "REDIS_PORT": dev_redis.get_port(),
    "REDIS_PASSWORD": "ai_redis_password",
    # Qdrant configuration
    "QDRANT_HOST": dev_qdrant.get_host(),
    "QDRANT_PORT": dev_qdrant.get_port(),
    # Wait for services
    "WAIT_FOR_DB": ws_settings.dev_db_enabled,
    "WAIT_FOR_REDIS": True,
    "WAIT_FOR_QDRANT": True,
    "MAX_MEMORY": "2G",
    "MAX_CPU": "1.5",
    "GRACEFUL_SHUTDOWN_TIMEOUT": "30",
    "HEALTH_CHECK_INTERVAL": "15",
    # Add these for UI functionality
    "STREAMLIT_SHARE_ENABLED": "true",
    "STREAMLIT_CHAT_HISTORY": "true",
    "STREAMLIT_MAX_MESSAGE_SIZE": "5242880",  # 5MB
    "STREAMLIT_RATE_LIMIT": "100",
    "STREAMLIT_SESSION_TIMEOUT": "3600",
}

# -*- Streamlit app
dev_streamlit = Streamlit(
    name=f"{ws_settings.ws_name}-app",
    enabled=ws_settings.dev_app_enabled,
    image=dev_image,
    command="streamlit run app/Home.py",
    port_number=8501,
    debug_mode=True,
    mount_workspace=True,
    streamlit_server_headless=True,
    env_vars=container_env,
    use_cache=ws_settings.use_cache,
    secrets_file=ws_settings.ws_root.joinpath("workspace/secrets/dev_app_secrets.yml"),
    depends_on=[dev_db, dev_redis, dev_qdrant],
    environment={
        **container_env,
        "STREAMLIT_THEME_BASE": "light",
        "STREAMLIT_SERVER_MAX_UPLOAD_SIZE": "50",
        "STREAMLIT_CLIENT_TOOLBAR_MODE": "minimal",
        "STREAMLIT_CLIENT_SHOW_ERROR_DETAILS": str(ws_settings.debug_mode).lower(),
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    },
    health_check_endpoint="/health",
    mount_workspace=True,
    reload_on_change=True,
)

# -*- FastAPI app
dev_fastapi = FastApi(
    name=f"{ws_settings.ws_name}-api",
    enabled=ws_settings.dev_api_enabled,
    image=dev_image,
    command="uvicorn api.main:app --reload",
    port_number=8000,
    debug_mode=True,
    mount_workspace=True,
    env_vars=container_env,
    use_cache=ws_settings.use_cache,
    secrets_file=ws_settings.ws_root.joinpath("workspace/secrets/dev_app_secrets.yml"),
    depends_on=[dev_db, dev_redis, dev_qdrant],
)

# -*- Dev DockerResources
dev_docker_resources = DockerResources(
    env=ws_settings.dev_env,
    network=ws_settings.ws_name,
    apps=[dev_db, dev_redis, dev_qdrant, dev_streamlit, dev_fastapi],
)

# Vector store configuration
dev_vector_stores = {
    "pgvector": dev_db,
    "qdrant": dev_qdrant,
}
