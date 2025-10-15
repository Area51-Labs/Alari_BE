"""
Database health check endpoint for verifying database connection and tables.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import time

from database import get_db, engine

router = APIRouter()


@router.get("/health")
async def database_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive database health check.
    Verifies connection, tables, and basic operations.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    try:
        # Check 1: Database connection
        start = time.time()
        db.execute(text("SELECT 1"))
        connection_time = time.time() - start
        health_status["checks"]["connection"] = {
            "status": "ok",
            "response_time_ms": round(connection_time * 1000, 2)
        }
        
        # Check 2: Verify all tables exist
        inspector = inspect(engine)
        expected_tables = ["users", "conversations", "messages", "goals", "goal_check_ins"]
        existing_tables = inspector.get_table_names()
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            health_status["checks"]["tables"] = {
                "status": "error",
                "message": f"Missing tables: {missing_tables}",
                "existing_tables": existing_tables
            }
            health_status["status"] = "unhealthy"
        else:
            health_status["checks"]["tables"] = {
                "status": "ok",
                "count": len(existing_tables),
                "tables": existing_tables
            }
        
        # Check 3: Get table row counts
        table_stats = {}
        for table in expected_tables:
            if table in existing_tables:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_stats[table] = count
        
        health_status["checks"]["table_stats"] = {
            "status": "ok",
            "row_counts": table_stats
        }
        
        # Check 4: Verify indexes exist
        indexes_info = {}
        for table in expected_tables:
            if table in existing_tables:
                indexes = inspector.get_indexes(table)
                indexes_info[table] = len(indexes)
        
        health_status["checks"]["indexes"] = {
            "status": "ok",
            "index_counts": indexes_info
        }
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        raise HTTPException(status_code=503, detail=health_status)


@router.get("/tables")
async def list_database_tables():
    """List all tables with column information."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        table_info = {}
        for table in tables:
            columns = inspector.get_columns(table)
            table_info[table] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": str(col["default"]) if col["default"] else None
                    }
                    for col in columns
                ],
                "column_count": len(columns)
            }
        
        return {
            "total_tables": len(tables),
            "tables": table_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify-schema")
async def verify_schema():
    """Verify database schema matches expected structure."""
    try:
        inspector = inspect(engine)
        
        expected_schema = {
            "users": ["id", "email", "hashed_password", "user_name", "created_at"],
            "conversations": ["id", "user_id", "session_id", "title", "created_at", "updated_at"],
            "messages": ["id", "conversation_id", "role", "content", "keywords", "created_at"],
            "goals": ["id", "user_id", "title", "description", "target_date", "status", "streak_count", "created_at", "updated_at"],
            "goal_check_ins": ["id", "goal_id", "check_in_date", "progress_note", "completed"]
        }
        
        verification_results = {}
        all_valid = True
        
        for table, expected_columns in expected_schema.items():
            if table not in inspector.get_table_names():
                verification_results[table] = {
                    "exists": False,
                    "status": "missing"
                }
                all_valid = False
            else:
                actual_columns = [col["name"] for col in inspector.get_columns(table)]
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                extra_columns = [col for col in actual_columns if col not in expected_columns]
                
                verification_results[table] = {
                    "exists": True,
                    "status": "valid" if not missing_columns and not extra_columns else "invalid",
                    "missing_columns": missing_columns,
                    "extra_columns": extra_columns,
                    "all_columns": actual_columns
                }
                
                if missing_columns or extra_columns:
                    all_valid = False
        
        return {
            "schema_valid": all_valid,
            "tables": verification_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
