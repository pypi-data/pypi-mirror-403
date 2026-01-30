import psutil
import psycopg2
from utils.config import settings

class Bouncer:
    """
    Guard class to prevent system overload by blocking expensive 
    operations when resources are scarce.
    """
    
    @staticmethod
    def check_system_cpu(threshold_percent: float = 80.0) -> bool:
        """Check if system CPU is below threshold."""
        try:
            # Check system-wide CPU usage (non-blocking)
            # The first call to cpu_percent returns 0.0 unless interval is provided, 
            # but providing interval blocks. 
            # Better strategy: Call it once, if 0.0, assume safe or use load avg.
            # actually psutil.cpu_percent(interval=None) returns time since last call.
            # For simplicity/robustness, we can use psutil.getloadavg() / logical_cpus * 100
            
            cpu_usage = psutil.cpu_percent(interval=0.1) # Short block to get valid reading
            
            if cpu_usage > threshold_percent:
                print(f"🛑 BOUNCER: High CPU usage detected ({cpu_usage}%) - Skipping Analysis")
                return False
            return True
        except Exception as e:
            print(f"⚠️ BOUNCER: Failed to check CPU usage: {str(e)}")
            return True # Fail open to allow functionality if monitoring fails

    @staticmethod
    def check_db_connections(conn_threshold_percent: float = 90.0) -> bool:
        """Check if DB active connections are below threshold."""
        try:
            conn = psycopg2.connect(settings.db_url)
            cur = conn.cursor()
            
            # Get max connections
            cur.execute("SHOW max_connections;")
            max_conns = int(cur.fetchone()[0])
            
            # Get active connections
            # We exclude our own monitoring connection roughly, but counting all active is safer
            cur.execute("SELECT count(*) FROM pg_stat_activity;")
            current_conns = int(cur.fetchone()[0])
            
            cur.close()
            conn.close()
            
            usage_percent = (current_conns / max_conns) * 100
            
            if usage_percent > conn_threshold_percent:
                print(f"🛑 BOUNCER: High DB connection usage detected ({current_conns}/{max_conns} - {usage_percent:.1f}%) - Skipping Analysis")
                return False
                
            return True
            
        except Exception as e:
            print(f"⚠️ BOUNCER: Failed to check DB health: {str(e)}")
            # If we can't check DB health, better not to add load
            return False

    @staticmethod
    def is_safe_to_operate() -> bool:
        """Comprehensive system safety check."""
        if not Bouncer.check_system_cpu():
            return False
            
        if not Bouncer.check_db_connections():
            return False
            
        return True
