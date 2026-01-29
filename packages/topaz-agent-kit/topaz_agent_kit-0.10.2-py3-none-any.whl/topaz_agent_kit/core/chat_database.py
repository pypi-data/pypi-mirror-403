"""
Chat Database Module
Handles SQLite database operations for chat sessions, turns, and context management
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from topaz_agent_kit.utils.logger import Logger


class ChatDatabase:
    """SQLite database manager for chat sessions, turns, and context storage"""
    
    def __init__(self, db_path: str = "data/chat.db"):
        self.logger = Logger("ChatDatabase")
        self.db_path = Path(db_path)
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Chat database initialized: {}", self.db_path.absolute())
        
        # Initialize database schema
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Create database tables and indexes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create chat_sessions table - simplified
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    thread_state TEXT,
                    title TEXT DEFAULT 'New chat'
                )
            """)
            
            # Add missing columns to existing tables (if not exists)
            # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we check first
            cursor.execute("PRAGMA table_info(chat_sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'thread_state' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN thread_state TEXT")
                    self.logger.info("Added thread_state column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add thread_state column (may already exist): {}", e)
            
            if 'title' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN title TEXT DEFAULT 'New chat'")
                    self.logger.info("Added title column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add title column (may already exist): {}", e)
            
            if 'pinned' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN pinned INTEGER DEFAULT 0")
                    self.logger.info("Added pinned column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add pinned column (may already exist): {}", e)
            
            if 'pinned_order' not in columns:
                try:
                    cursor.execute("ALTER TABLE chat_sessions ADD COLUMN pinned_order INTEGER DEFAULT 0")
                    self.logger.info("Added pinned_order column to chat_sessions table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add pinned_order column (may already exist): {}", e)
            
            # Create chat_turns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT REFERENCES chat_sessions(id),
                    turn_number INTEGER NOT NULL,
                    turn_id TEXT,
                    entries TEXT NOT NULL DEFAULT '[]',
                    pipeline_id TEXT,
                    run_id TEXT,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Add missing columns to existing chat_turns table (if not exists)
            cursor.execute("PRAGMA table_info(chat_turns)")
            turn_columns = [row[1] for row in cursor.fetchall()]
            
            if 'entries' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN entries TEXT NOT NULL DEFAULT '[]'")
                    self.logger.info("Added entries column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add entries column (may already exist): {}", e)
            
            if 'feedback' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN feedback TEXT")
                    self.logger.info("Added feedback column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add feedback column (may already exist): {}", e)
            
            if 'regenerated_by' not in turn_columns:
                try:
                    cursor.execute("ALTER TABLE chat_turns ADD COLUMN regenerated_by INTEGER REFERENCES chat_turns(id)")
                    self.logger.info("Added regenerated_by column to chat_turns table")
                except sqlite3.Error as e:
                    self.logger.warning("Failed to add regenerated_by column (may already exist): {}", e)
            
            # Create available_content table for analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS available_content (
                    file_name TEXT PRIMARY KEY,
                    file_type TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    topics TEXT NOT NULL,
                    example_questions TEXT NOT NULL,
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    word_count INTEGER
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_session ON chat_turns(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_turn_id ON chat_turns(turn_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_pipeline ON chat_turns(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_run_id ON chat_turns(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON chat_sessions(last_accessed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_available_content_type ON available_content(content_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_available_content_timestamp ON available_content(analysis_timestamp)")
            
            # =============================================================================
            # ASYNC HITL QUEUE SYSTEM TABLES
            # =============================================================================
            
            # Create pipeline_cases table - ALL cases (both HITL and straight-through)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT UNIQUE NOT NULL,
                    display_id TEXT NOT NULL,
                    pipeline_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    session_id TEXT,
                    case_type TEXT,
                    status TEXT NOT NULL DEFAULT 'processing',
                    current_step TEXT,
                    case_data TEXT NOT NULL DEFAULT '{}',
                    final_output TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    processing_time_ms INTEGER
                )
            """)
            
            # Add display_id column if it doesn't exist (migration for existing databases)
            try:
                cursor.execute("ALTER TABLE pipeline_cases ADD COLUMN display_id TEXT")
                # Backfill: set display_id = case_id for existing rows
                cursor.execute("UPDATE pipeline_cases SET display_id = case_id WHERE display_id IS NULL")
                self.logger.info("Added display_id column to pipeline_cases table")
            except Exception:
                pass  # Column already exists
            
            # Create pipeline_checkpoints table - HITL cases only (for resumption)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL,
                    pipeline_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    gate_id TEXT NOT NULL,
                    checkpoint_data BLOB NOT NULL,
                    resume_point TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resumed_at TIMESTAMP,
                    FOREIGN KEY (case_id) REFERENCES pipeline_cases(case_id)
                )
            """)
            
            # Create hitl_queue table - Queue display items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hitl_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_item_id TEXT UNIQUE NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    pipeline_id TEXT NOT NULL,
                    gate_id TEXT NOT NULL,
                    gate_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    options TEXT,
                    gate_config TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'medium',
                    decision TEXT,
                    response_data TEXT,
                    responded_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP,
                    FOREIGN KEY (checkpoint_id) REFERENCES pipeline_checkpoints(checkpoint_id),
                    FOREIGN KEY (case_id) REFERENCES pipeline_cases(case_id)
                )
            """)
            
            # Add gate_config column if it doesn't exist (migration for existing databases)
            try:
                cursor.execute("ALTER TABLE hitl_queue ADD COLUMN gate_config TEXT")
                self.logger.info("Added gate_config column to hitl_queue table")
            except Exception:
                pass  # Column already exists
            
            # Create indexes for async HITL tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_pipeline ON pipeline_cases(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON pipeline_cases(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_created ON pipeline_cases(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_run_id ON pipeline_cases(run_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_case ON pipeline_checkpoints(case_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_status ON pipeline_checkpoints(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkpoints_pipeline ON pipeline_checkpoints(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_pipeline ON hitl_queue(pipeline_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON hitl_queue(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_created ON hitl_queue(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_checkpoint ON hitl_queue(checkpoint_id)")
            
            conn.commit()
            self.logger.info("Database schema initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            self.logger.error("Database error: {}", e)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def create_chat_session(self, session_id: str, source: str = "fastapi") -> bool:
        """Create a new chat session - simplified"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_sessions (id, source)
                    VALUES (?, ?)
                """, (session_id, source))
                
                conn.commit()
                self.logger.info("Created chat session: {} - {}", session_id, source)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create chat session {}: {}", session_id, e)
            return False
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session by ID - simplified"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat session {}: {}", session_id, e)
            return None
    
    def update_chat_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update chat session"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare update fields
                update_fields = []
                update_values = []
                
                for key, value in updates.items():
                    if key in ['history', 'usage'] and isinstance(value, (dict, list)):
                        update_fields.append(f"{key} = ?")
                        update_values.append(json.dumps(value))
                    else:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                # Add last_accessed timestamp
                update_fields.append("last_accessed = ?")
                update_values.append(datetime.now())
                
                update_values.append(session_id)
                
                query = f"UPDATE chat_sessions SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                self.logger.debug("Updated chat session: {}", session_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update chat session {}: {}", session_id, e)
            return False
    
    def create_chat_turn(self, session_id: str, turn_number: int,
                        pipeline_id: Optional[str] = None, run_id: Optional[str] = None) -> Optional[int]:
        """Create a new chat turn"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_turns (
                        session_id, turn_number, pipeline_id, run_id
                    ) VALUES (?, ?, ?, ?)
                """, (session_id, turn_number, pipeline_id, run_id))
                
                turn_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info("Created chat turn: {} - turn {}", turn_id, turn_number)
                return turn_id
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create chat turn: {}", e)
            return None
    
    def update_chat_turn(self, turn_id: int, updates: Dict[str, Any]) -> bool:
        """Update chat turn"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare update fields
                update_fields = []
                update_values = []
                
                for key, value in updates.items():
                    if key in ['entries', 'feedback']:
                        if isinstance(value, (dict, list)):
                            update_fields.append(f"{key} = ?")
                            update_values.append(json.dumps(value))
                        else:
                            update_fields.append(f"{key} = ?")
                            update_values.append(value)
                    else:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                update_values.append(turn_id)
                
                query = f"UPDATE chat_turns SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                self.logger.debug("Updated chat turn: {}", turn_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update chat turn {}: {}", turn_id, e)
            return False
    
    def get_chat_turns(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all turns for a session"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM chat_turns 
                    WHERE session_id = ? 
                    ORDER BY turn_number ASC
                """, (session_id,))
                
                rows = cursor.fetchall()
                turns = []
                
                for row in rows:
                    turn_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['entries', 'feedback']:
                        if turn_data.get(json_field):
                            try:
                                turn_data[json_field] = json.loads(turn_data[json_field])
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, keep as string
                                pass
                    
                    turns.append(turn_data)
                
                return turns
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat turns for session {}: {}", session_id, e)
            return []
    
    def get_chat_turn_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get chat turn by run ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM chat_turns WHERE run_id = ?", (run_id,))
                row = cursor.fetchone()
                
                if row:
                    turn_data = dict(row)
                    
                    # Parse JSON fields
                    for json_field in ['entries', 'feedback']:
                        if turn_data.get(json_field):
                            try:
                                turn_data[json_field] = json.loads(turn_data[json_field])
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, keep as string
                                pass
                    
                    return turn_data
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get chat turn by run_id {}: {}", run_id, e)
            return None
    
    def get_all_sessions(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all sessions with given status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM chat_sessions 
                    WHERE status = ? 
                    ORDER BY last_accessed DESC
                """, (status,))
                
                rows = cursor.fetchall()
                sessions = []
                
                for row in rows:
                    session_data = dict(row)
                    
                    # Parse JSON fields
                    if session_data.get('history'):
                        session_data['history'] = json.loads(session_data['history'])
                    if session_data.get('usage'):
                        session_data['usage'] = json.loads(session_data['usage'])
                    
                    sessions.append(session_data)
                
                return sessions
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get sessions with status {}: {}", status, e)
            return []
    
    def delete_chat_session(self, session_id: str) -> bool:
        """Delete chat session and all associated turns"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete associated turns first
                cursor.execute("DELETE FROM chat_turns WHERE session_id = ?", (session_id,))
                
                # Delete session
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
                
                conn.commit()
                self.logger.info("Deleted chat session: {}", session_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete chat session {}: {}", session_id, e)
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get session counts
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'active'")
                active_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'archived'")
                archived_sessions = cursor.fetchone()[0]
                
                # Get turn counts
                cursor.execute("SELECT COUNT(*) FROM chat_turns")
                total_turns = cursor.fetchone()[0]
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    "active_sessions": active_sessions,
                    "archived_sessions": archived_sessions,
                    "total_turns": total_turns,
                    "database_size_bytes": db_size,
                    "database_path": str(self.db_path)
                }
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get database stats: {}", e)
            return {}
    
    # =============================================================================
    # AVAILABLE CONTENT MANAGEMENT METHODS
    # =============================================================================
    
    def create_available_content(self, file_name: str, file_type: str, content_type: str, 
                               summary: str, topics: List[str], example_questions: List[str],
                               file_size: Optional[int] = None, word_count: Optional[int] = None) -> bool:
        """Create or update available content entry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert lists to JSON strings
                topics_json = json.dumps(topics)
                questions_json = json.dumps(example_questions)
                
                # Insert or replace (upsert) the content
                cursor.execute("""
                    INSERT OR REPLACE INTO available_content 
                    (file_name, file_type, content_type, summary, topics, example_questions, 
                     file_size, word_count, analysis_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_name, file_type, content_type, summary, topics_json, questions_json, 
                      file_size, word_count))
                
                conn.commit()
                self.logger.info("Created/updated available content for file: {}", file_name)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create available content for {}: {}", file_name, e)
            return False
    
    def get_available_content(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available content entries, optionally filtered by content_type"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if content_type:
                    cursor.execute("""
                        SELECT file_name, file_type, content_type, summary, topics, 
                               example_questions, analysis_timestamp, file_size, word_count
                        FROM available_content 
                        WHERE content_type = ?
                        ORDER BY analysis_timestamp DESC
                    """, (content_type,))
                else:
                    cursor.execute("""
                        SELECT file_name, file_type, content_type, summary, topics, 
                               example_questions, analysis_timestamp, file_size, word_count
                        FROM available_content 
                        ORDER BY analysis_timestamp DESC
                    """)
                
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    # Convert JSON strings back to lists
                    topics = json.loads(row['topics']) if row['topics'] else []
                    example_questions = json.loads(row['example_questions']) if row['example_questions'] else []
                    
                    results.append({
                        "file_name": row['file_name'],
                        "file_type": row['file_type'],
                        "content_type": row['content_type'],
                        "summary": row['summary'],
                        "topics": topics,
                        "example_questions": example_questions,
                        "analysis_timestamp": row['analysis_timestamp'],
                        "file_size": row['file_size'],
                        "word_count": row['word_count']
                    })
                
                self.logger.debug("Retrieved {} available content entries", len(results))
                return results
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get available content: {}", e)
            return []
    
    def update_available_content(self, file_name: str, **updates) -> bool:
        """Update available content entry with provided fields"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields = []
                update_values = []
                
                for field, value in updates.items():
                    if field in ['topics', 'example_questions'] and isinstance(value, list):
                        # Convert lists to JSON
                        update_fields.append(f"{field} = ?")
                        update_values.append(json.dumps(value))
                    elif field in ['summary', 'file_type', 'content_type']:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                    elif field in ['file_size', 'word_count']:
                        update_fields.append(f"{field} = ?")
                        update_values.append(value)
                
                if not update_fields:
                    self.logger.warning("No valid fields to update for file: {}", file_name)
                    return False
                
                # Add timestamp update
                update_fields.append("analysis_timestamp = CURRENT_TIMESTAMP")
                
                query = f"UPDATE available_content SET {', '.join(update_fields)} WHERE file_name = ?"
                update_values.append(file_name)
                
                cursor.execute(query, update_values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Updated available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No content found to update for file: {}", file_name)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update available content for {}: {}", file_name, e)
            return False
    
    def get_available_content_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get available content entry by filename"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT file_name, file_type, content_type, summary, topics, 
                           example_questions, file_size, word_count, analysis_timestamp
                    FROM available_content 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "file_name": result[0],
                        "file_type": result[1],
                        "content_type": result[2],
                        "summary": result[3],
                        "topics": json.loads(result[4]) if result[4] else [],
                        "example_questions": json.loads(result[5]) if result[5] else [],
                        "file_size": result[6],
                        "word_count": result[7],
                        "analysis_timestamp": result[8]
                    }
                return None
                    
        except sqlite3.Error as e:
            self.logger.error("Failed to get available content for {}: {}", file_name, e)
            return None
    
    def delete_available_content_by_filename(self, file_name: str) -> bool:
        """Delete available content entry by filename"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM available_content 
                    WHERE file_name = ?
                """, (file_name,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info("Deleted available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No available content found for file: {}", file_name)
                    return False
                    
        except sqlite3.Error as e:
            self.logger.error("Failed to delete available content for {}: {}", file_name, e)
            return False
    
    def delete_available_content(self, file_name: str) -> bool:
        """Delete available content entry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM available_content WHERE file_name = ?", (file_name,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Deleted available content for file: {}", file_name)
                    return True
                else:
                    self.logger.warning("No content found to delete for file: {}", file_name)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete available content for {}: {}", file_name, e)
            return False
    
    # =============================================================================
    # PIPELINE CASES MANAGEMENT METHODS
    # =============================================================================
    
    def create_pipeline_case(
        self,
        case_id: str,
        pipeline_id: str,
        run_id: str,
        display_id: Optional[str] = None,
        session_id: Optional[str] = None,
        case_type: Optional[str] = None,
        status: str = "processing",
        current_step: Optional[str] = None,
        case_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a new pipeline case entry
        
        Args:
            case_id: Unique case identifier (always unique with suffix)
            pipeline_id: Pipeline that created this case
            run_id: Run ID for tracking
            display_id: Human-readable business ID (may not be unique). Defaults to case_id.
            session_id: Session ID for tracking
            case_type: Type of case (from case config)
            status: Initial status (default: processing)
            current_step: Current processing step
            case_data: Case data for display
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                case_data_json = json.dumps(case_data or {})
                # If display_id not provided, use case_id as fallback
                actual_display_id = display_id or case_id
                
                cursor.execute("""
                    INSERT INTO pipeline_cases (
                        case_id, display_id, pipeline_id, run_id, session_id, case_type,
                        status, current_step, case_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (case_id, actual_display_id, pipeline_id, run_id, session_id, case_type,
                      status, current_step, case_data_json))
                
                conn.commit()
                self.logger.info("Created pipeline case: {} (display: {}) for pipeline {}", 
                               case_id, actual_display_id, pipeline_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Database error: {}", e)
            self.logger.error("Failed to create pipeline case {}: {}", case_id, e)
            return False
    
    def get_pipeline_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pipeline case by case_id or display_id.
        Tries case_id first, then falls back to display_id if not found.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First try by case_id
                cursor.execute("SELECT * FROM pipeline_cases WHERE case_id = ?", (case_id,))
                row = cursor.fetchone()
                
                # If not found, try by display_id
                if not row:
                    cursor.execute("SELECT * FROM pipeline_cases WHERE display_id = ?", (case_id,))
                    row = cursor.fetchone()
                
                if row:
                    case_data = dict(row)
                    # Parse JSON fields
                    if case_data.get('case_data'):
                        try:
                            case_data['case_data'] = json.loads(case_data['case_data'])
                        except (json.JSONDecodeError, TypeError):
                            case_data['case_data'] = {}
                    if case_data.get('final_output'):
                        try:
                            case_data['final_output'] = json.loads(case_data['final_output'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return case_data
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get pipeline case {}: {}", case_id, e)
            return None
    
    def update_pipeline_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """Update pipeline case with provided fields"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = []
                update_values = []
                
                for key, value in updates.items():
                    if key in ['case_data', 'final_output'] and isinstance(value, (dict, list)):
                        update_fields.append(f"{key} = ?")
                        update_values.append(json.dumps(value))
                    else:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                # Always update updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                update_values.append(case_id)
                
                query = f"UPDATE pipeline_cases SET {', '.join(update_fields)} WHERE case_id = ?"
                cursor.execute(query, update_values)
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.debug("Updated pipeline case: {}", case_id)
                    return True
                else:
                    self.logger.warning("No pipeline case found to update: {}", case_id)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update pipeline case {}: {}", case_id, e)
            return False
    
    def list_pipeline_cases(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        run_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List pipeline cases with optional filters"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM pipeline_cases WHERE 1=1"
                params = []
                
                if pipeline_id:
                    query += " AND pipeline_id = ?"
                    params.append(pipeline_id)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if run_id:
                    query += " AND run_id = ?"
                    params.append(run_id)
                if from_date:
                    query += " AND created_at >= ?"
                    params.append(from_date)
                if to_date:
                    query += " AND created_at <= ?"
                    params.append(to_date)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                cases = []
                for row in rows:
                    case_data = dict(row)
                    # Parse JSON fields
                    if case_data.get('case_data'):
                        try:
                            case_data['case_data'] = json.loads(case_data['case_data'])
                        except (json.JSONDecodeError, TypeError):
                            case_data['case_data'] = {}
                    if case_data.get('final_output'):
                        try:
                            case_data['final_output'] = json.loads(case_data['final_output'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    cases.append(case_data)
                
                return cases
                
        except sqlite3.Error as e:
            self.logger.error("Failed to list pipeline cases: {}", e)
            return []
    
    def delete_pipeline_case(self, case_id: str) -> bool:
        """Delete pipeline case and associated checkpoints/queue items"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete associated queue items first
                cursor.execute("DELETE FROM hitl_queue WHERE case_id = ?", (case_id,))
                # Delete associated checkpoints
                cursor.execute("DELETE FROM pipeline_checkpoints WHERE case_id = ?", (case_id,))
                # Delete the case
                cursor.execute("DELETE FROM pipeline_cases WHERE case_id = ?", (case_id,))
                
                conn.commit()
                self.logger.info("Deleted pipeline case and associated data: {}", case_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete pipeline case {}: {}", case_id, e)
            return False
    
    def delete_pipeline_cases(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """
        Delete multiple pipeline cases with filters and their associated data.
        
        Args:
            pipeline_id: Filter by pipeline ID (optional)
            status: Filter by status (optional)
            
        Returns:
            Number of cases deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause
                conditions = []
                params = []
                
                if pipeline_id:
                    conditions.append("pipeline_id = ?")
                    params.append(pipeline_id)
                
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                # First, get all case_ids that match the filters
                cursor.execute(
                    f"SELECT case_id FROM pipeline_cases WHERE {where_clause}",
                    params
                )
                case_ids = [row[0] for row in cursor.fetchall()]
                
                if not case_ids:
                    return 0
                
                # Delete associated queue items
                placeholders = ",".join("?" * len(case_ids))
                cursor.execute(
                    f"DELETE FROM hitl_queue WHERE case_id IN ({placeholders})",
                    case_ids
                )
                
                # Delete associated checkpoints
                cursor.execute(
                    f"DELETE FROM pipeline_checkpoints WHERE case_id IN ({placeholders})",
                    case_ids
                )
                
                # Delete the cases
                cursor.execute(
                    f"DELETE FROM pipeline_cases WHERE case_id IN ({placeholders})",
                    case_ids
                )
                
                conn.commit()
                deleted_count = len(case_ids)
                self.logger.info("Deleted {} pipeline cases with filters: pipeline_id={}, status={}", 
                               deleted_count, pipeline_id, status)
                return deleted_count
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete pipeline cases: {}", e)
            return 0
    
    # =============================================================================
    # PIPELINE CHECKPOINTS MANAGEMENT METHODS
    # =============================================================================
    
    def create_checkpoint(
        self,
        checkpoint_id: str,
        case_id: str,
        pipeline_id: str,
        run_id: str,
        gate_id: str,
        checkpoint_data: bytes,
        resume_point: str,
        expires_at: Optional[str] = None,
    ) -> bool:
        """Create a new pipeline checkpoint for HITL resumption"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO pipeline_checkpoints (
                        checkpoint_id, case_id, pipeline_id, run_id, gate_id,
                        checkpoint_data, resume_point, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (checkpoint_id, case_id, pipeline_id, run_id, gate_id,
                      checkpoint_data, resume_point, expires_at))
                
                conn.commit()
                self.logger.info("Created checkpoint {} for case {}", checkpoint_id, case_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create checkpoint {}: {}", checkpoint_id, e)
            return False
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint by checkpoint_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM pipeline_checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get checkpoint {}: {}", checkpoint_id, e)
            return None
    
    def get_checkpoint_by_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest pending checkpoint for a case"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM pipeline_checkpoints 
                    WHERE case_id = ? AND status = 'pending'
                    ORDER BY created_at DESC LIMIT 1
                """, (case_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get checkpoint for case {}: {}", case_id, e)
            return None
    
    def get_checkpoint_by_case_gate(
        self,
        case_id: str,
        gate_id: str,
        include_resumed: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for a case and gate combination.
        
        Args:
            case_id: The case identifier
            gate_id: The gate identifier
            include_resumed: If True, include resumed checkpoints (for duplicate prevention)
            
        Returns:
            Checkpoint record or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if include_resumed:
                    # Check for any checkpoint (pending or resumed) for this case+gate
                    cursor.execute("""
                        SELECT * FROM pipeline_checkpoints 
                        WHERE case_id = ? AND gate_id = ?
                        ORDER BY created_at DESC LIMIT 1
                    """, (case_id, gate_id))
                else:
                    # Only check for pending checkpoints
                    cursor.execute("""
                        SELECT * FROM pipeline_checkpoints 
                        WHERE case_id = ? AND gate_id = ? AND status = 'pending'
                        ORDER BY created_at DESC LIMIT 1
                    """, (case_id, gate_id))
                
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get checkpoint for case {} gate {}: {}", case_id, gate_id, e)
            return None
    
    def update_checkpoint_status(
        self,
        checkpoint_id: str,
        status: str,
        resumed_at: Optional[str] = None,
    ) -> bool:
        """Update checkpoint status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if resumed_at:
                    cursor.execute("""
                        UPDATE pipeline_checkpoints 
                        SET status = ?, resumed_at = ?
                        WHERE checkpoint_id = ?
                    """, (status, resumed_at, checkpoint_id))
                else:
                    cursor.execute("""
                        UPDATE pipeline_checkpoints 
                        SET status = ?
                        WHERE checkpoint_id = ?
                    """, (status, checkpoint_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.debug("Updated checkpoint status: {} -> {}", checkpoint_id, status)
                    return True
                else:
                    self.logger.warning("No checkpoint found to update: {}", checkpoint_id)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update checkpoint {}: {}", checkpoint_id, e)
            return False
    
    def list_pending_checkpoints(
        self,
        pipeline_id: Optional[str] = None,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """List pending checkpoints"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM pipeline_checkpoints WHERE status = 'pending'"
                params = []
                
                if pipeline_id:
                    query += " AND pipeline_id = ?"
                    params.append(pipeline_id)
                
                if not include_expired:
                    query += " AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)"
                
                query += " ORDER BY created_at ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            self.logger.error("Failed to list pending checkpoints: {}", e)
            return []
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete associated queue items first
                cursor.execute("DELETE FROM hitl_queue WHERE checkpoint_id = ?", (checkpoint_id,))
                # Delete the checkpoint
                cursor.execute("DELETE FROM pipeline_checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
                
                conn.commit()
                self.logger.info("Deleted checkpoint: {}", checkpoint_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete checkpoint {}: {}", checkpoint_id, e)
            return False
    
    # =============================================================================
    # HITL QUEUE MANAGEMENT METHODS
    # =============================================================================
    
    def create_hitl_queue_item(
        self,
        queue_item_id: str,
        checkpoint_id: str,
        case_id: str,
        pipeline_id: str,
        gate_id: str,
        gate_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        gate_config: Optional[Dict[str, Any]] = None,
        priority: str = "medium",
    ) -> bool:
        """Create a new HITL queue item"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                options_json = json.dumps(options) if options else None
                gate_config_json = json.dumps(gate_config) if gate_config else None
                
                cursor.execute("""
                    INSERT INTO hitl_queue (
                        queue_item_id, checkpoint_id, case_id, pipeline_id,
                        gate_id, gate_type, title, description, options, gate_config, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (queue_item_id, checkpoint_id, case_id, pipeline_id,
                      gate_id, gate_type, title, description, options_json, gate_config_json, priority))
                
                conn.commit()
                self.logger.info("Created HITL queue item {} for case {}", queue_item_id, case_id)
                return True
                
        except sqlite3.Error as e:
            self.logger.error("Failed to create HITL queue item {}: {}", queue_item_id, e)
            return False
    
    def get_hitl_queue_item(self, queue_item_id: str) -> Optional[Dict[str, Any]]:
        """Get HITL queue item by queue_item_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM hitl_queue WHERE queue_item_id = ?", (queue_item_id,))
                row = cursor.fetchone()
                
                if row:
                    item = dict(row)
                    # Parse JSON fields
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (json.JSONDecodeError, TypeError):
                            item['options'] = []
                    if item.get('response_data'):
                        try:
                            item['response_data'] = json.loads(item['response_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return item
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get HITL queue item {}: {}", queue_item_id, e)
            return None
    
    def get_hitl_queue_item_by_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get HITL queue item by checkpoint_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM hitl_queue WHERE checkpoint_id = ?", (checkpoint_id,))
                row = cursor.fetchone()
                
                if row:
                    item = dict(row)
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (json.JSONDecodeError, TypeError):
                            item['options'] = []
                    if item.get('gate_config'):
                        try:
                            item['gate_config'] = json.loads(item['gate_config'])
                        except (json.JSONDecodeError, TypeError):
                            item['gate_config'] = {}
                    if item.get('response_data'):
                        try:
                            item['response_data'] = json.loads(item['response_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return item
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get HITL queue item by checkpoint {}: {}", checkpoint_id, e)
            return None
    
    def list_hitl_queue(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List HITL queue items with optional filters"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM hitl_queue WHERE 1=1"
                params = []
                
                if pipeline_id:
                    query += " AND pipeline_id = ?"
                    params.append(pipeline_id)
                if status:
                    query += " AND status = ?"
                    params.append(status)
                if priority:
                    query += " AND priority = ?"
                    params.append(priority)
                
                # Order by priority (high first) then by created_at
                query += """
                    ORDER BY 
                        CASE priority 
                            WHEN 'high' THEN 1 
                            WHEN 'medium' THEN 2 
                            WHEN 'low' THEN 3 
                        END,
                        created_at ASC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                items = []
                for row in rows:
                    item = dict(row)
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (json.JSONDecodeError, TypeError):
                            item['options'] = []
                    if item.get('gate_config'):
                        try:
                            item['gate_config'] = json.loads(item['gate_config'])
                        except (json.JSONDecodeError, TypeError):
                            item['gate_config'] = {}
                    if item.get('response_data'):
                        try:
                            item['response_data'] = json.loads(item['response_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    items.append(item)
                
                return items
                
        except sqlite3.Error as e:
            self.logger.error("Failed to list HITL queue: {}", e)
            return []
    
    def get_pending_queue_item_by_case_gate(
        self,
        case_id: str,
        gate_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a pending HITL queue item for a specific case and gate"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM hitl_queue 
                    WHERE case_id = ? AND gate_id = ? AND status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (case_id, gate_id))
                
                row = cursor.fetchone()
                
                if row:
                    item = dict(row)
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (json.JSONDecodeError, TypeError):
                            item['options'] = []
                    if item.get('gate_config'):
                        try:
                            item['gate_config'] = json.loads(item['gate_config'])
                        except (json.JSONDecodeError, TypeError):
                            item['gate_config'] = {}
                    if item.get('response_data'):
                        try:
                            item['response_data'] = json.loads(item['response_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return item
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get pending queue item for case {} gate {}: {}", case_id, gate_id, e)
            return None
    
    def get_queue_item_by_case_gate(
        self,
        case_id: str,
        gate_id: str,
        include_responded: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a HITL queue item for a specific case and gate combination.
        
        Args:
            case_id: The case identifier
            gate_id: The gate identifier
            include_responded: If True, include responded queue items (for duplicate prevention)
            
        Returns:
            Queue item record or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if include_responded:
                    # Check for any queue item (pending or responded) for this case+gate
                    cursor.execute("""
                        SELECT * FROM hitl_queue 
                        WHERE case_id = ? AND gate_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (case_id, gate_id))
                else:
                    # Only check for pending queue items
                    cursor.execute("""
                        SELECT * FROM hitl_queue 
                        WHERE case_id = ? AND gate_id = ? AND status = 'pending'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (case_id, gate_id))
                
                row = cursor.fetchone()
                
                if row:
                    item = dict(row)
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (json.JSONDecodeError, TypeError):
                            item['options'] = []
                    if item.get('gate_config'):
                        try:
                            item['gate_config'] = json.loads(item['gate_config'])
                        except (json.JSONDecodeError, TypeError):
                            item['gate_config'] = {}
                    if item.get('response_data'):
                        try:
                            item['response_data'] = json.loads(item['response_data'])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    return item
                
                return None
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get queue item for case {} gate {}: {}", case_id, gate_id, e)
            return None
    
    def update_hitl_queue_response(
        self,
        queue_item_id: str,
        decision: str,
        response_data: Optional[Dict[str, Any]] = None,
        responded_by: Optional[str] = None,
    ) -> bool:
        """Update HITL queue item with user response"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                response_data_json = json.dumps(response_data) if response_data else None
                
                cursor.execute("""
                    UPDATE hitl_queue 
                    SET status = 'responded',
                        decision = ?,
                        response_data = ?,
                        responded_by = ?,
                        responded_at = CURRENT_TIMESTAMP
                    WHERE queue_item_id = ?
                """, (decision, response_data_json, responded_by, queue_item_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Updated HITL queue response: {} -> {}", queue_item_id, decision)
                    return True
                else:
                    self.logger.warning("No HITL queue item found to update: {}", queue_item_id)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update HITL queue response {}: {}", queue_item_id, e)
            return False
    
    def update_hitl_queue_item_status(
        self,
        queue_item_id: str,
        status: str,
        clear_response: bool = False,
    ) -> bool:
        """Update HITL queue item status, optionally clearing response data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if clear_response:
                    cursor.execute("""
                        UPDATE hitl_queue 
                        SET status = ?,
                            decision = NULL,
                            response_data = NULL,
                            responded_by = NULL,
                            responded_at = NULL
                        WHERE queue_item_id = ?
                    """, (status, queue_item_id))
                else:
                    cursor.execute("""
                        UPDATE hitl_queue 
                        SET status = ?
                        WHERE queue_item_id = ?
                    """, (status, queue_item_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Updated HITL queue item status: {} -> {}", queue_item_id, status)
                    return True
                else:
                    self.logger.warning("No HITL queue item found to update: {}", queue_item_id)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to update HITL queue item status {}: {}", queue_item_id, e)
            return False
    
    def delete_hitl_queue_item(self, queue_item_id: str) -> bool:
        """Delete HITL queue item"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM hitl_queue WHERE queue_item_id = ?", (queue_item_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info("Deleted HITL queue item: {}", queue_item_id)
                    return True
                else:
                    self.logger.warning("No HITL queue item found to delete: {}", queue_item_id)
                    return False
                
        except sqlite3.Error as e:
            self.logger.error("Failed to delete HITL queue item {}: {}", queue_item_id, e)
            return False
    
    def get_hitl_queue_count(
        self,
        pipeline_id: Optional[str] = None,
        status: str = "pending",
    ) -> int:
        """Get count of HITL queue items"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT COUNT(*) FROM hitl_queue WHERE status = ?"
                params = [status]
                
                if pipeline_id:
                    query += " AND pipeline_id = ?"
                    params.append(pipeline_id)
                
                cursor.execute(query, params)
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            self.logger.error("Failed to get HITL queue count: {}", e)
            return 0