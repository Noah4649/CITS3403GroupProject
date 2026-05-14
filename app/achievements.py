from datetime import datetime

from app import db
from app.models import Achievement, Workout

# ─── Achievement Helpers ─────────────────────────────────
# These functions check whether a user has met achievement conditions.
# If an achievement has been earned and does not already exist for that user,
# it is added to the current database session and saved when db.session.commit()
# is called in the route.

def award_achievement(user_id, title, description, badge_icon):
    existing = Achievement.query.filter_by(
        user_id=user_id,
        title=title
    ).first()

    if existing:
        return None

    achievement = Achievement(
        user_id=user_id,
        title=title,
        description=description,
        badge_icon=badge_icon,
        earned_at=datetime.utcnow()
    )

    db.session.add(achievement)
    return achievement


def check_and_award_achievements(user_id):
    newly_awarded = []

    workouts = Workout.query.filter_by(user_id=user_id).all()
    workout_count = len(workouts)
    total_calories_burned = sum(w.calories_burned or 0 for w in workouts)

    if workout_count >= 1:
        achievement = award_achievement(
            user_id,
            "First Workout",
            "Completed your first workout.",
            "🏋️"
        )
        if achievement:
            newly_awarded.append(achievement)
    
    if any(w.is_public for w in workouts):
        achievement = award_achievement(
            user_id,
            "Shared the Grind",
            "Made a workout public.",
            "📣"
        )
        if achievement:
            newly_awarded.append(achievement)

    if any((w.calories_burned or 0) >= 500 for w in workouts):
        achievement = award_achievement(
            user_id,
            "Calorie Crusher",
            "Burned over 500 kcal in a single session.",
            "⚡"
        )
        if achievement:
            newly_awarded.append(achievement)

    if workout_count >= 5:
        achievement = award_achievement(
            user_id,
            "Getting Consistent",
            "Logged 5 workouts.",
            "🔥"
        )
        if achievement:
            newly_awarded.append(achievement)

    if workout_count >= 30:
        achievement = award_achievement(
            user_id,
            "Consistency King",
            "Logged 30 workouts.",
            "👑"
        )
        if achievement:
            newly_awarded.append(achievement)
    
    if workout_count >= 100:
        achievement = award_achievement(
            user_id,
            "Century Club",
            "Logged 100 workouts.",
            "💯"
        )
        if achievement:
            newly_awarded.append(achievement)

    if total_calories_burned >= 5000:
        achievement = award_achievement(
            user_id,
            "Burn Machine",
            "Burned 5,000 total calories.",
            "🔥"
        )
        if achievement:
            newly_awarded.append(achievement)
    
    if total_calories_burned >= 10000:
        achievement = award_achievement(
            user_id,
            "Inferno Engine",
            "Burned 10,000 total calories.",
            "🔥"
        )
        if achievement:
            newly_awarded.append(achievement)

    if total_calories_burned >= 25000:
        achievement = award_achievement(
            user_id,
            "Metabolic Machine",
            "Burned 25,000 total calories.",
            "🚀"
        )
        if achievement:
            newly_awarded.append(achievement)

    return newly_awarded