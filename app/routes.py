from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from app import db
from app.models import User, Workout, Exercise, Meal, Achievement

main = Blueprint('main', __name__)

# ─── HOME ───────────────────────────────────────────────
@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

# ─── SIGNUP ─────────────────────────────────────────────
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.')
            return redirect(url_for('main.signup'))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.dashboard'))

    return render_template('signup.html')

# ─── LOGIN ──────────────────────────────────────────────
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.')
            return redirect(url_for('main.login'))

        login_user(user)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')

# ─── LOGOUT ─────────────────────────────────────────────
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# ─── DASHBOARD ──────────────────────────────────────────
@main.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    workouts = Workout.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Workout.date) == today
    ).all()
    meals = Meal.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Meal.date) == today
    ).all()
    total_calories = sum(m.calories for m in meals)

    return render_template('dashboard.html',
        workouts=workouts,
        meals=meals,
        total_calories=total_calories
    )

# ─── PROFILE ────────────────────────────────────────────
@main.route('/profile')
@login_required
def profile():
    workouts = Workout.query.filter_by(user_id=current_user.id).all()
    achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    total_calories_burned = sum(w.calories_burned or 0 for w in workouts)
    return render_template('profile.html',
        workouts=workouts,
        achievements=achievements,
        total_calories_burned=total_calories_burned
    )

# ─── START WORKOUT ──────────────────────────────────────
@main.route('/start-workout', methods=['GET', 'POST'])
@login_required
def start_workout():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        is_public = bool(request.form.get('is_public'))
        names = request.form.getlist('exercise_name[]')
        sets = request.form.getlist('exercise_sets[]')
        reps = request.form.getlist('exercise_reps[]')
        weights = request.form.getlist('exercise_weight[]')
        durations = request.form.getlist('exercise_duration[]')

        if not title:
            flash('Workout title is required.')
            return redirect(url_for('main.start_workout'))

        if not any((n or '').strip() for n in names):
            flash('Add at least one exercise to start a workout.')
            return redirect(url_for('main.start_workout'))

        workout = Workout(
            user_id=current_user.id,
            title=title,
            notes=notes,
            is_public=is_public
        )

        total_duration = 0
        for index, name in enumerate(names):
            name = (name or '').strip()
            if not name:
                continue

            sets_value = request.form.getlist('exercise_sets[]')[index] if index < len(sets) else None
            reps_value = request.form.getlist('exercise_reps[]')[index] if index < len(reps) else None
            weight_value = request.form.getlist('exercise_weight[]')[index] if index < len(weights) else None
            duration_value = request.form.getlist('exercise_duration[]')[index] if index < len(durations) else None

            try:
                sets_value = int(sets_value) if sets_value else None
            except ValueError:
                sets_value = None
            try:
                reps_value = int(reps_value) if reps_value else None
            except ValueError:
                reps_value = None
            try:
                weight_value = float(weight_value) if weight_value else None
            except ValueError:
                weight_value = None
            try:
                duration_value = int(duration_value) if duration_value else None
            except ValueError:
                duration_value = None

            if duration_value:
                total_duration += duration_value

            workout.exercises.append(Exercise(
                name=name,
                sets=sets_value,
                reps=reps_value,
                weight_kg=weight_value,
                duration_mins=duration_value
            ))

        workout.duration_mins = total_duration or None
        db.session.add(workout)
        db.session.commit()

        if is_public:
            flash('Workout completed and shared publicly.')
        else:
            flash('Workout completed privately.')

        return redirect(url_for('main.dashboard'))

    return render_template('start_workout.html')

# ─── FRIENDS FEED ───────────────────────────────────────
@main.route('/friends-feed')
@login_required
def friends_feed():
    public_workouts = Workout.query.filter_by(is_public=True).order_by(Workout.date.desc()).all()
    return render_template('friends_feed.html', current_username=current_user.username, public_workouts=public_workouts)

# ─── PASSWORD RESET ─────────────────────────────────────
@main.route('/password-reset')
def password_reset():
    return render_template('password_reset.html')