"""
HELIX Authentication Module
===========================
Simple SQLite + JWT authentication for user management.
"""

import os
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'helix_users.db')
JWT_SECRET = os.getenv('JWT_SECRET', 'helix-jwt-secret-change-in-prod')
JWT_EXPIRY_HOURS = 24 * 7  # 7 days

def _get_db():
    """Get database connection and ensure tables exist"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Create tables if not exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            cloudinary_url TEXT,
            local_path TEXT,
            hlx_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # API Keys table for SDK/API access
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_hash TEXT NOT NULL,
            key_prefix TEXT NOT NULL,
            name TEXT NOT NULL,
            permissions TEXT DEFAULT 'encode,materialize',
            requests_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

def hash_password(password: str) -> str:
    """Hash password with salt (salt:hash)"""
    salt = secrets.token_hex(16)
    return f"{salt}:{_hash_with_salt(password, salt)}"

def _hash_with_salt(password: str, salt: str) -> str:
    """Helper to hash salt + password"""
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify password against stored hash"""
    try:
        if ':' in stored_password:
            salt, hash_val = stored_password.split(':')
            # Check salt + password
            if hash_val == hashlib.sha256((salt + provided_password).encode()).hexdigest():
                return True
            # Check password + salt (just in case)
            if hash_val == hashlib.sha256((provided_password + salt).encode()).hexdigest():
                return True
            return False
        else:
            # Fallback for unsalted
            return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()
    except Exception:
        return False

def _generate_token(user_id: int, email: str) -> str:
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def register_user(email: str, password: str, name: str = None) -> Tuple[bool, str]:
    """Register a new user"""
    try:
        conn = _get_db()
        password_hash = hash_password(password)
        
        try:
            cursor = conn.execute(
                'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
                (email, password_hash, name)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            # Auto-login
            token = _generate_token(user_id, email)
            conn.close()
            return True, token
            
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Email already exists"
            
    except Exception as e:
        print(f"Register error: {e}")
        return False, str(e)

def login_user(email: str, password: str) -> Tuple[bool, str]:
    """Login a user"""
    try:
        conn = _get_db()
        user = conn.execute(
            'SELECT id, email, password_hash FROM users WHERE email = ?',
            (email,)
        ).fetchone()
        conn.close()
        
        if not user:
            return False, "Invalid credentials"
            
        if not verify_password(user['password_hash'], password):
            return False, "Invalid credentials"
            
        token = _generate_token(user['id'], user['email'])
        return True, token
        
    except Exception as e:
        print(f"Login error: {e}")
        return False, str(e)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except Exception:
        return None

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user profile"""
    conn = _get_db()
    user = conn.execute(
        'SELECT id, email, name, created_at FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def save_user_file(user_id: int, filename: str, file_type: str, hlx_data: str = None, cloudinary_url: str = None) -> int:
    """Save file reference"""
    conn = _get_db()
    cursor = conn.execute(
        '''INSERT INTO user_files 
           (user_id, filename, file_type, hlx_data, cloudinary_url) 
           VALUES (?, ?, ?, ?, ?)''',
        (user_id, filename, file_type, hlx_data, cloudinary_url)
    )
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def get_user_files(user_id: int) -> list:
    """List user files"""
    conn = _get_db()
    files = conn.execute(
        'SELECT * FROM user_files WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(f) for f in files]

def save_chat_message(user_id: int, role: str, content: str) -> bool:
    """Save a chat message to history"""
    try:
        conn = _get_db()
        conn.execute(
            'INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)',
            (user_id, role, content)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Failed to save chat message: {e}")
        return False

def get_chat_history(user_id: int, limit: int = 50) -> list:
    """Get chat history for a user"""
    try:
        conn = _get_db()
        messages = conn.execute(
            'SELECT role, content, created_at FROM chat_history WHERE user_id = ? ORDER BY created_at ASC',
            (user_id,)
        ).fetchall()
        conn.close()
        # Filter to last 'limit' messages but keep chronological order
        if len(messages) > limit:
            messages = messages[-limit:]
        return [dict(m) for m in messages]
    except Exception as e:
        print(f"Failed to get chat history: {e}")
        return []

def get_file_by_id(file_id: int, user_id: int = None) -> Optional[dict]:
    """Get file by ID, optionally verifying ownership"""
    conn = _get_db()
    if user_id:
        file = conn.execute(
            'SELECT * FROM user_files WHERE id = ? AND user_id = ?',
            (file_id, user_id)
        ).fetchone()
    else:
        file = conn.execute(
            'SELECT * FROM user_files WHERE id = ?',
            (file_id,)
        ).fetchone()
    conn.close()
    
    if file:
        return dict(file)
    return None

def delete_user_file(file_id: int, user_id: int) -> bool:
    """Delete a user file"""
    try:
        conn = _get_db()
        cursor = conn.execute(
            'DELETE FROM user_files WHERE id = ? AND user_id = ?',
            (file_id, user_id)
        )
        row_count = cursor.rowcount
        conn.commit()
        conn.close()
        return row_count > 0
    except Exception as e:
        print(f"Delete file error: {e}")
        return False

# ============================================
# API KEY MANAGEMENT
# ============================================

def generate_api_key(user_id: int, name: str, permissions: str = 'encode,materialize') -> Tuple[bool, str, str]:
    """
    Generate a new API key for a user.
    Returns: (success, api_key, error_message)
    The full API key is only returned once - we store the hash.
    """
    try:
        conn = _get_db()
        
        # Generate a secure random key: hlx_<random>
        key_secret = secrets.token_urlsafe(32)
        api_key = f"hlx_{key_secret}"
        key_prefix = api_key[:12]  # hlx_XXXXXXXX for display
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        conn.execute(
            '''INSERT INTO api_keys (user_id, key_hash, key_prefix, name, permissions)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, key_hash, key_prefix, name, permissions)
        )
        conn.commit()
        conn.close()
        
        return True, api_key, ""
    except Exception as e:
        print(f"API key generation error: {e}")
        return False, "", str(e)

def verify_api_key(api_key: str) -> Optional[dict]:
    """
    Verify an API key and return user info if valid.
    Also increments usage count.
    """
    try:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        conn = _get_db()
        
        row = conn.execute(
            '''SELECT ak.*, u.email, u.name as user_name
               FROM api_keys ak
               JOIN users u ON ak.user_id = u.id
               WHERE ak.key_hash = ? AND ak.revoked_at IS NULL''',
            (key_hash,)
        ).fetchone()
        
        if row:
            # Update usage stats
            conn.execute(
                '''UPDATE api_keys 
                   SET requests_count = requests_count + 1, last_used_at = CURRENT_TIMESTAMP
                   WHERE id = ?''',
                (row['id'],)
            )
            conn.commit()
            conn.close()
            
            return {
                'user_id': row['user_id'],
                'email': row['email'],
                'key_name': row['name'],
                'permissions': row['permissions'].split(',') if row['permissions'] else []
            }
        
        conn.close()
        return None
    except Exception as e:
        print(f"API key verification error: {e}")
        return None

def get_user_api_keys(user_id: int) -> list:
    """Get all API keys for a user (without revealing the actual keys)"""
    try:
        conn = _get_db()
        keys = conn.execute(
            '''SELECT id, key_prefix, name, permissions, requests_count, 
                      last_used_at, created_at, revoked_at
               FROM api_keys WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        ).fetchall()
        conn.close()
        return [dict(k) for k in keys]
    except Exception as e:
        print(f"Get API keys error: {e}")
        return []

def revoke_api_key(key_id: int, user_id: int) -> bool:
    """Revoke an API key"""
    try:
        conn = _get_db()
        cursor = conn.execute(
            '''UPDATE api_keys SET revoked_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?''',
            (key_id, user_id)
        )
        row_count = cursor.rowcount
        conn.commit()
        conn.close()
        return row_count > 0
    except Exception as e:
        print(f"Revoke API key error: {e}")
        return False

def delete_api_key(key_id: int, user_id: int) -> bool:
    """Delete an API key permanently"""
    try:
        conn = _get_db()
        cursor = conn.execute(
            'DELETE FROM api_keys WHERE id = ? AND user_id = ?',
            (key_id, user_id)
        )
        row_count = cursor.rowcount
        conn.commit()
        conn.close()
        return row_count > 0
    except Exception as e:
        print(f"Delete API key error: {e}")
        return False
