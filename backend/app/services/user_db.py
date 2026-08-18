"""
User storage using MariaDB (MySQL-compatible).
This keeps the auth system independent from any embedding or external APIs.
"""
import pymysql
from pymysql.cursors import DictCursor
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
from app.config.env import env

# Database configuration from environment variables using your existing env function
DB_CONFIG = {
    'host': env("DB_HOST", "localhost"),
    'port': int(env("DB_PORT", 3306)),
    'user': env("DB_USER", "root"),
    'password': env("DB_PASSWORD", ""),
    'database': env("DB_NAME", "insurance_db"),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'autocommit': True
}


def _get_conn():
    """Get MariaDB connection"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MariaDB: {e}")
        raise


# In user_db.py, add file_size column
def _init_db():
    conn = _get_conn()
    with conn.cursor() as cur:
        # Update history table to include file_size
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                file_hash VARCHAR(255),
                filename VARCHAR(255),
                name VARCHAR(255),
                policy_id VARCHAR(255),
                description TEXT,
                raw_text LONGTEXT,
                json_data LONGTEXT,
                file_size BIGINT,  # ADD THIS COLUMN
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_history_username (username),
                INDEX idx_history_file_hash (file_hash),
                INDEX idx_history_policy_id (policy_id),
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
        """)
    conn.commit()
    conn.close()

# Initialize database on import
try:
    _init_db()
except Exception as e:
    print(f"⚠️  Database initialization note: {e}")


def store_user(username: str, password_hash: str) -> bool:
    """Store a new user"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password_hash)
            )
        conn.close()
        return True
    except pymysql.IntegrityError:
        return False  # User already exists
    except pymysql.Error as e:
        print(f"Error storing user: {e}")
        return False


def get_user(username: str) -> Optional[dict]:
    """Get user by username"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, password, created_at FROM users WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
        conn.close()
        return row if row else None
    except pymysql.Error as e:
        print(f"Error retrieving user: {e}")
        return None


def user_exists(username: str) -> bool:
    """Check if user exists"""
    return get_user(username) is not None


def create_session(username: str, token: str) -> bool:
    """Create a new session token"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Delete any existing sessions for this user
            cur.execute("DELETE FROM sessions WHERE username = %s", (username,))
            # Create new session
            cur.execute(
                "INSERT INTO sessions (token, username) VALUES (%s, %s)",
                (token, username)
            )
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"Error creating session: {e}")
        return False


def get_username_for_token(token: str) -> Optional[str]:
    """Get username for a session token"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username FROM sessions WHERE token = %s",
                (token,)
            )
            row = cur.fetchone()
        conn.close()
        return row['username'] if row else None
    except pymysql.Error as e:
        print(f"Error looking up session: {e}")
        return None


def create_history_entry(username: str, file_hash: str, filename: str, name: str,
                        policy_id: str, description: str, raw_text: str, 
                        json_data: Optional[dict] = None) -> bool:
    """Create a history entry for uploaded PDF"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Convert json_data to string if provided
            json_str = json.dumps(json_data) if json_data else None
            
            cur.execute("""
                INSERT INTO history 
                (username, file_hash, filename, name, policy_id, description, raw_text, json_data) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, file_hash, filename, name, policy_id, description, raw_text, json_str))
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"Error creating history entry: {e}")
        return False


def get_user_uploads(username: str) -> List[Dict[str, Any]]:
    """Get all PDF uploads for a user"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT file_hash, filename, name, policy_id, description, 
                       created_at, json_data
                FROM history 
                WHERE username = %s 
                ORDER BY created_at DESC
            """, (username,))
            rows = cur.fetchall()
        conn.close()
        
        uploads = []
        for row in rows:
            # Parse JSON data if it exists
            json_data = {}
            if row['json_data']:
                try:
                    json_data = json.loads(row['json_data'])
                except:
                    json_data = {}
            
            upload = {
                "file_hash": row['file_hash'],
                "filename": row['filename'],
                "name": row['name'],
                "policy_id": row['policy_id'],
                "description": row['description'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "download_url": f"/download/{row['file_hash']}",
                "has_json_data": bool(row['json_data']),
                "extracted_data": json_data
            }
            uploads.append(upload)
        
        return uploads
    except pymysql.Error as e:
        print(f"Error getting user uploads: {e}")
        return []


def get_user_history(username: str):
    """Get user's complete history (uploads and queries)"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Get uploads
            cur.execute("""
                SELECT id, file_hash, filename, name, policy_id, description, 
                       raw_text, created_at, json_data
                FROM history 
                WHERE username = %s 
                ORDER BY created_at DESC
            """, (username,))
            rows = cur.fetchall()
            
            uploads = []
            for row in rows:
                json_data = {}
                if row['json_data']:
                    try:
                        json_data = json.loads(row['json_data'])
                    except:
                        json_data = {}
                
                uploads.append({
                    "id": row['id'],
                    "file_hash": row['file_hash'],
                    "filename": row['filename'],
                    "name": row['name'],
                    "policy_id": row['policy_id'],
                    "description": row['description'],
                    "raw_text": row['raw_text'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "extracted_data": json_data,
                    "download_url": f"/download/{row['file_hash']}"
                })

            # Get queries
            cur.execute("""
                SELECT id, query, answer, file_hash, created_at
                FROM queries 
                WHERE username = %s 
                ORDER BY created_at DESC
            """, (username,))
            qrows = cur.fetchall()
            
            queries = []
            for row in qrows:
                pdf_ref = None
                if row['file_hash']:
                    pdf_ref = {
                        "file_hash": row['file_hash'],
                        "download_url": f"/download/{row['file_hash']}"
                    }
                
                queries.append({
                    "id": row['id'],
                    "query": row['query'],
                    "answer": row['answer'],
                    "file_hash": row['file_hash'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "pdf_reference": pdf_ref
                })

        conn.close()
        return {"uploads": uploads, "queries": queries}
    except pymysql.Error as e:
        print(f"Error retrieving history: {e}")
        return {"uploads": [], "queries": []}


def create_query_entry(username: str, query: str, answer: Any, file_hash: Optional[str] = None) -> bool:
    """Create a query history entry"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Convert answer to string if it's a dict
            if isinstance(answer, dict):
                answer_str = json.dumps(answer)
            else:
                answer_str = str(answer)
            
            cur.execute("""
                INSERT INTO queries (username, query, answer, file_hash)
                VALUES (%s, %s, %s, %s)
            """, (username, query, answer_str, file_hash))
        conn.close()
        return True
    except pymysql.Error as e:
        print(f"Error creating query entry: {e}")
        return False


def get_history_by_hash(username: str, file_hash: str):
    """Get history entry with file size"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, file_hash, filename, name, policy_id, description, 
                       raw_text, created_at, json_data, file_size
                FROM history 
                WHERE username = %s AND file_hash = %s
                LIMIT 1
            """, (username, file_hash))
            row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        json_data = json.loads(row['json_data']) if row['json_data'] else {}
        return {
            "id": row['id'],
            "file_hash": row['file_hash'],
            "filename": row['filename'],
            "name": row['name'],
            "policy_id": row['policy_id'],
            "description": row['description'],
            "raw_text": row['raw_text'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "extracted_data": json_data,
            "file_size": row['file_size'],  # ADD THIS
            "download_url": f"/download/{row['file_hash']}"
        }
    except Exception as e:
        print(f"Error getting history by hash: {e}")
        return None


def get_history_by_hash_any(file_hash: str):
    """Get history entry by file hash (any user)"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, file_hash, filename, name, policy_id, 
                       description, raw_text, created_at, json_data
                FROM history 
                WHERE file_hash = %s 
                LIMIT 1
            """, (file_hash,))
            row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        json_data = {}
        if row['json_data']:
            try:
                json_data = json.loads(row['json_data'])
            except:
                json_data = {}
        
        return {
            "id": row['id'],
            "username": row['username'],
            "file_hash": row['file_hash'],
            "filename": row['filename'],
            "name": row['name'],
            "policy_id": row['policy_id'],
            "description": row['description'],
            "raw_text": row['raw_text'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "extracted_data": json_data,
            "download_url": f"/download/{row['file_hash']}"
        }
    except pymysql.Error as e:
        print(f"Error getting any history by hash: {e}")
        return None


def get_relevant_pdfs_for_query(username: str, query: str, answer_data: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Find PDFs relevant to a query"""
    try:
        user_pdfs = get_user_uploads(username)
        if not user_pdfs:
            return []
        
        relevant_pdfs = []
        query_lower = query.lower()
        
        # 1. Check for policy number match in answer data
        if answer_data and isinstance(answer_data, dict):
            policy_number = answer_data.get("policy_number")
            if policy_number:
                matching_policy = [
                    pdf for pdf in user_pdfs 
                    if pdf.get('policy_id') and pdf['policy_id'].lower() == str(policy_number).lower()
                ]
                if matching_policy:
                    return matching_policy
        
        # 2. Check for filename or name matches in query
        for pdf in user_pdfs:
            # Check if filename is mentioned in query
            if pdf.get('filename') and pdf['filename'].lower() in query_lower:
                relevant_pdfs.append(pdf)
                continue
            
            # Check if policy name is mentioned
            if pdf.get('name') and pdf['name'].lower() in query_lower:
                relevant_pdfs.append(pdf)
                continue
            
            # Check if policy ID is mentioned
            if pdf.get('policy_id') and pdf['policy_id'].lower() in query_lower:
                relevant_pdfs.append(pdf)
                continue
        
        # 3. If we found relevant PDFs, return them
        if relevant_pdfs:
            return relevant_pdfs
        
        # 4. If query contains insurance terms, return all PDFs
        insurance_terms = ['policy', 'insurance', 'premium', 'claim', 'coverage', 
                          'term', 'document', 'pdf', 'file', 'upload']
        if any(term in query_lower for term in insurance_terms):
            return user_pdfs
        
        # 5. Return empty if no relevance found
        return []
        
    except Exception as e:
        print(f"Error finding relevant PDFs: {e}")
        return []


def get_pdf_by_policy_id(username: str, policy_id: str) -> Optional[Dict[str, Any]]:
    """Get PDF by policy ID for a specific user"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT file_hash, filename, name, policy_id, description, 
                       created_at, json_data
                FROM history 
                WHERE username = %s AND policy_id = %s
                LIMIT 1
            """, (username, policy_id))
            row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        json_data = {}
        if row['json_data']:
            try:
                json_data = json.loads(row['json_data'])
            except:
                json_data = {}
        
        return {
            "file_hash": row['file_hash'],
            "filename": row['filename'],
            "name": row['name'],
            "policy_id": row['policy_id'],
            "description": row['description'],
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "download_url": f"/download/{row['file_hash']}",
            "extracted_data": json_data
        }
    except pymysql.Error as e:
        print(f"Error getting PDF by policy ID: {e}")
        return None


def get_recent_pdfs(username: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get most recent PDF uploads"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT file_hash, filename, name, policy_id, description, created_at
                FROM history 
                WHERE username = %s 
                ORDER BY created_at DESC
                LIMIT %s
            """, (username, limit))
            rows = cur.fetchall()
        conn.close()
        
        pdfs = []
        for row in rows:
            pdfs.append({
                "file_hash": row['file_hash'],
                "filename": row['filename'],
                "name": row['name'],
                "policy_id": row['policy_id'],
                "description": row['description'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "download_url": f"/download/{row['file_hash']}"
            })
        
        return pdfs
    except pymysql.Error as e:
        print(f"Error getting recent PDFs: {e}")
        return []


def delete_user_history(username: str, file_hash: str) -> bool:
    """Delete a PDF upload from user's history"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Delete from history
            cur.execute(
                "DELETE FROM history WHERE username = %s AND file_hash = %s",
                (username, file_hash)
            )
            history_deleted = cur.rowcount
            
            # Delete related queries
            cur.execute(
                "DELETE FROM queries WHERE username = %s AND file_hash = %s",
                (username, file_hash)
            )
            
        conn.close()
        return history_deleted > 0
    except pymysql.Error as e:
        print(f"Error deleting user history: {e}")
        return False


def get_user_stats(username: str) -> Dict[str, Any]:
    """Get user statistics"""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            # Count uploads
            cur.execute(
                "SELECT COUNT(*) as count FROM history WHERE username = %s",
                (username,)
            )
            result = cur.fetchone()
            upload_count = result['count'] if result else 0
            
            # Count queries
            cur.execute(
                "SELECT COUNT(*) as count FROM queries WHERE username = %s",
                (username,)
            )
            result = cur.fetchone()
            query_count = result['count'] if result else 0
            
            # Get unique policy count
            cur.execute("""
                SELECT COUNT(DISTINCT policy_id) as count 
                FROM history 
                WHERE username = %s
            """, (username,))
            result = cur.fetchone()
            unique_policies = result['count'] if result else 0
            
            # Get latest upload date
            cur.execute("""
                SELECT MAX(created_at) as latest 
                FROM history 
                WHERE username = %s
            """, (username,))
            result = cur.fetchone()
            latest_upload = result['latest'].isoformat() if result and result['latest'] else None
            
        conn.close()
        
        return {
            "upload_count": upload_count,
            "query_count": query_count,
            "unique_policies": unique_policies,
            "latest_upload": latest_upload,
            "total_documents": upload_count
        }
    except pymysql.Error as e:
        print(f"Error getting user stats: {e}")
        return {
            "upload_count": 0,
            "query_count": 0,
            "unique_policies": 0,
            "latest_upload": None,
            "total_documents": 0
        }


# For backward compatibility
def get_user_history_legacy(username: str):
    """Legacy version for backward compatibility"""
    return get_user_history(username)