"""
Advanced Task Prioritization Algorithm
Based on scientific research and modern productivity systems
"""

from datetime import datetime, timedelta

# Category weights based on life impact research
CATEGORY_WEIGHTS = {
    'health': 2.0,       # Highest priority (well-being)
    'finance': 1.8,      # High impact on security  
    'work': 1.5,         # Career/income
    'learning': 1.3,
    'personal': 1.0,
    'general': 1.0
}

def calculate_master_priority(task):
    """
    Master priority algorithm combining multiple proven techniques:
    - Eisenhower Matrix (Urgent-Important)
    - WSJF (Weighted Shortest Job First)
    - Energy optimization
    - Context switching minimization
    - Task aging penalty
    - Keyword detection
    
    Returns: (score 0-100, reasons list, time_recommendation)
    """
    
    score = 0
    reasons = []
    
    # === 1. URGENCY SCORE (30% weight) - Eisenhower Matrix ===
    urgency_score = calculate_urgency_score(task)
    score += urgency_score * 0.30
    
    if urgency_score >= 95:
        reasons.append("⚠️ OVERDUE - Critical!")
    elif urgency_score >= 85:
        reasons.append("📅 Due today")
    elif urgency_score >= 70:
        reasons.append("📅 Due very soon")
    
    # === 2. IMPORTANCE SCORE (25% weight) ===
    importance_score = (task.importance or 3) * 20  # 1-5 scale to 0-100
    score += importance_score * 0.25
    
    if task.importance >= 4:
        reasons.append(f"⭐ High importance ({task.importance}/5)")
    
    # === 3. EFFORT OPTIMIZATION (15% weight) - WSJF ===
    # Favors quick wins (15 min) and medium tasks (30-60 min)
    # Penalizes very long tasks unless importance is high
    estimated_mins = task.estimated_time or 30
    
    if estimated_mins <= 15:
        effort_score = 100  # Quick win!
        reasons.append("⚡ Quick win (15 min)")
    elif estimated_mins <= 30:
        effort_score = 90
    elif estimated_mins <= 60:
        effort_score = 70
    elif estimated_mins <= 120:
        effort_score = 50
        if task.importance >= 4:
            reasons.append("🐸 Big task - eat the frog")
    else:
        effort_score = 30
        if task.importance >= 4:
            reasons.append("🐘 Major project - break it down")
    
    score += effort_score * 0.15
    
    # === 4. ENERGY ALIGNMENT (10% weight) ===
    energy_score = calculate_energy_alignment(task)
    score += energy_score * 0.10
    
    time_recommendation = get_optimal_time_recommendation(task)
    
    # === 5. CATEGORY WEIGHT (10% weight) ===
    category_multiplier = CATEGORY_WEIGHTS.get(task.category, 1.0)
    category_score = category_multiplier * 50  # Normalize to 0-100
    score += category_score * 0.10
    
    if category_multiplier >= 1.5:
        reasons.append(f"💎 High-impact category ({task.category})")
    
    # === 6. TASK AGING (5% weight) - Don't forget old tasks ===
    age_score = calculate_task_age_penalty(task)
    score += age_score * 0.05
    
    if age_score > 20:
        reasons.append("⏰ Task aging - don't forget!")
    
    # === 7. KEYWORD ANALYSIS (5% weight) ===
    keyword_boost, keyword_reasons = analyze_keywords(task.text)
    score += keyword_boost
    reasons.extend(keyword_reasons)
    
    # === PRIORITY LEVEL MULTIPLIER ===
    priority_multipliers = {
        'urgent': 1.3,
        'high': 1.15,
        'medium': 1.0,
        'low': 0.85
    }
    score *= priority_multipliers.get(task.priority, 1.0)
    
    # === DIMINISHING RETURNS FOR VERY HIGH SCORES ===
    # Prevent one factor from dominating
    if score > 100:
        score = 100 + (score - 100) * 0.3
    
    # Cap at 120 for extreme cases
    score = min(score, 120)
    
    return round(score, 2), reasons, time_recommendation


def calculate_urgency_score(task):
    """Calculate urgency based on due date"""
    if not task.due_date:
        return 20  # Low urgency if no deadline
    
    try:
        due = datetime.fromisoformat(task.due_date.replace('Z', '+00:00'))
        now = datetime.now()
        days_until = (due - now).days
        hours_until = (due - now).total_seconds() / 3600
        
        if days_until < 0:
            # Overdue - exponential urgency
            days_overdue = abs(days_until)
            return min(100 + days_overdue * 5, 150)  # Can go above 100!
        
        elif hours_until <= 4:
            return 100  # Due in hours
        
        elif days_until == 0:
            return 95  # Due today
        
        elif days_until == 1:
            return 85  # Due tomorrow
        
        elif days_until <= 3:
            return 70  # Due this week
        
        elif days_until <= 7:
            return 50
        
        elif days_until <= 14:
            return 35
        
        elif days_until <= 30:
            return 25
        
        else:
            return 15
    
    except:
        return 20


def calculate_energy_alignment(task):
    """
    Match task to optimal time based on circadian rhythm research
    Based on Daniel Pink's "When" - peak, trough, recovery
    """
    current_hour = datetime.now().hour
    estimated_mins = task.estimated_time or 30
    category = task.category
    
    # PEAK HOURS (9-11 AM): Analytical, deep work
    if 9 <= current_hour <= 11:
        if category in ['work', 'learning', 'finance']:
            return 100  # Perfect match
        elif estimated_mins >= 60:
            return 90  # Good for long tasks
        else:
            return 70
    
    # LATE MORNING (11 AM - 1 PM): Still good for focused work
    elif 11 <= current_hour <= 13:
        if category in ['work', 'learning']:
            return 85
        else:
            return 70
    
    # TROUGH (2-4 PM): Low energy - quick tasks only
    elif 14 <= current_hour <= 16:
        if estimated_mins <= 15:
            return 100  # Perfect for quick wins
        elif estimated_mins <= 30:
            return 60
        else:
            return 30  # Avoid long tasks now
    
    # RECOVERY (4-6 PM): Creative, collaborative
    elif 16 <= current_hour <= 18:
        if category in ['personal', 'creative']:
            return 90
        elif estimated_mins <= 60:
            return 75
        else:
            return 50
    
    # EVENING (6-9 PM): Personal tasks, light work
    elif 18 <= current_hour <= 21:
        if category in ['personal', 'health']:
            return 85
        elif estimated_mins <= 30:
            return 70
        else:
            return 40
    
    # LATE NIGHT (9 PM+): Only quick personal tasks
    elif current_hour >= 21 or current_hour <= 6:
        if estimated_mins <= 15 and category == 'personal':
            return 60
        else:
            return 20  # Should rest!
    
    # EARLY MORNING (6-9 AM): Light tasks, exercise
    else:
        if category in ['health', 'personal']:
            return 80
        elif estimated_mins <= 30:
            return 70
        else:
            return 50
    
    return 50  # Default


def get_optimal_time_recommendation(task):
    """Recommend the best time to do this task"""
    estimated_mins = task.estimated_time or 30
    category = task.category
    
    if category in ['work', 'learning', 'finance'] and estimated_mins >= 60:
        return "Best: 9-11 AM (peak focus time)"
    
    elif estimated_mins <= 15:
        return "Best: 2-4 PM (trough - quick wins)"
    
    elif category in ['personal', 'health']:
        return "Best: 6-9 PM (evening personal time)"
    
    elif category == 'creative':
        return "Best: 4-6 PM (recovery - creative work)"
    
    else:
        return "Best: 9 AM - 1 PM (morning energy)"


def calculate_task_age_penalty(task):
    """Penalize old tasks to prevent indefinite postponement"""
    if not task.created_at:
        return 0
    
    try:
        created = datetime.fromisoformat(task.created_at)
        age_days = (datetime.now() - created).days
        
        if age_days >= 60:
            return 50  # Severe penalty
        elif age_days >= 30:
            return 35
        elif age_days >= 14:
            return 20
        elif age_days >= 7:
            return 10
        else:
            return 0
    except:
        return 0


def analyze_keywords(text):
    """Detect priority keywords in task text"""
    text_lower = text.lower()
    boost = 0
    reasons = []
    
    # Urgent keywords (highest weight)
    urgent_keywords = ['urgent', 'asap', 'critical', 'emergency', 'now', 'immediately', 'crisis']
    for keyword in urgent_keywords:
        if keyword in text_lower:
            boost += 25
            reasons.append(f"🚨 Contains '{keyword}'")
            break  # Only count once
    
    # Important keywords
    important_keywords = ['important', 'crucial', 'essential', 'vital', 'key', 'priority', 'must']
    for keyword in important_keywords:
        if keyword in text_lower:
            boost += 15
            reasons.append(f"❗ Contains '{keyword}'")
            break
    
    # Time-sensitive keywords
    time_keywords = ['today', 'tonight', 'deadline', 'meeting', 'call', 'appointment', 'presentation']
    for keyword in time_keywords:
        if keyword in text_lower:
            boost += 10
            break
    
    # Negative keywords (reduce priority)
    negative_keywords = ['maybe', 'someday', 'eventually', 'consider', 'think about']
    for keyword in negative_keywords:
        if keyword in text_lower:
            boost -= 15
            reasons.append(f"💭 Seems optional ('{keyword}')")
            break
    
    return boost, reasons


def create_daily_plan(tasks, max_tasks=5):
    """
    Create optimized daily plan using decision science
    Limits to 3-5 tasks to prevent decision fatigue
    """
    
    # Calculate scores for all tasks
    scored_tasks = []
    for task in tasks:
        score, reasons, time_rec = calculate_master_priority(task)
        scored_tasks.append({
            'task': task,
            'score': score,
            'reasons': reasons,
            'time_recommendation': time_rec
        })
    
    # Sort by score
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    # Apply the 2-Minute Rule (David Allen's GTD)
    two_min_tasks = [st for st in scored_tasks if st['task'].estimated_time <= 2]
    if two_min_tasks:
        for st in two_min_tasks[:2]:  # Do up to 2 immediately
            st['reasons'].insert(0, "⚡ 2-MIN RULE: Do now!")
    
    # Build optimal daily plan
    daily_plan = {
        'morning_focus': [],  # 1 big task (eat the frog)
        'quick_wins': [],     # 2-3 quick tasks (momentum)
        'afternoon': [],      # 1-2 medium tasks
        'total_time': 0
    }
    
    # 1. Identify the "frog" (hardest/most important)
    frogs = [st for st in scored_tasks if st['task'].estimated_time >= 60 and st['score'] >= 70]
    if frogs:
        daily_plan['morning_focus'].append(frogs[0])
        daily_plan['total_time'] += frogs[0]['task'].estimated_time
    
    # 2. Quick wins for momentum (15-30 min)
    quick_wins = [st for st in scored_tasks 
                  if 10 <= st['task'].estimated_time <= 30 
                  and st not in daily_plan['morning_focus']][:3]
    daily_plan['quick_wins'] = quick_wins
    daily_plan['total_time'] += sum(st['task'].estimated_time for st in quick_wins)
    
    # 3. Medium tasks for afternoon
    medium_tasks = [st for st in scored_tasks 
                    if st['task'].estimated_time > 30 
                    and st not in daily_plan['morning_focus']
                    and st not in daily_plan['quick_wins']][:2]
    daily_plan['afternoon'] = medium_tasks
    daily_plan['total_time'] += sum(st['task'].estimated_time for st in medium_tasks)
    
    return daily_plan, scored_tasks[:max_tasks]
