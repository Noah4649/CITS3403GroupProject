import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import (
    Achievement,
    Challenge,
    ChallengeParticipant,
    Exercise,
    Feedback,
    Friendship,
    Goal,
    Meal,
    Report,
    User,
    Workout,
)


# FITTRACK-MODEL-TESTS-SETUP: imports and shared setup for model unit tests.
# The app fixture in tests/conftest.py creates a fresh in-memory SQLite database
# for each test and seeds one regular user plus one admin user.


class TestUserModel:
    """Tests for creating users and enforcing user database constraints."""

    # FITTRACK-MODEL-TESTS-USER: tests for the User model

    def test_user_can_be_created_with_hashed_password(self, app):
        """A user should save a password hash, not the plain password text."""
        with app.app_context():
            plain_password = 'securepassword123'
            password_hash = generate_password_hash(plain_password)
            user = User(
                username='modeluser',
                email='modeluser@test.com',
                password_hash=password_hash
            )

            db.session.add(user)
            db.session.commit()

            assert user.password_hash != plain_password
            assert check_password_hash(user.password_hash, plain_password)
            assert user.profile_pic == 'default.png'
            assert user.is_admin is False

    def test_duplicate_user_email_is_rejected(self, app):
        """The database should reject a second user with the same email."""
        with app.app_context():
            duplicate_user = User(
                username='duplicateuser',
                email='test@test.com',
                password_hash=generate_password_hash('password123')
            )

            db.session.add(duplicate_user)
            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()


class TestWorkoutAndExerciseModels:
    """Tests for workout ownership and workout exercise records."""

    # FITTRACK-MODEL-TESTS-WORKOUT: tests for Workout and Exercise models

    def test_workout_belongs_to_user(self, app):
        """A workout should link back to its user and appear in user.workouts."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=regular_user.id,
                title='Model relationship workout',
                duration_mins=30,
                calories_burned=250
            )

            db.session.add(workout)
            db.session.commit()

            assert workout.user == regular_user
            assert workout in regular_user.workouts

    def test_exercise_belongs_to_workout(self, app):
        """An exercise should link back to its workout and appear in workout.exercises."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=regular_user.id,
                title='Workout with exercise'
            )
            exercise = Exercise(
                workout=workout,
                name='Bench Press',
                sets=3,
                reps=10,
                weight_kg=60
            )

            db.session.add_all([workout, exercise])
            db.session.commit()

            assert exercise.workout == workout
            assert exercise in workout.exercises

    def test_deleting_workout_deletes_exercises(self, app):
        """Deleting a workout should also delete its exercises through cascade."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=regular_user.id,
                title='Workout to delete'
            )
            exercise = Exercise(
                workout=workout,
                name='Squat',
                sets=4,
                reps=8
            )

            db.session.add_all([workout, exercise])
            db.session.commit()
            workout_id = workout.id
            exercise_id = exercise.id

            db.session.delete(workout)
            db.session.commit()

            assert db.session.get(Workout, workout_id) is None
            assert db.session.get(Exercise, exercise_id) is None


class TestNutritionModel:
    """Tests for meal records."""

    # FITTRACK-MODEL-TESTS-NUTRITION: tests for Meal model

    def test_meal_belongs_to_user(self, app):
        """A meal should link back to its user and appear in user.meals."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            meal = Meal(
                user_id=regular_user.id,
                name='Chicken and rice',
                calories=550,
                protein=45,
                carbs=60,
                fats=12
            )

            db.session.add(meal)
            db.session.commit()

            assert meal.user == regular_user
            assert meal in regular_user.meals


class TestGoalModel:
    """Tests for goal records and their defaults."""

    # FITTRACK-MODEL-TESTS-GOAL: tests for Goal model

    def test_goal_default_values_work(self, app):
        """A new goal should default current to 0 and completed to False."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            goal = Goal(
                user_id=regular_user.id,
                type='workouts',
                target=5
            )

            db.session.add(goal)
            db.session.commit()

            assert goal.current == 0
            assert goal.completed is False


class TestSocialModels:
    """Tests for social model records."""

    # FITTRACK-MODEL-TESTS-SOCIAL: tests for Friendship and Achievement models

    def test_friendship_default_status_is_pending(self, app):
        """A new friendship request should start with pending status."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            admin_user = User.query.filter_by(email='admin@test.com').first()
            friendship = Friendship(
                requester_id=regular_user.id,
                receiver_id=admin_user.id
            )

            db.session.add(friendship)
            db.session.commit()

            assert friendship.status == 'pending'
            assert friendship.requester_id == regular_user.id
            assert friendship.receiver_id == admin_user.id

    def test_achievement_belongs_to_user(self, app):
        """An achievement should link back to its user and appear in user.achievements."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            achievement = Achievement(
                user_id=regular_user.id,
                title='First Workout',
                description='Completed the first workout',
                badge_icon='first-workout.png'
            )

            db.session.add(achievement)
            db.session.commit()

            assert achievement.user == regular_user
            assert achievement in regular_user.achievements


class TestAdminModels:
    """Tests for feedback and report records."""

    # FITTRACK-MODEL-TESTS-ADMIN: tests for Feedback and Report models

    def test_feedback_can_be_created(self, app):
        """Feedback should save its type, message, user ID, and creation time."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            feedback = Feedback(
                user_id=regular_user.id,
                type='feedback',
                message='The app is useful.'
            )

            db.session.add(feedback)
            db.session.commit()

            assert feedback.type == 'feedback'
            assert feedback.message == 'The app is useful.'
            assert feedback.user_id == regular_user.id
            assert isinstance(feedback.created_at, datetime)

    def test_report_default_status_is_open(self, app):
        """A new report should start with open status."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            admin_user = User.query.filter_by(email='admin@test.com').first()
            report = Report(
                reporter_id=regular_user.id,
                reported_user_id=admin_user.id,
                reason='Testing report creation'
            )

            db.session.add(report)
            db.session.commit()

            assert report.status == 'open'
            assert report.reporter_id == regular_user.id
            assert report.reported_user_id == admin_user.id


class TestChallengeModels:
    """Tests for challenge records."""

    # FITTRACK-MODEL-TESTS-CHALLENGE: tests for Challenge and ChallengeParticipant models

    def test_challenge_participant_default_score_is_zero(self, app):
        """A user added to a challenge should start with a score of zero."""
        with app.app_context():
            regular_user = User.query.filter_by(email='test@test.com').first()
            start_date = datetime.now()
            challenge = Challenge(
                title='Weekly Steps',
                description='Walk as much as possible this week',
                start_date=start_date,
                end_date=start_date + timedelta(days=7),
                created_by=regular_user.id
            )
            db.session.add(challenge)
            db.session.flush()

            participant = ChallengeParticipant(
                challenge_id=challenge.id,
                user_id=regular_user.id
            )

            db.session.add(participant)
            db.session.commit()

            assert participant.score == 0
            assert participant.challenge_id == challenge.id
            assert participant.user_id == regular_user.id
