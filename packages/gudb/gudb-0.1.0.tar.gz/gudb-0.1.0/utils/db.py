import psycopg2
from utils.config import settings


def test_db_connection():
    """Test database connection and print status"""
    try:
        print("=" * 50)
        print("🔌 Testing Database Connection...")
        print(f"📍 DB URL: {settings.db_url}")
        print("=" * 50)
        
        conn = psycopg2.connect(settings.db_url)
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        
        print("✅ Database connection successful!")
        print(f"📊 PostgreSQL version: {version}")
        
        cur.close()
        conn.close()
        
        print("=" * 50)
        return True
        
    except Exception as e:
        print("❌ Database connection failed!")
        print(f"🔴 Error: {str(e)}")
        print("=" * 50)
        print("💡 Tips:")
        print("   1. Check if PostgreSQL is running")
        print("   2. Verify DB_URL in .env file")
        print("   3. Ensure database exists and credentials are correct")
        print("=" * 50)
        return False


def get_db_connection():
    """Get a database connection with error handling"""
    try:
        conn = psycopg2.connect(settings.db_url)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None