import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from rag.config.settings import get_settings

@pytest.mark.asyncio
async def test_postgresql_connection():
    """Verify that we can connect to the real PostgreSQL database and pgvector is enabled."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    
    async with engine.connect() as conn:
        # Test basic connectivity
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # Test pgvector extension
        result = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        assert result.scalar() == "vector"
        
        # Test if our schema exists
        result = await conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'rag'"))
        assert result.scalar() == "rag"
        
    await engine.dispose()
