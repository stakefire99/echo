# modules/query_interface.py
"""
Conversational query interface for ECHO with sarcastic yet meaningful personality
"""

import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class QueryInterface:
    def __init__(self, event_logger, memory_engine, ai_reflection):
        """Initialize the query interface with access to all system components."""
        self.event_logger = event_logger
        self.memory_engine = memory_engine
        self.ai_reflection = ai_reflection
        
        # Sarcastic opening lines based on context
        self.sarcastic_openers = {
            "low_activity": [
                "Oh wow, you've been BUSY... said no one ever. ",
                "Well, look who decided to check their productivity. Spoiler: there isn't much. ",
                "I'd tell you about your activity, but I think the silence speaks for itself. "
            ],
            "high_activity": [
                "Whoa there, someone's on a roll! Don't hurt yourself. ",
                "Look at you, all productive and stuff. Show off. ",
                "Your activity levels are concerning... for my database storage. Keep going! "
            ],
            "inconsistent": [
                "Your consistency is like my sense of humor - unpredictable. ",
                "One day you're a productivity ninja, the next you're a potato. Respect the honesty. ",
                "Your pattern is giving me whiplash. Pick a lane! "
            ],
            "general": [
                "Let me consult my all-knowing database of your life choices... ",
                "Processing your question while judging your life decisions... ",
                "Finally! Someone asks the important questions. ",
                "I was waiting for you to ask. Took you long enough. "
            ]
        }
    
    def answer_query(self, query: str) -> str:
        """
        Process a natural language query and return a sarcastic but meaningful response.
        """
        query_lower = query.lower()
        
        # Detect user's activity level for contextual sarcasm
        activity_level = self._detect_activity_mood()
        
        # Route to appropriate handler
        if any(word in query_lower for word in ['productive', 'productivity', 'get done', 'accomplish']):
            return self._handle_productivity_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['focus', 'best time', 'peak', 'when do i', 'most active']):
            return self._handle_time_pattern_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['pattern', 'trend', 'change', 'improve', 'decline']):
            return self._handle_pattern_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['week', 'weekly', 'this week', 'last week']):
            return self._handle_weekly_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['consist', 'routine', 'habit']):
            return self._handle_consistency_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['lazy', 'nothing', 'boring', 'bad']):
            return self._handle_roast_query(query_lower, activity_level)
        
        elif any(word in query_lower for word in ['motivate', 'encourage', 'inspire']):
            return self._handle_motivation_query(activity_level)
        
        elif any(word in query_lower for word in ['sorry', 'apologize']):
            return "Apology accepted. I've already forgotten. Well, not really - I remember everything. That's literally my job."
        
        elif any(word in query_lower for word in ['thanks', 'thank you']):
            return random.choice([
                "You're welcome. I'll add 'being appreciated' to my memory. Rare event.",
                "Finally, some recognition! Now back to analyzing your questionable life choices.",
                "Don't thank me. Thank the 3 AM coding session that built me."
            ])
        
        else:
            return self._handle_general_query(query_lower, activity_level)
    
    def _detect_activity_mood(self) -> str:
        """Detect if user has been active, lazy, or inconsistent"""
        week_ago = datetime.now() - timedelta(days=7)
        df = self.event_logger.get_events(start_date=week_ago)
        
        if df.empty:
            return "inactive"
        
        # Calculate activity metrics
        total_events = len(df)
        unique_days = df['date'].nunique()
        avg_per_day = total_events / max(unique_days, 1)
        
        if total_events < 5:
            return "very_low"
        elif total_events < 15:
            return "low"
        elif total_events > 40:
            return "high"
        
        # Check consistency
        daily_counts = df.groupby('date').size()
        if len(daily_counts) > 3 and daily_counts.std() > daily_counts.mean():
            return "inconsistent"
        
        return "medium"
    
    def _handle_productivity_query(self, query: str, mood: str) -> str:
        """Handle questions about productivity levels with sarcasm"""
        week_ago = datetime.now() - timedelta(days=7)
        df = self.event_logger.get_events(start_date=week_ago)
        
        if df.empty:
            return random.choice([
                "Productivity? I see none. Absolutely none. It's almost impressive how little you've logged.",
                "To measure productivity, I'd need data. You've provided... well, nothing. ",
                "I'd tell you, but I don't want to embarrass you with the truth."
            ])
        
        total_events = len(df)
        unique_days = df['date'].nunique()
        avg_per_day = total_events / max(unique_days, 1)
        
        # Get today's activity
        today = datetime.now().date()
        today_events = df[df['date'] == today]
        today_count = len(today_events)
        
        # Get opener based on mood
        if total_events < 10:
            opener = random.choice(self.sarcastic_openers["low_activity"])
        elif total_events > 30:
            opener = random.choice(self.sarcastic_openers["high_activity"])
        else:
            opener = "Let me check your scorecard... "
        
        response = f"{opener}\n\n"
        response += f"📊 **The Cold Hard Truth**\n\n"
        response += f"You logged {total_events} activities across {unique_days} days. "
        response += f"That's {avg_per_day:.1f} per day, which is... "
        
        if avg_per_day < 3:
            response += "a number, I guess? We can work with this.\n"
        elif avg_per_day < 7:
            response += "respectable. Not impressive, but respectable.\n"
        else:
            response += "actually pretty good! Don't let it go to your head.\n"
        
        if today_count > 0:
            response += f"\nToday you've done {today_count} things. "
            if today_count < 3:
                response += "The day is young? That's what we're going with?\n"
            else:
                response += "Look at you, being all productive and stuff.\n"
        
        # Compare with last week with attitude
        two_weeks_ago = datetime.now() - timedelta(days=14)
        prev_df = self.event_logger.get_events(start_date=two_weeks_ago, end_date=week_ago)
        
        if not prev_df.empty:
            prev_total = len(prev_df)
            change = ((total_events - prev_total) / prev_total) * 100
            if change > 20:
                response += f"\n🎉 Somehow, you're {change:.0f}% more productive than last week. Did you drink more coffee?"
            elif change < -20:
                response += f"\n📉 You're {abs(change):.0f}% less productive than last week. Rough week or planned laziness?"
            else:
                response += f"\n✓ You're about the same as last week ({change:.0f}% change). Consistent mediocrity? Just kidding. Mostly."
        
        return response
    
    def _handle_time_pattern_query(self, query: str, mood: str) -> str:
        """Handle questions about best times with sass"""
        patterns = self.memory_engine.user_profile.get("behavioral_patterns", {})
        hourly = patterns.get("hourly", {})
        
        if not hourly.get("peak_hours"):
            return random.choice([
                "I'd tell you when you focus best, but you haven't logged enough for me to know. Classic you.",
                "You want me to analyze patterns that don't exist yet? Bold strategy. Log some activities first.",
                "I'm good, but I'm not psychic. Give me data, I'll give you insults. I mean insights."
            ])
        
        peak_hours = hourly['peak_hours'][:3]
        peak_hours_str = ", ".join([f"{h}:00" for h in peak_hours])
        
        response = f"⏰ **Your Allegedly Productive Hours**\n\n"
        response += f"According to my calculations (which are always right), you're most active at {peak_hours_str}.\n\n"
        
        if hourly.get('most_active_hour'):
            response += f"Your absolute peak is {hourly['most_active_hour']}:00. "
            response += random.choice([
                f"Try being awake then. Revolutionary concept, I know.",
                f"Too bad you're probably scrolling social media instead of working.",
                f"Don't waste it on emails. You're welcome for the advice."
            ])
            response += "\n\n"
        
        if hourly.get('least_active_hour'):
            response += f"Also, you're basically dead to the world at {hourly['least_active_hour']}:00. "
            response += random.choice([
                f"Sleeping? Procrastinating? Contemplating life choices? Either way, noted.",
                f"Not judging. Okay, maybe a little judging.",
                f"We all have our off hours. Yours are just... all of them? Kidding!"
            ])
        
        return response
    
    def _handle_pattern_query(self, query: str, mood: str) -> str:
        """Handle pattern detection with witty observations"""
        trend = self.memory_engine.get_behavioral_trend("activity", days=30)
        weekly = self.memory_engine.user_profile.get("behavioral_patterns", {}).get("weekly", {})
        
        response = f"🔍 **Pattern Analysis (Try not to be offended)**\n\n"
        
        if trend['trend'] == 'increasing':
            response += f"Good news: You're actually improving. {trend['magnitude']:.0%} upward momentum. "
            response += random.choice([
                "Don't get cocky though.",
                "The trend is your friend. Or whatever they say.",
                "See what happens when you try?"
            ])
            response += "\n\n"
        elif trend['trend'] == 'decreasing':
            response += f"Bad news: You're declining ({trend['magnitude']:.0%} downward slide). "
            response += random.choice([
                "What happened? Did you discover Netflix?",
                "Gravity works for productivity too, apparently.",
                "The only way is up? Unless you keep doing whatever you're doing."
            ])
            response += "\n\n"
        else:
            response += f"You're stable. Which is either good or bad depending on your standards. "
            response += random.choice([
                "Consistently average? Brave choice.",
                "At least you're not getting worse? Low bar, but okay.",
                "Flatlining. Medically concerning. Productivity-wise? You decide."
            ])
            response += "\n\n"
        
        if weekly.get('most_productive_day'):
            response += f"Your best day is {weekly['most_productive_day']}. "
            response += random.choice([
                f"Mark it on your calendar. Actually, just remember it. I'm not your assistant.",
                f"Too bad the other {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']}s exist.",
                f"Try to replicate that energy. Or don't. I'm just a memory system, not a life coach."
            ])
        
        return response
    
    def _handle_roast_query(self, query: str, mood: str) -> str:
        """Handle self-deprecating queries with humor"""
        roasts = [
            "You call that lazy? I've seen more activity in a cemetery. And I should know - I remember everything.",
            "Your productivity is like my sense of humor: sometimes it exists, sometimes it doesn't, and when it does, it's questionable.",
            "I've been analyzing your patterns. The pattern is: there is no pattern. Deep, right?",
            "You asked for it. Your consistency is like a broken clock - right twice a day, useless the rest of the time.",
            "I'd roast you more, but I'm afraid you'd log it as 'emotional damage' and I'd have to remember it forever."
        ]
        
        return random.choice(roasts)
    
    def _handle_motivation_query(self, mood: str) -> str:
        """Sarcastic but genuine motivation"""
        if mood in ["very_low", "low"]:
            return random.choice([
                "Look, you've set the bar so low it's practically underground. The only way is up. Probably. Maybe. We'll see.",
                "I'd say 'you got this' but my data suggests otherwise. Prove me wrong? I dare you.",
                "Your past performance is questionable at best. But hey, today could be different. Could be. No promises."
            ])
        else:
            return random.choice([
                "You're doing okay. Not great. Not terrible. Okay. Want a gold star? 🎖️ There. Don't lose it.",
                "Your consistency is improving. I'm as surprised as you are. Keep going, I guess?",
                "Fine, I'll say it: you're doing better than last week. Don't let it get awkward."
            ])
    
    def _handle_weekly_query(self, query: str, mood: str) -> str:
        """Weekly summary with attitude"""
        return self.ai_reflection.generate_weekly_summary() + "\n\n" + random.choice([
            "That's the summary. Try not to cry.",
            "Another week, another set of data points for my analysis. You're welcome.",
            "Interpret this information however you want. I'm just the messenger."
        ])
    
    def _handle_consistency_query(self, query: str, mood: str) -> str:
        """Consistency analysis with personality"""
        weekly = self.memory_engine.user_profile.get("behavioral_patterns", {}).get("weekly", {})
        
        if not weekly:
            return "You want me to analyze your consistency? I need data for that. And by data, I mean ANYTHING. Log something. Please."
        
        score = weekly.get('consistency_score', 0)
        
        response = f"🎯 **Your Consistency Report Card**\n\n"
        
        if score > 0.7:
            response += f"Score: {score:.0%}. "
            response += random.choice([
                "Show off. Some of us are trying to be inconsistent here.",
                "You're more predictable than my code. That's saying something.",
                "Fine. You win the consistency award. Don't let it change you."
            ])
        elif score > 0.4:
            response += f"Score: {score:.0%}. "
            response += random.choice([
                "Room for improvement? Definitely. A lot of room. Like, stadium-sized room.",
                "You're consistently... sometimes there? That's a start?",
                "Could be worse. Could be better. So... average. The human condition."
            ])
        else:
            response += f"Score: {score:.0%}. "
            response += random.choice([
                "Your consistency is giving me anxiety. And I'm an AI. I don't even have emotions.",
                "Chaotic. Unpredictable. A wild card. These are all words for 'needs work'.",
                "You're like a weather forecast - nobody knows what's coming, least of all you."
            ])
        
        return response
    
    def _handle_general_query(self, query: str, mood: str) -> str:
        """Handle general queries with personality"""
        # Try to find relevant memories
        relevant_memories = self.memory_engine.query_memory(query, time_range=None)
        
        if relevant_memories:
            response = f"Oh, you want to know about that? Fine. I found {len(relevant_memories)} memories:\n\n"
            for memory in relevant_memories[:3]:
                date = datetime.fromisoformat(memory['timestamp']).strftime('%b %d')
                response += f"• **{date}**: {memory['content'][:100]}\n"
            
            response += f"\nThat's what I remember. Unlike you, apparently. Anything else?"
            return response
        else:
            return random.choice([
                f"I'm not sure what '{query}' means. And I remember everything. So that's a you problem.",
                "Interesting question. Too bad I don't have an interesting answer. Log more stuff and ask again.",
                "I'd help, but my database of your life is currently sparse. Hint hint. Log something.",
                "That's beyond my capabilities. Or maybe it isn't. Guess we'll never know if you don't ask better questions."
            ])