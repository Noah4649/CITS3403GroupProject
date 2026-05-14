from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import date, timedelta, datetime
import hashlib
import hmac

from app import db, mail
from app.models import User, Workout, Meal, Achievement, Exercise, Feedback, Goal, Report, Friendship


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

    total_calories = sum(m.calories or 0 for m in meals)

    return render_template(
        'dashboard.html',
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

    return render_template(
        'profile.html',
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

    return render_template(
        'history.html',
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

            for i, name in enumerate(exercise_names):
                name = (name or '').strip()

                if not name:
                    continue

                sets = to_int(get_form_value(exercise_sets, i))
                reps = to_int(get_form_value(exercise_reps, i))
                weight = to_float(get_form_value(exercise_weights, i))
                duration = to_int(get_form_value(exercise_durations, i))

                new_exercise = Exercise(
                    workout_id=new_workout.id,
                    name=name,
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

# ─── FRIENDS ────────────────────────────────────────────
@main.route('/friends')
@login_required
def friends():
    search_query = (request.args.get('q') or '').strip()
    search_results = []

    if search_query:
        search_results = User.query.filter(
            User.id != current_user.id,
            db.or_(
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).order_by(
            User.username.asc()
        ).limit(10).all()

    incoming_requests = Friendship.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).order_by(
        Friendship.created_at.desc()
    ).all()

    sent_requests = Friendship.query.filter_by(
        requester_id=current_user.id,
        status='pending'
    ).order_by(
        Friendship.created_at.desc()
    ).all()

    accepted_friendships = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            Friendship.requester_id == current_user.id,
            Friendship.receiver_id == current_user.id
        )
    ).all()

    friends = []

    for friendship in accepted_friendships:
        if friendship.requester_id == current_user.id:
            friends.append(friendship.receiver)
        else:
            friends.append(friendship.requester)

    return render_template(
        'friends.html',
        search_query=search_query,
        search_results=search_results,
        incoming_requests=incoming_requests,
        sent_requests=sent_requests,
        friends=friends
    )

def wants_json_response():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

# ─── SEND FRIEND REQUEST ────────────────────────────────
@main.route('/friends/request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    receiver = User.query.get_or_404(user_id)

    if receiver.id == current_user.id:
        message = 'You cannot send a friend request to yourself.'

        if wants_json_response():
            return jsonify({'success': False, 'message': message}), 400

        flash(message, 'danger')
        return redirect(url_for('main.friends'))

    existing_friendship = Friendship.query.filter(
        db.or_(
            db.and_(
                Friendship.requester_id == current_user.id,
                Friendship.receiver_id == receiver.id
            ),
            db.and_(
                Friendship.requester_id == receiver.id,
                Friendship.receiver_id == current_user.id
            )
        )
    ).first()

    if existing_friendship:
        if existing_friendship.status == 'accepted':
            message = f'You are already friends with {receiver.username}.'
        elif existing_friendship.status == 'pending':
            message = 'A friend request is already pending.'
        else:
            message = 'A friendship record already exists with this user.'

        if wants_json_response():
            return jsonify({'success': False, 'message': message}), 409

        flash(message, 'info')
        return redirect(url_for('main.friends', q=receiver.username))

    new_request = Friendship(
        requester_id=current_user.id,
        receiver_id=receiver.id,
        status='pending'
    )

    db.session.add(new_request)
    db.session.commit()

    message = f'Friend request sent to {receiver.username}.'

    if wants_json_response():
        return jsonify({
            'success': True,
            'message': message,
            'request': {
                'id': new_request.id,
                'receiver_id': receiver.id,
                'receiver_username': receiver.username,
                'status': new_request.status
            }
        })

    flash(message, 'success')
    return redirect(url_for('main.friends', q=receiver.username))

# ─── ACCEPT FRIEND REQUEST ──────────────────────────────
@main.route('/friends/accept/<int:friendship_id>', methods=['POST'])
@login_required
def accept_friend_request(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.receiver_id != current_user.id:
        flash('You do not have permission to accept this friend request.', 'danger')
        return redirect(url_for('main.friends'))

    if friendship.status != 'pending':
        flash('This friend request is no longer pending.', 'info')
        return redirect(url_for('main.friends'))

    friendship.status = 'accepted'
    db.session.commit()

    flash(f'You are now friends with {friendship.requester.username}.', 'success')
    return redirect(url_for('main.friends'))

# ─── DECLINE FRIEND REQUEST ─────────────────────────────
@main.route('/friends/decline/<int:friendship_id>', methods=['POST'])
@login_required
def decline_friend_request(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)

    if friendship.receiver_id != current_user.id:
        flash('You do not have permission to decline this friend request.', 'danger')
        return redirect(url_for('main.friends'))

    if friendship.status != 'pending':
        flash('This friend request is no longer pending.', 'info')
        return redirect(url_for('main.friends'))

    requester_username = friendship.requester.username

    db.session.delete(friendship)
    db.session.commit()

    flash(f'Friend request from {requester_username} declined.', 'info')
    return redirect(url_for('main.friends'))

# ─── REMOVE FRIEND ──────────────────────────────────────
@main.route('/friends/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        db.or_(
            db.and_(
                Friendship.requester_id == current_user.id,
                Friendship.receiver_id == user_id
            ),
            db.and_(
                Friendship.requester_id == user_id,
                Friendship.receiver_id == current_user.id
            )
        )
    ).first()

    if not friendship:
        flash('Friendship not found.', 'danger')
        return redirect(url_for('main.friends'))

    if friendship.requester_id == current_user.id:
        friend = friendship.receiver
    else:
        friend = friendship.requester

    friend_username = friend.username

    db.session.delete(friendship)
    db.session.commit()

    flash(f'{friend_username} has been removed from your friends.', 'success')
    return redirect(url_for('main.friends'))

# ─── FRIENDS FEED ───────────────────────────────────────
@main.route('/friends-feed')
@login_required
def friends_feed():
    public_workouts = Workout.query.filter_by(is_public=True).order_by(
        Workout.date.desc()
    ).all()

    return render_template(
        'friends_feed.html',
        current_username=current_user.username,
        public_workouts=public_workouts
    )


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


# ─── CALORIES ───────────────────────────────────────────
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
    
    current_day_index = today.weekday() if selected_week == 'this' else None

    week_end = week_start + timedelta(days=6)

    week_labels = []
    week_burned_data = []
    week_consumed_data = []

    today_index = today.weekday() if selected_week == 'this' else None

    for i in range(7):
        day = week_start + timedelta(days=i)

        week_labels.append(day.strftime('%a'))

        # If viewing this week, do not draw future days
        if selected_week == 'this' and day > today:
            week_burned_data.append(None)
            week_consumed_data.append(None)
            continue

        daily_workouts = Workout.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Workout.date) == day
        ).all()

        daily_meals = Meal.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Meal.date) == day
        ).all()

        daily_total_burned = sum(workout.calories_burned or 0 for workout in daily_workouts)
        daily_total_consumed = sum(meal.calories or 0 for meal in daily_meals)

        week_burned_data.append(daily_total_burned)
        week_consumed_data.append(daily_total_consumed)


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
        week_burned_data=week_burned_data,
        week_consumed_data=week_consumed_data,
        today_index=today_index,
        current_day_index=current_day_index
    )

# ─── CALORIES CHART DATA API ────────────────────────────
@main.route('/api/calories-chart-data')
@login_required
def calories_chart_data():
    today = date.today()

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
    week_consumed_data = []

    today_index = today.weekday() if selected_week == 'this' else None
    current_day_index = today.weekday() if selected_week == 'this' else None

    for i in range(7):
        day = week_start + timedelta(days=i)

        week_labels.append(day.strftime('%a'))

        # If viewing this week, do not draw future days
        if selected_week == 'this' and day > today:
            week_burned_data.append(None)
            week_consumed_data.append(None)
            continue

        daily_workouts = Workout.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Workout.date) == day
        ).all()

        daily_meals = Meal.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Meal.date) == day
        ).all()

        daily_total_burned = sum(workout.calories_burned or 0 for workout in daily_workouts)
        daily_total_consumed = sum(meal.calories or 0 for meal in daily_meals)

        week_burned_data.append(daily_total_burned)
        week_consumed_data.append(daily_total_consumed)

    return jsonify({
        'success': True,
        'selectedWeek': selected_week,
        'weekStart': week_start.strftime('%d %b'),
        'weekEnd': week_end.strftime('%d %b'),
        'labels': week_labels,
        'burnedData': week_burned_data,
        'consumedData': week_consumed_data,
        'todayIndex': today_index,
        'currentDayIndex': current_day_index
    })

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


# ─── LEADERBOARD ────────────────────────────────────────
@main.route('/leaderboard')
@login_required
def leaderboard():

    def add_competition_ranks(entries, value_field):
        ranked_entries = []
        previous_value = None
        current_rank = 0

        for position, entry in enumerate(entries, start=1):
            value = getattr(entry, value_field)

            if value != previous_value:
                current_rank = position

            ranked_entries.append({
                'rank': current_rank,
                'username': entry.username,
                value_field: value
            })

            previous_value = value

        return ranked_entries

    def add_overall_ranks(entries):
        ranked_entries = []
        previous_value = None
        current_rank = 0

        for position, entry in enumerate(entries, start=1):
            value = entry['average_rank']

            if value != previous_value:
                current_rank = position

            entry['rank'] = current_rank
            ranked_entries.append(entry)

            previous_value = value

        return ranked_entries

    # Total calories burned leaderboard
    calories_leaderboard = db.session.query(
        User.username,
        db.func.sum(Workout.calories_burned).label('total_calories')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).group_by(
        User.id
    ).order_by(
        db.func.sum(Workout.calories_burned).desc(),
        User.username.asc()
    ).limit(10).all()

    calories_leaderboard = add_competition_ranks(
        calories_leaderboard,
        'total_calories'
    )

    # Workouts completed leaderboard
    workouts_completed_leaderboard = db.session.query(
        User.username,
        db.func.count(Workout.id).label('workout_count')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).group_by(
        User.id
    ).order_by(
        db.func.count(Workout.id).desc(),
        User.username.asc()
    ).limit(10).all()

    workouts_completed_leaderboard = add_competition_ranks(
        workouts_completed_leaderboard,
        'workout_count'
    )

    # Total training time leaderboard
    training_time_leaderboard = db.session.query(
        User.username,
        db.func.sum(Workout.duration_mins).label('total_duration')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).group_by(
        User.id
    ).order_by(
        db.func.sum(Workout.duration_mins).desc(),
        User.username.asc()
    ).limit(10).all()

    training_time_leaderboard = add_competition_ranks(
        training_time_leaderboard,
        'total_duration'
    )

    # ─── Overall leaderboard based on average rank ───────────
    leaderboard_scores = {}

    # Add calories leaderboard rankings
    for entry in calories_leaderboard:
        leaderboard_scores.setdefault(entry['username'], []).append(entry['rank'])

    # Add workouts completed leaderboard rankings
    for entry in workouts_completed_leaderboard:
        leaderboard_scores.setdefault(entry['username'], []).append(entry['rank'])

    # Add training time leaderboard rankings
    for entry in training_time_leaderboard:
        leaderboard_scores.setdefault(entry['username'], []).append(entry['rank'])

    overall_leaderboard = []

    for username, ranks in leaderboard_scores.items():
        average_rank = sum(ranks) / len(ranks)

        overall_leaderboard.append({
            'username': username,
            'average_rank': average_rank,
            'categories_counted': len(ranks)
        })

    overall_leaderboard = sorted(
        overall_leaderboard,
        key=lambda entry: (
            entry['average_rank'],
            -entry['categories_counted'],
            entry['username']
        )
    )[:10]

    overall_leaderboard = add_overall_ranks(overall_leaderboard)

    # Bench press leaderboard
    bench_leaderboard = db.session.query(
        User.username,
        db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).join(
        Exercise,
        Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%bench press%')
    ).group_by(
        User.id
    ).order_by(
        db.func.max(Exercise.weight_kg).desc(),
        User.username.asc()
    ).limit(10).all()

    bench_leaderboard = add_competition_ranks(
        bench_leaderboard,
        'weight_kg'
    )

    # Squat leaderboard
    squat_leaderboard = db.session.query(
        User.username,
        db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).join(
        Exercise,
        Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%squat%')
    ).group_by(
        User.id
    ).order_by(
        db.func.max(Exercise.weight_kg).desc(),
        User.username.asc()
    ).limit(10).all()

    squat_leaderboard = add_competition_ranks(
        squat_leaderboard,
        'weight_kg'
    )

    # Deadlift leaderboard
    deadlift_leaderboard = db.session.query(
        User.username,
        db.func.max(Exercise.weight_kg).label('weight_kg')
    ).join(
        Workout,
        Workout.user_id == User.id
    ).join(
        Exercise,
        Exercise.workout_id == Workout.id
    ).filter(
        db.func.lower(Exercise.name).like('%deadlift%')
    ).group_by(
        User.id
    ).order_by(
        db.func.max(Exercise.weight_kg).desc(),
        User.username.asc()
    ).limit(10).all()

    deadlift_leaderboard = add_competition_ranks(
        deadlift_leaderboard,
        'weight_kg'
    )

    return render_template(
        'leaderboard-page.html',
        overall_leaderboard = add_overall_ranks(overall_leaderboard),
        calories_leaderboard=calories_leaderboard,
        workouts_completed_leaderboard=workouts_completed_leaderboard,
        training_time_leaderboard=training_time_leaderboard,
        bench_leaderboard=bench_leaderboard,
        squat_leaderboard=squat_leaderboard,
        deadlift_leaderboard=deadlift_leaderboard
    )


# ─── WELCOME ────────────────────────────────────────────
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
    reports = Feedback.query.filter_by(type='report').order_by(Feedback.created_at.desc()).all()
    feedbacks = Feedback.query.filter(Feedback.type != 'report').order_by(Feedback.created_at.desc()).all()

    return render_template(
        'admin.html',
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