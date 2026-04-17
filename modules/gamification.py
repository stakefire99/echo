# modules/gamification.py
"""Gamification system for ECHO - Awards badges and tracks achievements"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

class Gamification:
    def __init__(self, event_logger, memory_engine):
        self.event_logger = event_logger
        self.memory_engine = memory_engine
        self.achievements_file = "data/achievements.json"
        self.achievements = self._load_achievements()
        
        # Define all possible badges
        self.badge_definitions = {
            "early_bird": {"name": "🐦 Early Bird", "description": "Logged 10 activities before 9 AM"},
            "night_owl": {"name": "🦉 Night Owl", "description": "Most active after 10 PM"},
            "streak_master": {"name": "🔥 Streak Master", "description": "7-day logging streak"},
            "streak_legend": {"name": "⚡ Streak Legend", "description": "30-day logging streak"},
            "focus_god": {"name": "🎯 Focus God", "description": "4+ hours of focused work in one day"},
            "consistent_king": {"name": "👑 Consistent King", "description": "90% consistency score for a month"},
            "productivity_pro": {"name": "📈 Productivity Pro", "description": "50+ activities in a week"},
            "diversity_master": {"name": "🎨 Diversity Master", "description": "Logged 5+ different activity types"},
            "weekend_warrior": {"name": "⚔️ Weekend Warrior", "description": "Productive on both Saturday and Sunday"},
            "comeback_kid": {"name": "🌟 Comeback Kid", "description": "50% increase in activity after a low week"}
        }
    
    def _load_achievements(self) -> Dict:
        """Load earned achievements from file"""
        if os.path.exists(self.achievements_file):
            with open(self.achievements_file, 'r') as f:
                return json.load(f)
        return {"earned": [], "last_checked": None}
    
    def _save_achievements(self):
        """Save earned achievements to file"""
        with open(self.achievements_file, 'w') as f:
            json.dump(self.achievements, f, indent=2)
    
    def check_and_award_badges(self) -> List[Dict]:
        """Check all conditions and award new badges"""
        new_badges = []
        
        # Get data
        df = self.event_logger.get_events(start_date=datetime.now() - timedelta(days=30))
        if df.empty:
            return new_badges
        
        earned_names = [b["name"] for b in self.achievements["earned"]]
        
        # Check Early Bird
        if "early_bird" not in earned_names:
            early_events = df[df['timestamp'].dt.hour < 9]
            if len(early_events) >= 10:
                new_badges.append(self._award_badge("early_bird"))
        
        # Check Night Owl
        if "night_owl" not in earned_names:
            night_events = df[df['timestamp'].dt.hour >= 22]
            if len(night_events) > len(df) / 2:
                new_badges.append(self._award_badge("night_owl"))
        
        # Check Streak Master (7 days)
        if "streak_master" not in earned_names:
            streak = self._calculate_streak()
            if streak >= 7:
                new_badges.append(self._award_badge("streak_master"))
        
        # Check Streak Legend (30 days)
        if "streak_legend" not in earned_names:
            streak = self._calculate_streak()
            if streak >= 30:
                new_badges.append(self._award_badge("streak_legend"))
        
        # Check Focus God
        if "focus_god" not in earned_names:
            daily_duration = df.groupby(df['timestamp'].dt.date)['duration_minutes'].sum()
            if (daily_duration / 60 >= 4).any():
                new_badges.append(self._award_badge("focus_god"))
        
        # Check Productivity Pro
        if "productivity_pro" not in earned_names:
            weekly = df.groupby(df['timestamp'].dt.isocalendar().week).size()
            if (weekly >= 50).any():
                new_badges.append(self._award_badge("productivity_pro"))
        
        # Check Diversity Master
        if "diversity_master" not in earned_names:
            if df['event_type'].nunique() >= 5:
                new_badges.append(self._award_badge("diversity_master"))
        
        # Check Consistency
        if "consistent_king" not in earned_names:
            weekly_patterns = self.memory_engine.user_profile.get("behavioral_patterns", {}).get("weekly", {})
            if weekly_patterns.get("consistency_score", 0) > 0.9:
                new_badges.append(self._award_badge("consistent_king"))
        
        # Check Comeback Kid
        if "comeback_kid" not in earned_names:
            weeks = df.groupby(df['timestamp'].dt.isocalendar().week).size()
            if len(weeks) >= 2:
                last_week = weeks.iloc[-1] if len(weeks) >= 1 else 0
                prev_week = weeks.iloc[-2] if len(weeks) >= 2 else 0
                if prev_week > 0 and (last_week - prev_week) / prev_week > 0.5:
                    new_badges.append(self._award_badge("comeback_kid"))
        
        if new_badges:
            self._save_achievements()
        
        return new_badges
    
    def _award_badge(self, badge_id: str) -> Dict:
        """Award a specific badge"""
        badge = self.badge_definitions[badge_id]
        badge_data = {
            "id": badge_id,
            "name": badge["name"],
            "description": badge["description"],
            "earned_at": datetime.now().isoformat()
        }
        self.achievements["earned"].append(badge_data)
        return badge_data
    
    def _calculate_streak(self) -> int:
        """Calculate current logging streak in days"""
        df = self.event_logger.get_events()
        if df.empty:
            return 0
        
        dates = sorted(df['timestamp'].dt.date.unique())
        if not dates:
            return 0
        
        streak = 1
        current_date = dates[-1]
        
        for i in range(len(dates)-2, -1, -1):
            if (current_date - dates[i]).days == 1:
                streak += 1
                current_date = dates[i]
            else:
                break
        
        return streak
    
    def get_earned_badges(self) -> List[Dict]:
        """Get list of earned badges"""
        return self.achievements["earned"]
    
    def get_level(self) -> Dict:
        """Calculate user level based on total activity"""
        df = self.event_logger.get_events()
        total_events = len(df)
        
        # Level formula: Level = floor(log10(total_events + 1) * 10)
        level = int((total_events ** 0.3) * 2) + 1
        next_level_events = int(((level + 1) / 2) ** 3.33)
        
        return {
            "current_level": level,
            "total_events": total_events,
            "next_level_events": next_level_events,
            "progress": min(100, int((total_events / next_level_events) * 100)) if next_level_events > 0 else 0
        }
    
    def get_statistics(self) -> Dict:
        """Get gamification statistics"""
        df = self.event_logger.get_events()
        
        return {
            "total_events": len(df),
            "unique_days": df['date'].nunique() if not df.empty else 0,
            "streak": self._calculate_streak(),
            "badges_earned": len(self.achievements["earned"]),
            "level": self.get_level()["current_level"]
        }