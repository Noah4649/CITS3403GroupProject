from app import db
from flask_login import UserMixin
from datetime import datetime

# ─── USER ───────────────────────────────────────────────
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), default='default.png')
    bio = db.Column(db.String(300))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    goal = db.Column(db.String(200))  # e.g. "Lose 5kg"
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    workouts = db.relationship('Workout', backref='user', lazy=True)
    meals = db.relationship('Meal', backref='user', lazy=True)
    achievements = db.relationship('Achievement', backref='user', lazy=True)

# ─── FRIENDSHIPS ────────────────────────────────────────
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/accepted/blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── WORKOUTS ───────────────────────────────────────────
class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_mins = db.Column(db.Integer)
    calories_burned = db.Column(db.Float)
    notes = db.Column(db.String(500))
    is_public = db.Column(db.Boolean, default=False)

    exercises = db.relationship('Exercise', backref='workout', lazy=True)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    duration_mins = db.Column(db.Integer)

# ─── NUTRITION ──────────────────────────────────────────
class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fats = db.Column(db.Float)
    water_ml = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ─── GOALS ──────────────────────────────────────────────
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50))   # e.g. 'weight', 'calories', 'workouts'
    target = db.Column(db.Float)
    current = db.Column(db.Float, default=0)
    deadline = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)

# ─── ACHIEVEMENTS & BADGES ──────────────────────────────
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    badge_icon = db.Column(db.String(100))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── CHALLENGES ─────────────────────────────────────────
class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class ChallengeParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, default=0)

# ─── REPORTS (Admin) ────────────────────────────────────
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(500))
    status = db.Column(db.String(20), default='open')  # open/resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)