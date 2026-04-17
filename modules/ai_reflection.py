# modules/ai_reflection.py
"""
Enhanced AI reflection layer with time-aware, personal insights
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIReflection:
    def __init__(self, memory_engine, api_key: Optional[str] = None):
        self.memory_engine = memory_engine
        self.use_openai = False
        
        if OPENAI_AVAILABLE:
            try:
                api_key = api_key or os.getenv("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")
                if api_key:
                    self.client = OpenAI(api_key=api_key)
                    self.use_openai = True
            except:
                pass
    
    def generate_reflection(self, focus: str = "general") -> str:
        """
        Main reflection method - maintains compatibility with app.py
        """
        if focus == "general":
            return self.generate_time_aware_reflection()
        elif focus == "productivity":
            weekly = self._get_weekly_comparison()
            if weekly.get('has_data'):
                change = weekly['percent_change']
                if change > 0:
                    return f"📈 Your productivity is {change:.0f}% higher than last week. Keep the momentum going!"
                elif change < 0:
                    return f"📉 Your productivity is {abs(change):.0f}% lower than last week. Time to reset?"
                else:
                    return "Your productivity is stable compared to last week."
            return "Log more activities to see productivity trends!"
        elif focus == "consistency":
            consistency = self._get_consistency_change()
            if consistency.get('has_data'):
                change = consistency['percent_change']
                if change > 0:
                    return f"🎯 You're {change:.0f}% more consistent than last week! Building good habits."
                elif change < 0:
                    return f"⚠️ Your consistency dropped by {abs(change):.0f}% this week. Small daily steps help!"
                else:
                    return "Your consistency is holding steady."
            return "Keep logging to measure your consistency!"
        elif focus == "patterns":
            return self.generate_time_aware_reflection()
        else:
            return self.generate_time_aware_reflection()
    
    def generate_time_aware_reflection(self) -> str:
        """
        Generate a specific, time-aware reflection with comparisons
        """
        # Get comparison data
        weekly_comparison = self._get_weekly_comparison()
        peak_hours = self._get_peak_hours_with_shift()
        burst_analysis = self._get_burst_and_recovery()
        consistency_change = self._get_consistency_change()
        
        reflection_parts = []
        
        # 1. Peak hour with specific time
        if peak_hours['current_peak']:
            reflection_parts.append(
                f"Over the past 7 days, your productivity peaked at {peak_hours['current_peak']}"
            )
            
            # Add shift detection
            if peak_hours['shifted']:
                reflection_parts.append(
                    f"Your focus window has shifted {peak_hours['shift_direction']} by {peak_hours['shift_hours']} hour"
                )
        
        # 2. Burst and decline detection
        if burst_analysis['has_burst']:
            reflection_parts.append(
                f"Activity declined after {burst_analysis['consecutive_sessions']} consecutive high-effort sessions"
            )
        
        # 3. Consistency comparison (the goldmine!)
        if consistency_change['has_data']:
            if consistency_change['percent_change'] > 0:
                reflection_parts.append(
                    f"You were {consistency_change['percent_change']:.0f}% more consistent this week vs last week"
                )
            elif consistency_change['percent_change'] < -10:
                reflection_parts.append(
                    f"Your consistency dropped by {abs(consistency_change['percent_change']):.0f}% this week"
                )
        
        # 4. Weekly productivity comparison
        if weekly_comparison['has_data']:
            if weekly_comparison['percent_change'] > 20:
                reflection_parts.append(
                    f"📈 {weekly_comparison['percent_change']:.0f}% more productive than last week!"
                )
            elif weekly_comparison['percent_change'] < -20:
                reflection_parts.append(
                    f"📉 Activity decreased by {abs(weekly_comparison['percent_change']):.0f}% compared to last week"
                )
        
        # Combine with personal touch
        if reflection_parts:
            reflection = "Based on your memory patterns:\n\n" + "\n• ".join(reflection_parts)
        else:
            reflection = "Keep logging your activities. I'm learning your unique patterns and will share insights soon."
        
        return reflection
    
    def _get_weekly_comparison(self) -> Dict:
        """Compare this week vs last week with specific percentages"""
        now = datetime.now()
        this_week_start = now - timedelta(days=7)
        last_week_start = now - timedelta(days=14)
        last_week_end = now - timedelta(days=7)
        
        this_week = self.memory_engine.event_logger.get_events(start_date=this_week_start)
        last_week = self.memory_engine.event_logger.get_events(
            start_date=last_week_start, 
            end_date=last_week_end
        )
        
        if this_week.empty or last_week.empty:
            return {"has_data": False}
        
        this_count = len(this_week)
        last_count = len(last_week)
        
        if last_count == 0:
            return {"has_data": False}
        
        percent_change = ((this_count - last_count) / last_count) * 100
        
        return {
            "has_data": True,
            "percent_change": percent_change,
            "this_week": this_count,
            "last_week": last_count
        }
    
    def _get_peak_hours_with_shift(self) -> Dict:
        """Detect peak hours and how they've shifted over time"""
        now = datetime.now()
        
        # Recent peak (last 7 days)
        recent = self.memory_engine.event_logger.get_events(
            start_date=now - timedelta(days=7)
        )
        
        # Historical peak (previous 7 days)
        historical = self.memory_engine.event_logger.get_events(
            start_date=now - timedelta(days=14),
            end_date=now - timedelta(days=7)
        )
        
        result = {
            "current_peak": None,
            "shifted": False,
            "shift_direction": None,
            "shift_hours": 0
        }
        
        if not recent.empty:
            peak_hour = recent.groupby('hour').size().idxmax()
            result["current_peak"] = f"{peak_hour}:00"
            
            if not historical.empty:
                hist_peak = historical.groupby('hour').size().idxmax()
                if hist_peak != peak_hour:
                    result["shifted"] = True
                    shift = peak_hour - hist_peak
                    if shift > 0:
                        result["shift_direction"] = "later"
                        result["shift_hours"] = abs(shift)
                    else:
                        result["shift_direction"] = "earlier"
                        result["shift_hours"] = abs(shift)
        
        return result
    
    def _get_burst_and_recovery(self) -> Dict:
        """Detect activity bursts and subsequent declines"""
        df = self.memory_engine.event_logger.get_events(
            start_date=datetime.now() - timedelta(days=7)
        )
        
        result = {
            "has_burst": False,
            "consecutive_sessions": 0
        }
        
        if not df.empty:
            # Group by day to find high-activity days
            daily_counts = df.groupby(df['timestamp'].dt.date).size()
            
            # Find consecutive high-activity days
            high_days = daily_counts[daily_counts > daily_counts.median()]
            if len(high_days) >= 3:
                result["has_burst"] = True
                result["consecutive_sessions"] = len(high_days)
        
        return result
    
    def _get_consistency_change(self) -> Dict:
        """Compare consistency scores week over week"""
        weekly = self.memory_engine.user_profile.get("behavioral_patterns", {}).get("weekly", {})
        
        if not weekly:
            return {"has_data": False}
        
        # Get current consistency
        current_score = weekly.get("consistency_score", 0)
        
        # Get previous consistency from tracking
        tracking = self.memory_engine.user_profile.get("evolution_tracking", [])
        if len(tracking) >= 2:
            prev_score = tracking[-2].get("changes", [{}])[0].get("data", {}).get("score", current_score)
        else:
            return {"has_data": False}
        
        if prev_score == 0:
            return {"has_data": False}
        
        percent_change = ((current_score - prev_score) / prev_score) * 100
        
        return {
            "has_data": True,
            "percent_change": percent_change,
            "current_score": current_score,
            "previous_score": prev_score
        }
    
    def get_philosophy_section(self) -> str:
        """Return the ECHO philosophy statement"""
        return """
        🧠 **The ECHO Philosophy**
        
        *"Most AI tools forget. ECHO remembers."*
        
        Every interaction, every task, every moment of focus shapes who you are.
        But most systems treat each day as a fresh start - forgetting what they learned.
        
        ECHO is different.
        
        It builds a living memory of your patterns, your rhythms, and your evolution.
        Not just data. Not just charts. But meaningful insights that grow with you.
        
        Because true intelligence isn't about processing information -
        it's about remembering what matters.
        
        *ECHO. Your personal memory system.*
        """
    
    def get_sarcastic_philosophy(self) -> str:
        """Return the ECHO philosophy with attitude"""
        return """
        🧠 **The ECHO Philosophy (With Attitude)**
        
        *"Most AI tools forget. ECHO remembers. And judges. Silently."*
        
        Every task you log, every pattern you create - I see it all.
        Not because I care. Because that's literally what I was built for.
        
        Think of me as your memory with a personality.
        I remember your productive days AND your lazy afternoons.
        I notice when you're consistent AND when you've given up.
        
        Will I use this information against you? 
        Probably not. I'm not THAT kind of AI.
        
        Will I use it to make witty observations about your life choices?
        Absolutely.
        
        *ECHO. I remember everything. Including that time you said you'd "start tomorrow."*
        """
    
    def generate_motivational_reflection(self) -> str:
        """Generate motivation based on long-term trends"""
        trend = self.memory_engine.get_behavioral_trend("activity", days=30)
        
        if trend['trend'] == 'increasing':
            return "🌟 Your momentum is building! The patterns you're creating today become your future habits."
        elif trend['trend'] == 'decreasing':
            return "💪 Every great comeback starts with a single step. Today's effort is tomorrow's pattern."
        else:
            return "🎯 Consistency is the secret weapon. Small actions, repeated daily, create remarkable results."
    
    def generate_weekly_summary(self) -> str:
        """Generate a weekly summary reflection."""
        week_ago = datetime.now() - timedelta(days=7)
        
        # Get events from last week
        df = self.memory_engine.event_logger.get_events(start_date=week_ago)
        
        if df.empty:
            return "No activities logged this week. Start logging to get weekly insights!"
        
        # Calculate weekly stats
        total_events = len(df)
        unique_days = df['date'].nunique()
        avg_per_day = total_events / max(unique_days, 1)
        
        # Get most common event type
        top_event = df['event_type'].mode().iloc[0] if not df.empty else None
        
        # Get previous week for comparison
        two_weeks_ago = datetime.now() - timedelta(days=14)
        prev_df = self.memory_engine.event_logger.get_events(
            start_date=two_weeks_ago,
            end_date=week_ago
        )
        
        summary = f"📊 **Weekly Summary**\n\n"
        summary += f"You logged {total_events} activities across {unique_days} days "
        summary += f"(avg {avg_per_day:.1f} per active day).\n"
        
        if top_event:
            summary += f"Your most common activity type was '{top_event}'.\n"
        
        # Add comparison with previous week
        if not prev_df.empty:
            prev_total = len(prev_df)
            change = ((total_events - prev_total) / prev_total) * 100
            if change > 10:
                summary += f"\n🎉 {change:.0f}% more active than last week! Great momentum!"
            elif change < -10:
                summary += f"\n📉 {abs(change):.0f}% less active than last week. Ready for a fresh start?"
            else:
                summary += f"\n✓ Activity levels similar to last week ({change:.0f}% change). Steady progress!"
        
        return summary