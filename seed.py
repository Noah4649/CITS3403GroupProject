from app import create_app, db
from app.models import User, Workout, Exercise, Meal, Achievement, Friendship, Challenge, ChallengeParticipant, Goal, Feedback, Comment, FeedPost, FeedPostComment
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

app = create_app()

def seed():
    with app.app_context():

        # ─── CLEAR EXISTING DATA ────────────────────────────────
        print("Clearing existing data...")
        ChallengeParticipant.query.delete()
        Challenge.query.delete()
        Feedback.query.delete()
        Achievement.query.delete()
        Goal.query.delete()
        FeedPostComment.query.delete()
        FeedPost.query.delete()
        Comment.query.delete()
        Exercise.query.delete()
        Workout.query.delete()
        Meal.query.delete()
        Friendship.query.delete()
        User.query.delete()
        db.session.commit()

        # ─── USERS ──────────────────────────────────────────────
        print("Seeding users...")
        users = [
            User(
                username="admin",
                email="admin@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="FitTrack administrator.",
                weight=80.0,
                height=180.0,
                goal="Maintain fitness",
                is_admin=True
            ),
            User(
                username="alex_lifts",
                email="alex@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Powerlifter chasing a 200kg deadlift.",
                weight=92.0,
                height=183.0,
                goal="Deadlift 200kg"
            ),
            User(
                username="sarah_runs",
                email="sarah@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Marathon runner and yoga enthusiast.",
                weight=62.0,
                height=168.0,
                goal="Run a sub-4hr marathon"
            ),
            User(
                username="mike_gains",
                email="mike@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Bodybuilder in off-season bulk.",
                weight=105.0,
                height=178.0,
                goal="Gain 5kg of muscle"
            ),
            User(
                username="emma_fit",
                email="emma@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="CrossFit athlete and personal trainer.",
                weight=68.0,
                height=172.0,
                goal="Compete in CrossFit regionals"
            ),
            User(
                username="james_shred",
                email="james@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Cutting for summer. Down 8kg so far.",
                weight=84.0,
                height=179.0,
                goal="Reach 10% body fat"
            ),
            User(
                username="priya_yoga",
                email="priya@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Yoga instructor and casual weightlifter.",
                weight=58.0,
                height=163.0,
                goal="Improve flexibility and core strength"
            ),
            User(
                username="tom_cyclist",
                email="tom@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Road cyclist training for a century ride.",
                weight=74.0,
                height=176.0,
                goal="Complete a 160km ride"
            ),
            User(
                username="lisa_strong",
                email="lisa@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Olympic weightlifter. Snatch PR: 75kg.",
                weight=69.0,
                height=165.0,
                goal="Snatch 80kg"
            ),
            User(
                username="dan_newbie",
                email="dan@fittrack.com",
                password_hash=generate_password_hash("pass1"),
                bio="Just getting started. Here to learn.",
                weight=95.0,
                height=181.0,
                goal="Lose 10kg and build a habit"
            ),
        ]

        db.session.add_all(users)
        db.session.commit()
        print(f"  Created {len(users)} users.")

        # ─── FRIENDSHIPS ────────────────────────────────────────
        print("Seeding friendships...")
        friendship_pairs = [
            (users[1], users[2]),
            (users[1], users[3]),
            (users[1], users[4]),
            (users[2], users[4]),
            (users[2], users[6]),
            (users[3], users[5]),
            (users[4], users[7]),
            (users[5], users[8]),
            (users[6], users[9]),
            (users[7], users[8]),
        ]

        for requester, receiver in friendship_pairs:
            db.session.add(Friendship(
                requester_id=requester.id,
                receiver_id=receiver.id,
                status='accepted'
            ))

        db.session.commit()
        print(f"  Created {len(friendship_pairs)} friendships.")

        # ─── WORKOUTS & EXERCISES ───────────────────────────────
        print("Seeding workouts and exercises...")

        workout_templates = [
            {
                "title": "Push Day",
                "duration_mins": 65,
                "calories_burned": 420,
                "exercises": [
                    {"name": "Bench Press", "sets": 4, "reps": 6, "weight_kg": 100.0},
                    {"name": "Overhead Press", "sets": 3, "reps": 8, "weight_kg": 60.0},
                    {"name": "Incline Dumbbell Press", "sets": 3, "reps": 10, "weight_kg": 35.0},
                    {"name": "Tricep Pushdown", "sets": 3, "reps": 12, "weight_kg": 25.0},
                ]
            },
            {
                "title": "Pull Day",
                "duration_mins": 60,
                "calories_burned": 390,
                "exercises": [
                    {"name": "Deadlift", "sets": 4, "reps": 5, "weight_kg": 160.0},
                    {"name": "Barbell Row", "sets": 3, "reps": 8, "weight_kg": 80.0},
                    {"name": "Lat Pulldown", "sets": 3, "reps": 10, "weight_kg": 70.0},
                    {"name": "Bicep Curl", "sets": 3, "reps": 12, "weight_kg": 20.0},
                ]
            },
            {
                "title": "Leg Day",
                "duration_mins": 75,
                "calories_burned": 510,
                "exercises": [
                    {"name": "Squat", "sets": 4, "reps": 6, "weight_kg": 140.0},
                    {"name": "Romanian Deadlift", "sets": 3, "reps": 8, "weight_kg": 100.0},
                    {"name": "Leg Press", "sets": 3, "reps": 12, "weight_kg": 200.0},
                    {"name": "Calf Raise", "sets": 4, "reps": 15, "weight_kg": 60.0},
                ]
            },
            {
                "title": "Morning Run",
                "duration_mins": 45,
                "calories_burned": 380,
                "exercises": [
                    {"name": "Running", "sets": None, "reps": None, "weight_kg": None, "duration_mins": 45},
                ]
            },
            {
                "title": "Full Body",
                "duration_mins": 55,
                "calories_burned": 450,
                "exercises": [
                    {"name": "Bench Press", "sets": 3, "reps": 8, "weight_kg": 80.0},
                    {"name": "Squat", "sets": 3, "reps": 8, "weight_kg": 100.0},
                    {"name": "Deadlift", "sets": 3, "reps": 6, "weight_kg": 120.0},
                    {"name": "Pull Up", "sets": 3, "reps": 10, "weight_kg": None},
                ]
            },
        ]

        for user in users[1:]:
            for i, template in enumerate(workout_templates):
                days_ago = random.randint(0, 30)
                workout = Workout(
                    user_id=user.id,
                    title=template["title"],
                    duration_mins=template["duration_mins"],
                    calories_burned=template["calories_burned"] + random.randint(-30, 30),
                    date=datetime.utcnow() - timedelta(days=days_ago),
                    is_public=random.choice([True, False]),
                    notes=f"{template['title']} session." if i % 2 == 0 else None
                )
                db.session.add(workout)
                db.session.flush()

                for ex in template["exercises"]:
                    db.session.add(Exercise(
                        workout_id=workout.id,
                        name=ex["name"],
                        sets=ex.get("sets"),
                        reps=ex.get("reps"),
                        weight_kg=ex.get("weight_kg"),
                        duration_mins=ex.get("duration_mins")
                    ))

        db.session.commit()
        print(f"  Created workouts and exercises for {len(users) - 1} users.")

        # ─── MEALS ──────────────────────────────────────────────
        print("Seeding meals...")

        meal_templates = [
            {"name": "Oats with banana", "calories": 380, "protein": 12, "carbs": 65, "fats": 7, "water_ml": 300},
            {"name": "Chicken rice bowl", "calories": 620, "protein": 48, "carbs": 72, "fats": 12, "water_ml": 500},
            {"name": "Protein shake", "calories": 220, "protein": 30, "carbs": 14, "fats": 4, "water_ml": 400},
            {"name": "Greek yoghurt and berries", "calories": 180, "protein": 15, "carbs": 22, "fats": 3, "water_ml": 0},
            {"name": "Salmon and vegetables", "calories": 520, "protein": 42, "carbs": 30, "fats": 22, "water_ml": 400},
            {"name": "Egg white omelette", "calories": 210, "protein": 28, "carbs": 6, "fats": 8, "water_ml": 0},
            {"name": "Tuna pasta", "calories": 580, "protein": 40, "carbs": 68, "fats": 10, "water_ml": 500},
            {"name": "Beef stir fry", "calories": 650, "protein": 45, "carbs": 55, "fats": 18, "water_ml": 300},
        ]

        for user in users[1:]:
            for i in range(7):
                daily_meals = random.sample(meal_templates, 3)
                for meal in daily_meals:
                    db.session.add(Meal(
                        user_id=user.id,
                        name=meal["name"],
                        calories=meal["calories"],
                        protein=meal["protein"],
                        carbs=meal["carbs"],
                        fats=meal["fats"],
                        water_ml=meal["water_ml"],
                        date=datetime.utcnow() - timedelta(days=i)
                    ))

        db.session.commit()
        print(f"  Created meals for {len(users) - 1} users.")

        # ─── GOALS ──────────────────────────────────────────────
        print("Seeding goals...")

        for user in users[1:]:
            db.session.add(Goal(
                user_id=user.id,
                type='calories',
                target=600,
                current=random.randint(200, 600),
                deadline=datetime.utcnow() + timedelta(days=30),
                completed=False
            ))
            db.session.add(Goal(
                user_id=user.id,
                type='workouts',
                target=20,
                current=random.randint(5, 20),
                deadline=datetime.utcnow() + timedelta(days=60),
                completed=False
            ))

        db.session.commit()
        print(f"  Created goals for {len(users) - 1} users.")
        db.session.commit()
        print(f"  Created achievements for {len(users) - 1} users.")

        # ─── CHALLENGES ─────────────────────────────────────────
        print("Seeding challenges...")

        challenges = [
            Challenge(
                title="30 Day Squat Challenge",
                description="Squat every day for 30 days and track your progress.",
                start_date=datetime.utcnow() - timedelta(days=10),
                end_date=datetime.utcnow() + timedelta(days=20),
                created_by=users[1].id
            ),
            Challenge(
                title="10k Steps Daily",
                description="Hit 10,000 steps every day for two weeks.",
                start_date=datetime.utcnow() - timedelta(days=5),
                end_date=datetime.utcnow() + timedelta(days=9),
                created_by=users[2].id
            ),
            Challenge(
                title="Calorie Burn Blitz",
                description="Burn the most calories in one week.",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=7),
                created_by=users[3].id
            ),
        ]

        db.session.add_all(challenges)
        db.session.flush()

        for challenge in challenges:
            participants = random.sample(users[1:], 5)
            for user in participants:
                db.session.add(ChallengeParticipant(
                    challenge_id=challenge.id,
                    user_id=user.id,
                    score=round(random.uniform(10, 100), 1)
                ))

        db.session.commit()
        print(f"  Created {len(challenges)} challenges with participants.")

        # ─── FEEDBACK ───────────────────────────────────────────
        print("Seeding feedback...")

        feedback_samples = [
            {"type": "feedback", "message": "Love the workout tracking feature, very intuitive!"},
            {"type": "complaint", "message": "The calorie page takes a while to load sometimes."},
            {"type": "feedback", "message": "Would be great to have a dark mode option."},
            {"type": "report", "message": "A user was posting inappropriate content on the feed."},
            {"type": "feedback", "message": "The leaderboard is super motivating, keep it up!"},
        ]

        for i, sample in enumerate(feedback_samples):
            db.session.add(Feedback(
                user_id=users[i + 1].id,
                type=sample["type"],
                message=sample["message"]
            ))

        db.session.commit()
        print(f"  Created {len(feedback_samples)} feedback entries.")

        # ─── DONE ───────────────────────────────────────────────
        print("\nDatabase seeded successfully!")
        print("Test accounts (all passwords: pass1):")
        for user in users:
            print(f"  {user.email} {'(admin)' if user.is_admin else ''}")

if __name__ == '__main__':
    seed()
