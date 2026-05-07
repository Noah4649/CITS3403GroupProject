from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from app import db
from app.models import User, Workout, Meal, Achievement, Exercise, Feedback, Report
from flask import abort

main = Blueprint('main', __name__)

# ─── HOME ───────────────────────────────────────────────
@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('welcome-page.html')

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

# ─── WORKOUT HISTORY ────────────────────────────────────
@main.route('/history')
@login_required
def history():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(
        Workout.date.desc()
    ).all()

    total_workouts = len(workouts)
    total_calories_burned = sum(w.calories_burned or 0 for w in workouts)
    total_duration = sum(w.duration_mins or 0 for w in workouts)

    return render_template('history.html',
        workouts=workouts,
        total_workouts=total_workouts,
        total_calories_burned=total_calories_burned,
        total_duration=total_duration
    )

# ─── DELETE WORKOUT ─────────────────────────────────────
@main.route('/delete-workout/<int:workout_id>')
@login_required
def delete_workout(workout_id):
    workout = Workout.query.get(workout_id)

    if workout and workout.user_id == current_user.id:
        db.session.delete(workout)
        db.session.commit()
        flash('Workout deleted successfully.')
    else:
        flash('Workout not found or you do not have permission to delete it.')

    return redirect(url_for('main.history'))

# ─── START WORKOUT ──────────────────────────────────────
@main.route('/start-workout', methods=['GET', 'POST'])
@login_required
def start_workout():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        is_public = request.form.get('is_public') in ('1', 'on', 'true', 'True')

        exercise_names = request.form.getlist('exercise_name[]')
        exercise_sets = request.form.getlist('exercise_sets[]')
        exercise_reps = request.form.getlist('exercise_reps[]')
        exercise_weights = request.form.getlist('exercise_weight[]')
        exercise_durations = request.form.getlist('exercise_duration[]')

        if not title:
            flash('Workout title is required.')
            return redirect(url_for('main.start_workout'))

        if not any((name or '').strip() for name in exercise_names):
            flash('Add at least one exercise to start a workout.')
            return redirect(url_for('main.start_workout'))

        def get_form_value(values, index):
            return values[index] if index < len(values) else None

        def to_int(value):
            try:
                return int(value) if value and value.strip() else None
            except ValueError:
                return None

        def to_float(value):
            try:
                return float(value) if value and value.strip() else None
            except ValueError:
                return None

        try:
            new_workout = Workout(
                user_id=current_user.id,
                title=title,
                notes=notes if notes else None,
                is_public=is_public
            )

            db.session.add(new_workout)
            db.session.flush()

            total_duration = 0

            for i, name in enumerate(exercise_names):
                name = (name or '').strip()

                if not name:
                    continue

                sets = to_int(get_form_value(exercise_sets, i))
                reps = to_int(get_form_value(exercise_reps, i))
                weight = to_float(get_form_value(exercise_weights, i))
                duration = to_int(get_form_value(exercise_durations, i))

                if duration:
                    total_duration += duration

                new_exercise = Exercise(
                    workout_id=new_workout.id,
                    name=name,
                    sets=sets,
                    reps=reps,
                    weight_kg=weight,
                    duration_mins=duration
                )

                db.session.add(new_exercise)

            new_workout.duration_mins = total_duration or None

            db.session.commit()

            if is_public:
                flash(f'Workout "{title}" saved and shared publicly.')
            else:
                flash(f'Workout "{title}" saved privately.')

            return redirect(url_for('main.history'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your workout. Please try again.')
            print(f"Error saving workout: {e}")
            return redirect(url_for('main.start_workout'))

    return render_template('start_workout.html')

# ─── FRIENDS FEED ───────────────────────────────────────
@main.route('/friends-feed')
@login_required
def friends_feed():
    public_workouts = Workout.query.filter_by(is_public=True).order_by(Workout.date.desc()).all()
    return render_template(
        'friends_feed.html',
        current_username=current_user.username,
        public_workouts=public_workouts
    )

# ─── PASSWORD RESET ─────────────────────────────────────
@main.route('/password-reset')
def password_reset():
    return render_template('password_reset.html')

# ─── FEEDBACK ───────────────────────────────────────────
@main.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        message = request.form.get('message')
        type_ = request.form.get('type')

        if not message or not type_:
            flash('Please complete all fields.')
            return redirect(url_for('main.feedback'))

        new_feedback = Feedback(
            user_id=current_user.id,
            type=type_,
            message=message
        )

        db.session.add(new_feedback)
        db.session.commit()

        flash('Submission received!')
        return redirect(url_for('main.feedback'))

    submissions = Feedback.query.filter_by(user_id=current_user.id) \
        .order_by(Feedback.created_at.desc()) \
        .all()

    return render_template('feedback.html', submissions=submissions)

# ─── CALORIES ───────────────────────────────────────────
@main.route('/calories')
@login_required
def calories():
    meals = [
        {
            "name": "Greek yoghurt, banana and honey",
            "calories": 420,
            "protein": 28,
            "carbs": 58,
            "fats": 8,
            "water_ml": 0
        },
        {
            "name": "Chicken rice bowl",
            "calories": 720,
            "protein": 45,
            "carbs": 82,
            "fats": 18,
            "water_ml": 500
        },
        {
            "name": "Protein shake",
            "calories": 250,
            "protein": 30,
            "carbs": 18,
            "fats": 5,
            "water_ml": 400
        }
    ]

    total_calories_consumed = 2050
    total_calories_burned = 420
    net_calories = total_calories_consumed - total_calories_burned

    calorie_burn_goal = 600
    burn_progress = min(round((total_calories_burned / calorie_burn_goal) * 100), 100)
    calories_remaining = max(calorie_burn_goal - total_calories_burned, 0)

    return render_template(
        'calories-page.html',
        meals=meals,
        total_calories_consumed=total_calories_consumed,
        total_calories_burned=total_calories_burned,
        net_calories=net_calories,
        calorie_burn_goal=calorie_burn_goal,
        burn_progress=burn_progress,
        calories_remaining=calories_remaining
    )

# ─── LEADERBOARD ────────────────────────────────────────
@main.route('/leaderboard')
@login_required
def leaderboard():
    overall_leaderboard = db.session.query(User).join(Workout).group_by(User.id).order_by(
        db.func.sum(Workout.calories_burned).desc()
    ).limit(10).all()

    bench_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(
        Exercise, Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%bench press%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    squat_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(
        Exercise, Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%squat%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    deadlift_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(
        Exercise, Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%deadlift%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    return render_template('leaderboard-page.html',
        overall_leaderboard=overall_leaderboard,
        bench_leaderboard=bench_leaderboard,
        squat_leaderboard=squat_leaderboard,
        deadlift_leaderboard=deadlift_leaderboard
    )

# ─── WELCOME ────────────────────────────────────────────
@main.route('/welcome')
def welcome():
    return render_template('welcome-page.html')

# ─── SETTINGS ───────────────────────────────────────────
@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# ─── ADMIN ──────────────────────────────────────────────
@main.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)

    users = User.query.order_by(User.created_at.desc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).all()
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()

    return render_template('admin.html',
        users=users,
        reports=reports,
        feedbacks=feedbacks
    )