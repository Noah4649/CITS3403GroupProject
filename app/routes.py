from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import date, timedelta
import hashlib
import hmac
from app import db, mail
from app.models import User, Workout, Meal, Achievement, Exercise, Feedback, Goal, Report
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
            flash('Invalid email or password.', 'danger')
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
    total_workouts = len(workouts)
    total_calories_burned = sum(w.calories_burned or 0 for w in workouts)
    total_duration = sum(w.duration_mins or 0 for w in workouts)
    
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
    """
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
    """
    Handles workout creation and persistence to database.
    """
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        is_public = request.form.get('is_public') == '1'

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

        try:
            new_workout = Workout(
                user_id=current_user.id,
                title=title,
                notes=notes if notes else None,
                is_public=is_public,
            )
            db.session.add(new_workout)
            db.session.flush()

            for i, name in enumerate(exercise_names):
                if not (name or '').strip():
                    continue

                sets = int(exercise_sets[i]) if exercise_sets[i] and exercise_sets[i].strip() else None
                reps = int(exercise_reps[i]) if exercise_reps[i] and exercise_reps[i].strip() else None
                weight = float(exercise_weights[i]) if exercise_weights[i] and exercise_weights[i].strip() else None
                duration = int(exercise_durations[i]) if exercise_durations[i] and exercise_durations[i].strip() else None

                new_exercise = Exercise(
                    workout_id=new_workout.id,
                    name=name.strip(),
                    sets=sets,
                    reps=reps,
                    weight_kg=weight,
                    duration_mins=duration
                )
                db.session.add(new_exercise)

            db.session.commit()

            return redirect(url_for('main.workout_active', workout_id=new_workout.id))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your workout. Please try again.')
            print(f"Error saving workout: {e}")
            return redirect(url_for('main.start_workout'))

    return render_template('start_workout.html')

# ─── ONGOING WORKOUT ────────────────────────────────────
@main.route('/workout/<int:workout_id>/active')
@login_required
def workout_active(workout_id):
    """
    Renders the live/in-progress workout page.
    """
    workout = Workout.query.get_or_404(workout_id)

    if workout.user_id != current_user.id:
        abort(403)

    return render_template('workout_active.html', workout=workout)

# ─── FINISH WORKOUT ─────────────────────────────────────
@main.route('/workout/<int:workout_id>/finish', methods=['POST'])
@login_required
def workout_finish(workout_id):
    """
    Saves the duration and calories burned when the user ends a session.
    """
    workout = Workout.query.get_or_404(workout_id)

    if workout.user_id != current_user.id:
        abort(403)

    duration_raw = (request.form.get('duration_mins') or '').strip()
    calories_raw = (request.form.get('calories_burned') or '').strip()

    try:
        duration_mins = int(duration_raw) if duration_raw else 0
        calories_burned = float(calories_raw) if calories_raw else 0.0
    except ValueError:
        flash('Duration and calories must be numbers.')
        return redirect(url_for('main.workout_active', workout_id=workout.id))

    if duration_mins < 0 or calories_burned < 0:
        flash('Duration and calories cannot be negative.')
        return redirect(url_for('main.workout_active', workout_id=workout.id))

    workout.duration_mins = duration_mins
    workout.calories_burned = calories_burned
    db.session.commit()

    flash(f'Nice work! "{workout.title}" saved to your history.')
    return redirect(url_for('main.history'))

# ─── FRIENDS FEED ───────────────────────────────────────
@main.route('/friends-feed')
@login_required
def friends_feed():
    return render_template('friends_feed.html')

# ─── PASSWORD RESET ─────────────────────────────────────
def password_reset_fingerprint(user):
    """
    Creates a safe fingerprint of the user's current password hash.

    The token stores this fingerprint, not the actual password hash.
    If the password changes, the fingerprint changes too, which makes old
    password reset links stop working.
    """
    secret_key = current_app.config['SECRET_KEY']
    value = f'{user.password_hash}{secret_key}'.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def generate_password_reset_token(user):
    """
    Creates a signed password reset token for one specific user.

    The token contains the user ID and a fingerprint of the user's current
    password hash. Flask signs the token, so if someone edits it, it becomes
    invalid.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    token_data = {
        'user_id': user.id,
        'password_fingerprint': password_reset_fingerprint(user)
    }

    return serializer.dumps(token_data, salt='password-reset-salt')


def verify_password_reset_token(token, max_age=1800):
    """
    Checks whether a password reset token is valid and not expired.

    max_age=1800 means the reset link expires after 30 minutes.
    Returns the matching User if valid, otherwise returns None.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        token_data = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=max_age
        )
    except (SignatureExpired, BadSignature):
        return None

    user = User.query.get(token_data.get('user_id'))

    if not user:
        return None

    expected_fingerprint = password_reset_fingerprint(user)
    token_fingerprint = token_data.get('password_fingerprint', '')

    if not hmac.compare_digest(token_fingerprint, expected_fingerprint):
        return None

    return user


def send_password_reset_email(user, reset_url):
    """
    Sends the password reset link to the user's registered email address.
    """
    msg = Message(
        subject='Reset your FitTrack password',
        recipients=[user.email]
    )

    msg.body = f"""
Hi {user.username},

You requested to reset your FitTrack password.

Click the link below to reset your password:

{reset_url}

This link will expire in 30 minutes.

If you did not request this password reset, you can ignore this email.

Thanks,
FitTrack
"""

    mail.send(msg)


@main.route('/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'danger')
            return redirect(url_for('main.password_reset'))

        user = User.query.filter_by(email=email).first()

        # SECURITY NOTE:
        # Use the same message whether the email exists or not.
        # This prevents people from testing random emails to discover accounts.
        if user:
            token = generate_password_reset_token(user)
            reset_url = url_for('main.password_reset_new', token=token, _external=True)

            try:
                send_password_reset_email(user, reset_url)
            except Exception as e:
                print(f'Password reset email failed for {user.email}: {e}')
                flash('There was a problem sending the reset email. Please try again later.', 'danger')
                return redirect(url_for('main.password_reset'))

        flash('If that email is registered, a password reset link has been sent.', 'info')
        return redirect(url_for('main.password_reset'))

    return render_template('password_reset.html')


@main.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset_new(token):
    user = verify_password_reset_token(token)

    if not user:
        flash('This password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('main.password_reset'))

    if request.method == 'POST':
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not password or not confirm_password:
            flash('Please fill in both password fields.', 'danger')
            return redirect(url_for('main.password_reset_new', token=token))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('main.password_reset_new', token=token))

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        flash('Password reset successful. Please log in with your new password.', 'success')
        return redirect(url_for('main.login'))

    return render_template('password_reset_new.html', token=token)

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
    today = date.today()

    meals = Meal.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Meal.date) == today
    ).all()

    workouts = Workout.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Workout.date) == today
    ).all()

    total_calories_consumed = sum(meal.calories or 0 for meal in meals)
    total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
    net_calories = total_calories_consumed - total_calories_burned

    active_calorie_goal = Goal.query.filter_by(
        user_id=current_user.id,
        type='calories',
        completed=False
    ).first()

    calorie_burn_goal = active_calorie_goal.target if active_calorie_goal else 600

    burn_progress = min(round((total_calories_burned / calorie_burn_goal) * 100), 100) if calorie_burn_goal else 0
    calories_remaining = max(calorie_burn_goal - total_calories_burned, 0)

    selected_week = request.args.get('week', 'this')

    start_of_this_week = today - timedelta(days=today.weekday())

    if selected_week == 'last':
        week_start = start_of_this_week - timedelta(days=7)
    elif selected_week == 'two_weeks_ago':
        week_start = start_of_this_week - timedelta(days=14)
    else:
        selected_week = 'this'
        week_start = start_of_this_week

    week_end = week_start + timedelta(days=6)

    week_labels = []
    week_burned_data = []

    for i in range(7):
        day = week_start + timedelta(days=i)

        daily_workouts = Workout.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Workout.date) == day
        ).all()

        daily_total_burned = sum(workout.calories_burned or 0 for workout in daily_workouts)

        week_labels.append(day.strftime('%a'))
        week_burned_data.append(daily_total_burned)

    return render_template(
        'calories-page.html',
        meals=meals,
        total_calories_consumed=total_calories_consumed,
        total_calories_burned=total_calories_burned,
        net_calories=net_calories,
        calorie_burn_goal=calorie_burn_goal,
        burn_progress=burn_progress,
        calories_remaining=calories_remaining,
        selected_week=selected_week,
        week_start=week_start,
        week_end=week_end,
        week_labels=week_labels,
        week_burned_data=week_burned_data
    )

# ─── ADD MEAL API ───────────────────────────────────────
@main.route('/api/add-meal', methods=['POST'])
@login_required
def add_meal():
    try:
        data = request.get_json()

        name = (data.get('name') or '').strip()
        calories = float(data.get('calories') or 0)
        protein = float(data.get('protein') or 0)
        carbs = float(data.get('carbs') or 0)
        fats = float(data.get('fats') or 0)
        water_ml = float(data.get('water_ml') or 0)

        if not name:
            return jsonify({
                'success': False,
                'message': 'Meal name is required.'
            }), 400

        if calories <= 0:
            return jsonify({
                'success': False,
                'message': 'Calories must be greater than 0.'
            }), 400

        meal = Meal(
            user_id=current_user.id,
            name=name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats,
            water_ml=water_ml,
            date=datetime.now()
        )

        db.session.add(meal)
        db.session.commit()

        # Recalculate today's totals after adding the meal
        today = date.today()

        meals = Meal.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Meal.date) == today
        ).all()

        workouts = Workout.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Workout.date) == today
        ).all()

        total_calories_consumed = sum(meal.calories or 0 for meal in meals)
        total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
        net_calories = total_calories_consumed - total_calories_burned
        total_protein = sum(meal.protein or 0 for meal in meals)
        total_carbs = sum(meal.carbs or 0 for meal in meals)
        total_fats = sum(meal.fats or 0 for meal in meals)
        total_water_ml = sum(meal.water_ml or 0 for meal in meals)

        return jsonify({
            'success': True,
            'message': 'Meal added successfully.',
            'meal': {
                'id': meal.id,
                'name': meal.name,
                'calories': meal.calories,
                'protein': meal.protein or 0,
                'carbs': meal.carbs or 0,
                'fats': meal.fats or 0,
                'water_ml': meal.water_ml or 0
            },
            'totals': {
                'total_calories_consumed': total_calories_consumed,
                'total_calories_burned': total_calories_burned,
                'net_calories': net_calories,
                'total_protein': total_protein,
                'total_carbs': total_carbs,
                'total_fats': total_fats,
                'total_water_ml': total_water_ml
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error adding meal: {e}")

        return jsonify({
            'success': False,
            'message': 'An error occurred while adding the meal.'
        }), 500

# ─── DELETE MEAL API ────────────────────────────────────
@main.route('/api/delete-meal/<int:meal_id>', methods=['DELETE'])
@login_required
def delete_meal(meal_id):
    meal = Meal.query.get(meal_id)

    if not meal:
        return jsonify({
            'success': False,
            'message': 'Meal not found.'
        }), 404

    if meal.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'You do not have permission to delete this meal.'
        }), 403

    db.session.delete(meal)
    db.session.commit()

    # Recalculate today's totals after deleting the meal
    today = date.today()

    meals = Meal.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Meal.date) == today
    ).all()

    workouts = Workout.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Workout.date) == today
    ).all()

    total_calories_consumed = sum(meal.calories or 0 for meal in meals)
    total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
    net_calories = total_calories_consumed - total_calories_burned

    total_protein = sum(meal.protein or 0 for meal in meals)
    total_carbs = sum(meal.carbs or 0 for meal in meals)
    total_fats = sum(meal.fats or 0 for meal in meals)
    total_water_ml = sum(meal.water_ml or 0 for meal in meals)

    return jsonify({
        'success': True,
        'message': 'Meal deleted successfully.',
        'meal_id': meal_id,
        'totals': {
            'total_calories_consumed': total_calories_consumed,
            'total_calories_burned': total_calories_burned,
            'net_calories': net_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fats': total_fats,
            'total_water_ml': total_water_ml
        }
    }), 200


# ─── Leaderboard ────────────────────────────────────────
@main.route('/leaderboard')
@login_required
def leaderboard():
    overall_leaderboard = db.session.query(User).join(Workout).group_by(User.id).order_by(
        db.func.sum(Workout.calories_burned).desc()
    ).limit(10).all()

    bench_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(Exercise, Exercise.workout_id == Workout.id).filter(
        db.func.lower(Exercise.name).like('%bench press%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    squat_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(Exercise, Exercise.workout_id == Workout.id).filter(
        db.func.lower(Exercise.name).like('%squat%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    deadlift_leaderboard = db.session.query(
        User.username, db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(Workout, Workout.user_id == User.id).join(Exercise, Exercise.workout_id == Workout.id).filter(
        db.func.lower(Exercise.name).like('%deadlift%')
    ).group_by(User.id).order_by(db.text('weight_kg DESC')).limit(10).all()

    return render_template('leaderboard-page.html',
        overall_leaderboard=overall_leaderboard,
        bench_leaderboard=bench_leaderboard,
        squat_leaderboard=squat_leaderboard,
        deadlift_leaderboard=deadlift_leaderboard
    )

# ─── Welcome ────────────────────────────────────────────
@main.route('/welcome')
def welcome():
    return render_template('welcome-page.html')

# ─── SETTINGS ───────────────────────────────────────────
@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Verify current password is correct
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.')
            return redirect(url_for('main.settings'))

        # Verify new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.')
            return redirect(url_for('main.settings'))

        # Verify new password is not the same as current
        if check_password_hash(current_user.password_hash, new_password):
            flash('New password must be different from your current password.')
            return redirect(url_for('main.settings'))

        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password updated successfully.')
        return redirect(url_for('main.settings'))

    return render_template('settings.html')

# ─── TERMS & CONDITIONS ─────────────────────────────────
@main.route('/terms')
def terms():
    return render_template('TermsCond.html')

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

# ─── API: EDIT PROFILE ──────────────────────────────────
@main.route('/api/edit-profile', methods=['POST'])
@login_required
def api_edit_profile():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data received.'}), 400

    # Only update fields that were actually sent and are not empty
    username = (data.get('username') or '').strip()
    bio = (data.get('bio') or '').strip()
    weight = data.get('weight')
    height = data.get('height')
    goal = (data.get('goal') or '').strip()

    # Check username is not already taken by another user
    if username and username != current_user.username:
        existing = User.query.filter_by(username=username).first()
        if existing:
            return jsonify({'success': False, 'error': 'Username already taken.'}), 409

    # Apply updates
    if username:
        current_user.username = username
    if bio:
        current_user.bio = bio
    if weight:
        try:
            current_user.weight = float(weight)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid weight value.'}), 400
    if height:
        try:
            current_user.height = float(height)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid height value.'}), 400
    if goal:
        current_user.goal = goal

    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully.'})