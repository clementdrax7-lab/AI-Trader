import pandas as pd
from datetime import datetime
import zoneinfo

class ICTKillzoneToolkit:
    """Replicates LuxAlgo ICT Killzone session logic in EST/EDT."""
    def __init__(self):
        # Precise ICT algorithm session times mapped in New York Time (24h format)
        self.sessions = {
            "ASIA_RANGE":   {"start": "20:00", "end": "00:00"},
            "LONDON_KILL":  {"start": "02:00", "end": "05:00"},
            "NY_AM_KILL":   {"start": "07:00", "end": "10:00"},
            "LONDON_CLOSE": {"start": "10:00", "end": "12:00"},
            "NY_PM_KILL":   {"start": "13:30", "end": "16:00"}
        }
        self.ny_tz = zoneinfo.ZoneInfo("America/New_York")

    def get_active_zone(self, dt: datetime) -> str:
        """Translates localized incoming candle data timestamps into active New York session blocks."""
        # Convert incoming execution timestamp into New York time structure
        ny_time = dt.astimezone(self.ny_tz)
        current_time_str = ny_time.strftime("%H:%M")
        
        for zone_name, times in self.sessions.items():
            if times["start"] <= current_time_str <= times["end"]:
                return zone_name
        return "NO_ZONE"
