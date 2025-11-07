from datetime import datetime, timedelta, timezone

class SmartDataCache:
    def __init__(self):
        self.data = None
        self.last_updated = None
        self.current_gw = None
        self.update_hours = [5, 17]  # 5am and 5pm UTC
        # Add a dictionary for storing arbitrary cached items
        self.cache_items = {}
    
    # ... (Original methods: get_next_update_time, should_refresh, update) ...
    
    def get_next_update_time(self):
        """Calculate when the next data update will happen"""
        now = datetime.now(timezone.utc)
        
        for hour in self.update_hours:
            next_update = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_update > now:
                return next_update
        
        tomorrow = now + timedelta(days=1)
        next_update = tomorrow.replace(hour=self.update_hours[0], minute=0, second=0, microsecond=0)
        return next_update
    
    def should_refresh(self):
        if self.last_updated is None:
            print("❓ Cache is empty - need to fetch data")
            return True
        
        now = datetime.now(timezone.utc)
        
        for hour in self.update_hours:
            update_time_today = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if self.last_updated < update_time_today <= now:
                print(f"⏰ Update time passed ({hour}:00 UTC) - fetching fresh data")
                return True
        
        yesterday = now - timedelta(days=1)
        for hour in self.update_hours:
            update_time_yesterday = yesterday.replace(hour=hour, minute=0, second=0, microsecond=0)
            if self.last_updated < update_time_yesterday <= now:
                print(f"⏰ Update time passed ({hour}:00 UTC yesterday) - fetching fresh data")
                return True
        
        next_update = self.get_next_update_time()
        time_until_next = next_update - now
        hours = int(time_until_next.total_seconds() // 3600)
        minutes = int((time_until_next.total_seconds() % 3600) // 60)
        print(f"✓ Using cached data - next update in {hours}h {minutes}m")
        return False
    
    def update(self, data, gw):
        self.data = data
        self.current_gw = gw
        self.last_updated = datetime.now(timezone.utc)
        
        next_update = self.get_next_update_time()
        print(f"✓ Cache updated at {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Next scheduled update: {next_update.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    def get(self, key=None):
        """
        Get cached data. 
        If no key is provided, returns the main FPL data.
        If a key is provided, returns the cached item for that key.
        """
        if key is None:
            # Original behavior - return FPL data
            if self.data is not None:
                return self.data, self.current_gw
            return None, None
        else:
            # New behavior - return cached item by key
            return self.cache_items.get(key)
    
    def set(self, key, value):
        """
        Set a cached item with a key.
        Used for caching things like LLM headlines.
        """
        self.cache_items[key] = value
        
    # --- NEW METHOD ADDED FOR SAFE DELETION ---
    def delete(self, key):
        """
        Safely delete a cached item by key, preventing a KeyError.
        """
        if key in self.cache_items:
            del self.cache_items[key]
            return True
        return False
    # ------------------------------------------

    def is_empty(self):
        return self.data is None
