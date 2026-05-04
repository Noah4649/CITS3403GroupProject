from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from app import db
from app.models import User, Workout, Meal, Achievement, Exercise, Feedback

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

# ─── WORKOUT HISTORY ────────────────────────────────────
# This route displays the user's complete workout history with statistics
@main.route('/history')
@login_required
def history():
    """
    Renders the workout history page showing all past workouts and statistics.
    
    Features:
    - Displays all workouts for the current logged-in user
    - Sorted by most recent first (descending date order)
    - Calculates three key statistics:
        1. Total number of workouts ever completed
        2. Total calories burned across all workouts
        3. Total time spent exercising (in minutes)
    
    Returns:
        Renders history.html template with workout data and statistics
    """
    # Query all workouts from the database for current user, newest first
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(
        Workout.date.desc()
    ).all()
    
    # Calculate aggregate statistics from all user workouts
    total_workouts = len(workouts)  # Count total number of workouts
    total_calories_burned = sum(w.calories_burned or 0 for w in workouts)  # Sum all calories (handle None values)
    total_duration = sum(w.duration_mins or 0 for w in workouts)  # Sum all duration minutes (handle None values)
    
    # Pass data to template for rendering
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
    """
    Deletes a workout from the database.
    
    Verifies that the workout belongs to the current user before deleting.
    Associated exercises are automatically deleted due to database cascade.
    
    Args:
        workout_id: The ID of the workout to delete
    
    Returns:
        Redirects to the history page after deletion
    """
    workout = Workout.query.get(workout_id)
    
    # Verify the workout exists and belongs to the current user
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
    """
    Handles workout creation and persistence to database.
    
    GET: Displays the start workout form
    POST: Processes form data to create Workout and Exercise records
    
    Form data processed:
    - title: Workout title (required)
    - notes: Optional workout notes
    - is_public: Boolean for public sharing
    - exercise_name[]: Array of exercise names
    - exercise_sets[]: Array of sets per exercise
    - exercise_reps[]: Array of reps per exercise  
    - exercise_weight[]: Array of weights in kg per exercise
    - exercise_duration[]: Array of durations in minutes per exercise
    """
    if request.method == 'POST':
        # Get basic workout information
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        is_public = request.form.get('is_public') == '1'  # Checkbox value

        # Get exercise data arrays
        exercise_names = request.form.getlist('exercise_name[]')
        exercise_sets = request.form.getlist('exercise_sets[]')
        exercise_reps = request.form.getlist('exercise_reps[]')
        exercise_weights = request.form.getlist('exercise_weight[]')
        exercise_durations = request.form.getlist('exercise_duration[]')

        # Validation: Workout title is required
        if not title:
            flash('Workout title is required.')
            return redirect(url_for('main.start_workout'))

        # Validation: At least one exercise with a name is required
        if not any((name or '').strip() for name in exercise_names):
            flash('Add at least one exercise to start a workout.')
            return redirect(url_for('main.start_workout'))

        try:
            # Create new Workout record
            new_workout = Workout(
                user_id=current_user.id,
                title=title,
                notes=notes if notes else None,
                is_public=is_public,
                # duration_mins and calories_burned will be calculated later
                # when the workout is completed
            )
            db.session.add(new_workout)
            db.session.flush()  # Get the workout ID without committing yet

            # Create Exercise records for each exercise in the workout
            for i, name in enumerate(exercise_names):
                # Skip empty exercise names
                if not (name or '').strip():
                    continue

                # Parse numeric values (handle empty strings)
                sets = int(exercise_sets[i]) if exercise_sets[i] and exercise_sets[i].strip() else None
                reps = int(exercise_reps[i]) if exercise_reps[i] and exercise_reps[i].strip() else None
                weight = float(exercise_weights[i]) if exercise_weights[i] and exercise_weights[i].strip() else None
                duration = int(exercise_durations[i]) if exercise_durations[i] and exercise_durations[i].strip() else None

                # Create Exercise record
                new_exercise = Exercise(
                    workout_id=new_workout.id,
                    name=name.strip(),
                    sets=sets,
                    reps=reps,
                    weight_kg=weight,
                    duration_mins=duration
                )
                db.session.add(new_exercise)

            # Commit all changes to database
            db.session.commit()

            # Success message and redirect to history page
            flash(f'Workout "{title}" started successfully! Check your history to see it.')
            return redirect(url_for('main.history'))

        except Exception as e:
            # Rollback on error and show error message
            db.session.rollback()
            flash('An error occurred while saving your workout. Please try again.')
            print(f"Error saving workout: {e}")  # For debugging
            return redirect(url_for('main.start_workout'))

    # GET request: Display the start workout form
    return render_template('start_workout.html')

# ─── FRIENDS FEED ───────────────────────────────────────
@main.route('/friends-feed')
@login_required
def friends_feed():
    return render_template('friends_feed.html')

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

# ─── Calories ───────────────────────────────────────────
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

# ─── Leaderboard ────────────────────────────────────────
@main.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard-page.html')

# ─── Welcome ────────────────────────────────────────────
@main.route('/welcome')
def welcome():
    return render_template('welcome-page.html')

# ─── SETTINGS ───────────────────────────────────────────
@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')