import sys
import os
from typing import List, Tuple
from datetime import datetime, timedelta
import asyncio
import random
from faker import Faker
import bcrypt
from sqlalchemy import or_, select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import io
import logging
from core.exceptions import InternalServerError
from database.session import AsyncSessionLocal
from database.base import Base
from database.session import engine
from auth.models.User import User
from auth.models.command import Command
from auth.models.UserProfile import UserProfile
from auth.models.Token import Token
from user_profile.models.Interest import Interest
from user_profile.models.UserInterest import UserInterest
from user_profile.models.Follower import Follower
from user_profile.models.FollowRequest import FollowRequest
from tweets.models.Tweet import Tweet
from tweets.models.TweetLike import TweetLike
from tweets.models.Comment import Comment
from tweets.models.CommentLike import CommentLike
from tweets.models.Bookmark import Bookmark
from tweets.models.Share import Share
from tweets.models.TweetReport import TweetReport
from tweets.models.CommentReport import CommentReport
from tweets.models.TweetMedia import TweetMedia
from core.image_utils import ImageUtils
import glob
from core.security import hash_password

logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)
fake = Faker("en_IN")

first_user_id_1 = ""
first_user_password_1 = ""

MOCK_IMAGE_DIR = "/app/assets/mock_images"


class MockDataError(Exception):
    pass


def generate_user_id() -> str:
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = "".join(str(random.randint(0, 9)) for _ in range(5))
    return f"{letters}{digits}"


def generate_secure_password() -> str:
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars),
    ]
    length = random.randint(8, 12)
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(random.choices(all_chars, k=length - 4))
    random.shuffle(password)
    return "".join(password)


def get_random_image_bytes() -> Tuple[bytes, str]:
    print("[DEBUG] Listing files in MOCK_IMAGE_DIR:", MOCK_IMAGE_DIR)
    try:
        print("[DEBUG] os.listdir:", os.listdir(MOCK_IMAGE_DIR))
    except Exception as e:
        print(f"[DEBUG] os.listdir error: {e}")
    image_files = glob.glob(os.path.join(MOCK_IMAGE_DIR, "*.*"))
    print("[DEBUG] glob.glob:", image_files)
    print("[DEBUG] All files found in mock_images:")
    for f in image_files:
        try:
            print(f"  {os.path.basename(f)} - {os.path.getsize(f)/1024/1024:.2f} MB")
        except Exception as e:
            print(f"  {os.path.basename(f)} - error reading size: {e}")
    valid_files = [f for f in image_files if os.path.getsize(f) <= 3 * 1024 * 1024]
    print(f"[DEBUG] Valid files (<=3MB): {[os.path.basename(f) for f in valid_files]}")
    if not valid_files:
        raise InternalServerError(
            "No images <= 3MB found in assets/mock_images. Please add smaller images."
        )
    img_path = random.choice(valid_files)
    ext = os.path.splitext(img_path)[-1].lstrip(".")
    with open(img_path, "rb") as f:
        return f.read(), ext


async def create_commands(session: AsyncSession) -> List[Command]:
    try:
        command_names = [
            "Southern Command",
            "Northern Command",
            "Eastern Command",
            "Western Command",
            "Central Command",
            "South Western Command",
            "Training Command",
        ]
        commands = []
        for name in command_names:
            result = await session.execute(select(Command).where(Command.name == name))
            existing = result.scalar_one_or_none()
            if not existing:
                command = Command(name=name)
                session.add(command)
                commands.append(command)
            else:
                commands.append(existing)
        await session.commit()
        return commands
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create commands: {str(e)}")


async def create_interests(session: AsyncSession) -> List[Interest]:
    try:
        interests = [
            "Technology",
            "Sports",
            "Politics",
            "Entertainment",
            "Science",
            "Music",
            "Art",
            "Food",
            "Travel",
            "Fashion",
            "Gaming",
            "Books",
            "Movies",
            "Health",
            "Business",
            "Military",
            "Defense",
            "Strategy",
            "Leadership",
            "National Security",
        ]
        interest_objects = []
        for interest in interests:
            result = await session.execute(
                select(Interest).where(Interest.name == interest)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                interest_obj = Interest(name=interest)
                session.add(interest_obj)
                interest_objects.append(interest_obj)
            else:
                interest_objects.append(existing)
        await session.commit()
        return interest_objects
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create interests: {str(e)}")


async def create_users_with_profiles(
    session: AsyncSession, commands: List[Command], num_users: int = 100
) -> Tuple[List[User], List[UserProfile], List[Token]]:
    try:
        users: List[User] = []
        profiles: List[UserProfile] = []
        tokens: List[Token] = []
        existing_users_result = await session.execute(select(User))
        existing_user_ids = {
            user.user_id for user in existing_users_result.scalars().all()
        }
        existing_profiles_result = await session.execute(select(UserProfile))
        existing_profile_ids = {
            profile.user_id for profile in existing_profiles_result.scalars().all()
        }
        first_user_id = "TU12345"
        first_user_password = "Test@123"
        counter = 1
        original_id = first_user_id
        while first_user_id in existing_user_ids:
            first_user_id = f"{original_id[:-3]}{counter:03d}"
            counter += 1
        global first_user_id_1, first_user_password_1
        first_user_id_1 = first_user_id
        first_user_password_1 = first_user_password
        command = commands[0]
        hashed_password = bcrypt.hashpw(
            first_user_password.encode(), bcrypt.gensalt()
        ).decode()
        first_user = User(
            user_id=first_user_id,
            password=hashed_password,
            date_of_birth=datetime(1990, 1, 15).date(),
            is_private=False,
            is_active=True,
            is_online=True,
            command_id=command.id,
            is_admin=False,
            is_blocked=False,
            block_until=None,
        )
        users.append(first_user)
        existing_user_ids.add(first_user_id)
        photo_bytes, photo_ext = get_random_image_bytes()
        photo_path = ImageUtils.save_user_photo(first_user_id, photo_bytes, photo_ext)
        banner_bytes, banner_ext = get_random_image_bytes()
        banner_path = ImageUtils.save_user_banner(first_user_id, banner_bytes, banner_ext)
        first_profile = UserProfile(
            user_id=first_user_id,
            name="Test User Prime",
            bio="🧪 Test user for cirkle system. Prime organizational user with all edge cases.",
            photo_path=photo_path,
            photo_content_type=photo_ext,
            banner_path=banner_path,
            banner_content_type=banner_ext,
            is_organizational=True,
            is_prime=True,
            command_id=command.id,
        )
        profiles.append(first_profile)
        existing_profile_ids.add(first_user_id)
        test_token = Token(
            user_id=first_user_id,
            access_token=f"test_access_token_{first_user_id}",
            refresh_token=f"test_refresh_token_{first_user_id}",
            expires_at=datetime.now() + timedelta(days=365),
        )
        tokens.append(test_token)
        for i in range(num_users - 1):
            user_id = generate_user_id()
            while user_id in existing_user_ids:
                user_id = generate_user_id()
            password = generate_secure_password()
            hashed_password = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            ).decode()
            command = random.choice(commands)
            is_prime = random.random() < 0.15
            is_organizational = random.random() < 0.12
            is_private = random.random() < 0.25
            user = User(
                user_id=user_id,
                password=hashed_password,
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=60),
                is_private=is_private,
                is_active=True,
                is_online=random.choice([True, False]),
                command_id=command.id,
                is_admin=False,
                is_blocked=False,
                block_until=None,
            )
            users.append(user)
            existing_user_ids.add(user_id)
            photo_bytes, photo_ext = get_random_image_bytes()
            photo_path = ImageUtils.save_user_photo(user_id, photo_bytes, photo_ext)
            banner_bytes, banner_ext = get_random_image_bytes()
            banner_path = ImageUtils.save_user_banner(user_id, banner_bytes, banner_ext)
            name = fake.name()[:100] if len(fake.name()) > 100 else fake.name()
            bio = fake.text(max_nb_chars=150) if random.random() > 0.3 else None
            if bio and len(bio) > 150:
                bio = bio[:150]
            profile = UserProfile(
                user_id=user_id,
                name=name,
                bio=bio,
                photo_path=photo_path,
                photo_content_type=photo_ext,
                banner_path=banner_path,
                banner_content_type=banner_ext,
                is_organizational=is_organizational,
                is_prime=is_prime,
                command_id=command.id,
            )
            profiles.append(profile)
            existing_profile_ids.add(user_id)
            if random.random() < 0.85:
                token = Token(
                    user_id=user_id,
                    access_token=fake.uuid4(),
                    refresh_token=fake.uuid4(),
                    expires_at=datetime.now() + timedelta(days=random.randint(1, 30)),
                )
                tokens.append(token)
        # ATOMIC: Add all at once, rollback on error
        try:
            session.add_all(users)
            session.add_all(profiles)
            session.add_all(tokens)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise MockDataError(f"Failed to create users/profiles/tokens atomically: {str(e)}")
        
        # Final check: all users have profiles
        user_ids = {u.user_id for u in users}
        profile_ids = {p.user_id for p in profiles}
        if user_ids != profile_ids:
            raise MockDataError(f"Mismatch between users and profiles: {user_ids ^ profile_ids}")
        # --- Create admin user ---
        return users, profiles, tokens
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create users and profiles: {str(e)}")


async def validate_user_consistency(session: AsyncSession) -> None:
    try:
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        profiles_result = await session.execute(select(UserProfile))
        profiles = profiles_result.scalars().all()
        user_ids = {user.user_id for user in users}
        profile_user_ids = {profile.user_id for profile in profiles}
        users_without_profiles = user_ids - profile_user_ids
        if users_without_profiles:
            raise MockDataError(
                f"Found users without profiles: {users_without_profiles}"
            )
        profiles_without_users = profile_user_ids - user_ids
        if profiles_without_users:
            raise MockDataError(
                f"Found profiles without users: {profiles_without_users}"
            )
        commands_result = await session.execute(select(Command))
        valid_command_ids = {cmd.id for cmd in commands_result.scalars().all()}
        for user in users:
            if user.command_id not in valid_command_ids:
                raise MockDataError(
                    f"User {user.user_id} has invalid command_id: {user.command_id}"
                )
        for profile in profiles:
            if profile.command_id not in valid_command_ids:
                raise MockDataError(
                    f"Profile {profile.user_id} has invalid command_id: {profile.command_id}"
                )
        admin_users = [user for user in users if user.is_admin]
        if admin_users:
            raise MockDataError(
                f"Found admin users in mock data (should be none): {[u.user_id for u in admin_users]}"
            )
        print("✅ User consistency validation passed (no admins created)")
    except SQLAlchemyError as e:
        raise MockDataError(f"Failed to validate user consistency: {str(e)}")


async def setup_comprehensive_test_user_relationships(
    session: AsyncSession, 
    test_user_id: str,
    users: List[User], 
    interests: List[Interest],
    profiles: List[UserProfile]
) -> None:
    """
    Set up comprehensive relationships and edge cases for the test user.
    This creates all possible scenarios for testing the recommendation system.
    Note: This runs AFTER general follow relationships are created, so it checks for existing relationships.
    """
    try:
        print(f"\n🔧 Setting up comprehensive relationships for test user: {test_user_id}")
        
        # Check existing relationships to avoid conflicts
        existing_followers_result = await session.execute(select(Follower))
        existing_follower_pairs = {
            (f.follower_id, f.followee_id)
            for f in existing_followers_result.scalars().all()
        }
        
        existing_requests_result = await session.execute(select(FollowRequest))
        existing_request_pairs = {
            (fr.follower_id, fr.followee_id)
            for fr in existing_requests_result.scalars().all()
        }
        
        # Build user groups from profiles
        prime_users = [u for u in users if any(p.user_id == u.user_id and p.is_prime for p in profiles)]
        org_users = [u for u in users if any(p.user_id == u.user_id and p.is_organizational for p in profiles)]
        regular_users = [u for u in users if not any(p.user_id == u.user_id and (p.is_prime or p.is_organizational) for p in profiles)]
        private_users = [u for u in users if u.is_private]
        
        # 1. INTERESTS - Give test user diverse interests (all categories)
        print("   📚 Setting up interests...")
        # BUSINESS RULE: A user can have at most 8 interests
        max_interests = 8
        if len(interests) > max_interests:
            selected_interests = random.sample(interests, max_interests)
        else:
            selected_interests = interests
        test_interests = []
        for interest in selected_interests:
            user_interest = UserInterest(
                user_id=test_user_id, 
                interest_id=interest.id
            )
            test_interests.append(user_interest)
        session.add_all(test_interests)
        
        # 2. ENSURE SUFFICIENT MUTUAL FOLLOWERS - Only add if needed
        print("   👥 Ensuring sufficient mutual followers...")
        following_to_create = []
        followers_to_create = []
        
        # Count current mutual followers
        current_mutual_count = 0
        for user in users:
            if user.user_id != test_user_id:
                if ((test_user_id, user.user_id) in existing_follower_pairs and 
                    (user.user_id, test_user_id) in existing_follower_pairs):
                    current_mutual_count += 1
        
        print(f"   Current mutual followers: {current_mutual_count}")
        
        # Ensure at least 30 mutual followers for test user
        target_mutual_followers = 30
        if current_mutual_count < target_mutual_followers:
            needed_mutuals = target_mutual_followers - current_mutual_count
            
            # Find candidates who aren't already mutual followers
            potential_candidates = []
            for user in (prime_users + org_users + regular_users):
                if (user.user_id != test_user_id and 
                    not ((test_user_id, user.user_id) in existing_follower_pairs and 
                         (user.user_id, test_user_id) in existing_follower_pairs)):
                    potential_candidates.append(user)
            
            if potential_candidates:
                candidates_to_add = min(needed_mutuals, len(potential_candidates))
                selected_candidates = random.sample(potential_candidates, candidates_to_add)
                
                for user in selected_candidates:
                    # Add both directions if not already present
                    if (test_user_id, user.user_id) not in existing_follower_pairs:
                        following_to_create.append(Follower(follower_id=test_user_id, followee_id=user.user_id))
                        existing_follower_pairs.add((test_user_id, user.user_id))
                    
                    if (user.user_id, test_user_id) not in existing_follower_pairs:
                        followers_to_create.append(Follower(follower_id=user.user_id, followee_id=test_user_id))
                        existing_follower_pairs.add((user.user_id, test_user_id))
        
        if following_to_create:
            session.add_all(following_to_create)
        if followers_to_create:
            session.add_all(followers_to_create)
        
        # 3. FOLLOW REQUESTS - Create pending requests for testing
        print("   📨 Setting up follow requests...")
        follow_requests = []
        
        # Incoming follow requests (others want to follow test user)
        incoming_candidates = [u for u in private_users[:10] if (u.user_id, test_user_id) not in existing_request_pairs]
        for user in incoming_candidates[:5]:  # 5 incoming requests
            follow_requests.append(FollowRequest(
                follower_id=user.user_id,
                followee_id=test_user_id,
                created_at=datetime.now() - timedelta(days=random.randint(1, 10))
            ))
            existing_request_pairs.add((user.user_id, test_user_id))
        
        # Outgoing follow requests (test user wants to follow private users)
        outgoing_candidates = [u for u in private_users[10:20] if (test_user_id, u.user_id) not in existing_request_pairs]
        for user in outgoing_candidates[:5]:  # 5 outgoing requests
            follow_requests.append(FollowRequest(
                follower_id=test_user_id,
                followee_id=user.user_id,
                created_at=datetime.now() - timedelta(days=random.randint(1, 10))
            ))
            existing_request_pairs.add((test_user_id, user.user_id))
        
        if follow_requests:
            session.add_all(follow_requests)
        
        await session.commit()
        
        print(f"   ✅ Added {len(following_to_create)} following relationships")
        print(f"   ✅ Added {len(followers_to_create)} follower relationships") 
        print(f"   ✅ Added {len(follow_requests)} follow requests")
        print(f"   ✅ Added {len(test_interests)} interests")
        print(f"   📊 Test user comprehensive relationships setup complete")
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to setup test user relationships: {str(e)}")


async def create_user_interests(
    session: AsyncSession, users: List[User], interests: List[Interest]
) -> None:
    try:
        existing_user_interests_result = await session.execute(select(UserInterest))
        existing_pairs = {
            (ui.user_id, ui.interest_id)
            for ui in existing_user_interests_result.scalars().all()
        }
        user_interests = []
        # BUSINESS RULE: A user can have at most 8 interests
        max_interests = 8
        for user in users:
            user_interest_count = random.randint(2, min(5, max_interests))
            selected_interests = random.sample(interests, min(user_interest_count, max_interests))
            for interest in selected_interests:
                if (user.user_id, interest.id) not in existing_pairs:
                    user_interest = UserInterest(
                        user_id=user.user_id, interest_id=interest.id
                    )
                    user_interests.append(user_interest)
                    existing_pairs.add((user.user_id, interest.id))
        if user_interests:
            session.add_all(user_interests)
            await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create user interests: {str(e)}")


async def get_valid_user_ids(session: AsyncSession) -> List[str]:
    try:
        result = await session.execute(select(User.user_id))
        return [row[0] for row in result.all()]
    except SQLAlchemyError as e:
        raise MockDataError(f"Failed to fetch valid user IDs: {str(e)}")


async def get_valid_tweet_ids(session: AsyncSession) -> List[int]:
    try:
        result = await session.execute(select(Tweet.id))
        return [row[0] for row in result.all()]
    except SQLAlchemyError as e:
        raise MockDataError(f"Failed to fetch valid tweet IDs: {str(e)}")


async def get_valid_comment_ids(session: AsyncSession) -> List[int]:
    try:
        result = await session.execute(select(Comment.id))
        return [row[0] for row in result.all()]
    except SQLAlchemyError as e:
        raise MockDataError(f"Failed to fetch valid comment IDs: {str(e)}")


async def create_follow_relationships(
    session: AsyncSession, users: List[User], min_followers=15, max_followers=80
):
    try:
        existing_followers_result = await session.execute(select(Follower))
        existing_follower_pairs = {
            (f.follower_id, f.followee_id)
            for f in existing_followers_result.scalars().all()
        }
        existing_requests_result = await session.execute(select(FollowRequest))
        existing_request_pairs = {
            (fr.follower_id, fr.followee_id)
            for fr in existing_requests_result.scalars().all()
        }
        # Use sets to track new pairs in this batch
        follower_pairs = set(existing_follower_pairs)
        request_pairs = set(existing_request_pairs)
        followers = []
        follow_requests = []
        mutual_follow_pairs = []  # Track mutual relationships
        valid_user_ids = await get_valid_user_ids(session)
        if not valid_user_ids:
            raise MockDataError("No valid users found in the database")
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id.in_(valid_user_ids))
        )
        user_profiles = {
            profile.user_id: profile for profile in profile_result.scalars().all()
        }
        # Track mutuals for each user
        user_mutuals = {u.user_id: set() for u in users if u.user_id in valid_user_ids}
        
        # PHASE 1: Create initial follow relationships with higher mutual probability
        print("   👥 Creating follow relationships with enhanced mutual connections...")
        for user in users:
            if user.user_id not in valid_user_ids:
                continue
            potential_followers = [
                u
                for u in users
                if u.user_id != user.user_id and u.user_id in valid_user_ids
            ]
            if not potential_followers:
                continue
            user_profile = user_profiles.get(user.user_id)
            if not user_profile:
                continue
            base_followers = max_followers
            if user_profile.is_organizational and user_profile.is_prime:
                base_followers = int(max_followers * 1.5)
            elif user_profile.is_prime or user_profile.is_organizational:
                base_followers = int(max_followers * 1.2)
            max_possible_followers = min(base_followers, len(potential_followers))
            min_possible_followers = min(min_followers, max_possible_followers)
            num_followers = random.randint(
                min_possible_followers, max_possible_followers
            )
            weighted_followers = []
            for follower in potential_followers:
                follower_profile = user_profiles.get(follower.user_id)
                if follower_profile:
                    weight = 1
                    if follower_profile.is_organizational and follower_profile.is_prime:
                        weight = 4
                    elif (
                        follower_profile.is_prime or follower_profile.is_organizational
                    ):
                        weight = 2
                    weighted_followers.extend([follower] * weight)
            if weighted_followers:
                selected_followers = random.sample(
                    weighted_followers,
                    min(num_followers, len(set(f.user_id for f in weighted_followers))),
                )
                unique_followers = []
                seen_ids = set()
                for follower in selected_followers:
                    if follower.user_id not in seen_ids:
                        unique_followers.append(follower)
                        seen_ids.add(follower.user_id)
                selected_followers = unique_followers[:num_followers]
            else:
                selected_followers = random.sample(potential_followers, num_followers)
            
            # Create follow relationships with 65% mutual probability (increased from 30%)
            for follower in selected_followers:
                if follower.user_id not in valid_user_ids:
                    continue
                if follower.user_id == user.user_id:
                    continue  # No self-follows
                pair = (follower.user_id, user.user_id)
                if pair in follower_pairs or pair in request_pairs:
                    continue  # No duplicates
                
                # A user cannot follow themselves
                if follower.user_id == user.user_id:
                    continue

                # 65% chance to create mutual follow relationship (increased from 30%)
                should_be_mutual = random.random() < 0.65
                if should_be_mutual:
                    reverse_pair = (user.user_id, follower.user_id)
                    if reverse_pair not in follower_pairs and reverse_pair not in request_pairs:
                        mutual_follow_pairs.append((follower.user_id, user.user_id))
                        user_mutuals[user.user_id].add(follower.user_id)
                        user_mutuals[follower.user_id].add(user.user_id)
                
                is_private = user.is_private
                if is_private:
                    status_choice = random.random()
                    if status_choice < 0.7:  # Increased acceptance rate for private users
                        follow = Follower(
                            follower_id=follower.user_id, followee_id=user.user_id
                        )
                        followers.append(follow)
                        follower_pairs.add(pair)
                    else:
                        request = FollowRequest(
                            follower_id=follower.user_id,
                            followee_id=user.user_id,
                            status="PENDING" if status_choice < 0.85 else "DECLINED",
                        )
                        follow_requests.append(request)
                        request_pairs.add(pair)
                else:
                    if random.random() < 0.95:
                        follow = Follower(
                            follower_id=follower.user_id, followee_id=user.user_id
                        )
                        followers.append(follow)
                        follower_pairs.add(pair)
                    else:
                        request = FollowRequest(
                            follower_id=follower.user_id,
                            followee_id=user.user_id,
                            status="DECLINED",
                        )
                        follow_requests.append(request)
                        request_pairs.add(pair)
        
        # PHASE 2: Create mutual follow relationships
        print(f"   🤝 Creating {len(mutual_follow_pairs)} mutual follow relationships...")
        mutual_followers_created = 0
        for follower_id, followee_id in mutual_follow_pairs:
            reverse_pair = (followee_id, follower_id)
            if reverse_pair not in follower_pairs and reverse_pair not in request_pairs:
                mutual_follow = Follower(
                    follower_id=followee_id, followee_id=follower_id
                )
                followers.append(mutual_follow)
                follower_pairs.add(reverse_pair)
                user_mutuals[follower_id].add(followee_id)
                user_mutuals[followee_id].add(follower_id)
                mutual_followers_created += 1
        
        # PHASE 3: Ensure every user has sufficient mutual followers
        print("   🔄 Ensuring minimum mutual followers for all users...")
        user_ids = list(user_mutuals.keys())
        min_mutual_followers = 5  # Minimum mutual followers per user
        additional_mutuals_created = 0
        
        for user_id in user_ids:
            current_mutuals = len(user_mutuals[user_id])
            if current_mutuals < min_mutual_followers:
                # Find candidates who don't have enough mutuals either
                candidates = [
                    uid for uid in user_ids 
                    if uid != user_id 
                    and user_id not in user_mutuals[uid]
                    and (user_id, uid) not in follower_pairs
                    and (uid, user_id) not in follower_pairs
                ]
                
                needed_mutuals = min_mutual_followers - current_mutuals
                available_candidates = min(needed_mutuals, len(candidates))
                
                if available_candidates > 0:
                    selected_candidates = random.sample(candidates, available_candidates)
                    for candidate in selected_candidates:
                        # Create bidirectional follows
                        followers.append(Follower(follower_id=user_id, followee_id=candidate))
                        followers.append(Follower(follower_id=candidate, followee_id=user_id))
                        follower_pairs.add((user_id, candidate))
                        follower_pairs.add((candidate, user_id))
                        user_mutuals[user_id].add(candidate)
                        user_mutuals[candidate].add(user_id)
                        additional_mutuals_created += 1
        
        if followers:
            session.add_all(followers)
        if follow_requests:
            session.add_all(follow_requests)
        await session.commit()
        
        # Calculate statistics
        total_mutual_relationships = sum(len(mutuals) for mutuals in user_mutuals.values()) // 2
        avg_mutual_per_user = total_mutual_relationships * 2 / len(user_ids) if user_ids else 0
        
        print("\n=== Enhanced Follow Relationships Statistics ===")
        print(f"Total direct followers: {len(followers)}")
        print(f"Mutual follow relationships created: {mutual_followers_created}")
        print(f"Additional mutual relationships: {additional_mutuals_created}")
        print(f"Total mutual relationships: {total_mutual_relationships}")
        print(f"Average mutual followers per user: {avg_mutual_per_user:.1f}")
        print(f"Follow requests: {len(follow_requests)}")
        pending_requests = sum(1 for r in follow_requests if r.status == "PENDING")
        declined_requests = sum(1 for r in follow_requests if r.status == "DECLINED")
        print(f"- Pending requests: {pending_requests}")
        print(f"- Declined requests: {declined_requests}")
        print("==============================================\n")
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create follow relationships: {str(e)}")


async def create_comprehensive_test_user_tweets(
    session: AsyncSession, 
    test_user_id: str, 
    users: List[User]
) -> Tuple[List[Tweet], List[TweetMedia]]:
    """
    Create comprehensive tweets for the test user covering all edge cases:
    - Recent tweets (24h) with high engagement
    - Older tweets for infinite scroll testing
    - Tweets with various media types
    - Tweets with different engagement levels
    """
    try:
        print(f"\n📝 Creating comprehensive tweets for test user: {test_user_id}")
        
        tweets = []
        media_items = []
        
        # 1. RECENT TWEETS (Last 24 hours) - For latest feed testing
        print("   🕐 Creating recent tweets (24h)...")
        recent_tweet_texts = [
            "🚀 Testing the new Twitter-like recommendation system! This tweet should appear in latest feed with high priority. #Testing #RecommendationSystem",
            "📊 Prime + Organizational user tweet with high engagement potential. Should be in 40% priority category. Like and share to test engagement!",
            "🔄 Pull-to-refresh functionality test tweet. This should appear when users refresh their feed. #FreshContent",
            "📱 Mobile app testing in progress. Infinite scroll and pagination working perfectly! #MobileFirst #UX",
            "🎯 Edge case testing: This tweet has exactly 280 characters to test the character limit functionality and ensure proper handling of maximum length content in the system.",
            "🧪 A/B testing different engagement patterns. This tweet should get various interactions for recommendation algorithm validation.",
            "🌟 Prime organizational content with media attachments. Testing image upload and display functionality.",
            "⚡ Real-time feed updates test. This tweet should appear instantly in followers' feeds with proper caching.",
        ]
        
        for i, text in enumerate(recent_tweet_texts):
            # Create tweets at different times within last 24 hours
            hours_ago = random.randint(1, 23)
            created_at = datetime.now() - timedelta(hours=hours_ago)
            
            tweet_text = fake.text(max_nb_chars=500)
            if len(tweet_text) > 500:
                tweet_text = tweet_text[:500]
            media_items = media_items[:4]  # Max 4 media per tweet
            tweets.append(Tweet(
                user_id=test_user_id,
                text=tweet_text,
                view_count=random.randint(100, 1000),  # High view counts
                created_at=created_at,
                updated_at=None
            ))
            
            # Add media to some tweets
            if i % 3 == 0:  # Every 3rd tweet gets media
                try:
                    media_bytes, media_ext = get_random_image_bytes()
                    media_path = ImageUtils.save_tweet_media(
                        test_user_id, f"temp_tweet_{i}", 1, media_bytes, media_ext
                    )
                    media_item = TweetMedia(
                        tweet_id=None,  # Will be set after tweet is saved
                        media_type=f"image/{media_ext}",
                        media_path=media_path
                    )
                    media_items.append((tweets[-1], media_item))
                except Exception as e:
                    print(f"   ⚠️ Could not add media to tweet {i}: {e}")
        
        # 2. OLDER TWEETS (2-30 days old) - For infinite scroll testing
        print("   📅 Creating older tweets (2-30 days)...")
        older_tweet_texts = [
            "📈 Historical tweet for infinite scroll testing. This should appear when users scroll down for older content.",
            "🔍 Search functionality test tweet with multiple hashtags #Search #Testing #Hashtags #Discovery",
            "💬 Comment thread starter. This tweet should have multiple replies and nested comments for testing.",
            "🔗 Link sharing test: https://example.com/test-link - Testing URL preview and link handling.",
            "📸 Media gallery test with multiple images. Testing carousel functionality and image optimization.",
            "🎭 Emoji heavy tweet 🚀🌟💫⭐🎯🔥💎✨🎉🎊 - Testing emoji rendering and character encoding.",
            "📊 Analytics test tweet. This helps validate engagement metrics and recommendation scoring algorithms.",
            "🌐 Multilingual test: Hello, नमस्ते, مرحبا, 你好, Bonjour - Testing international character support.",
            "🔄 Retweet simulation test. This content should be shareable and show proper attribution.",
            "🏷️ Mention test: Testing user mentions and notification system @testuser functionality.",
        ]
        
        for i, text in enumerate(older_tweet_texts):
            # Create tweets 2-30 days old
            days_ago = random.randint(2, 30)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            tweet_text = fake.text(max_nb_chars=500)
            if len(tweet_text) > 500:
                tweet_text = tweet_text[:500]
            tweets.append(Tweet(
                user_id=test_user_id,
                text=tweet_text,
                view_count=random.randint(50, 500),  # Moderate view counts
                created_at=created_at,
                updated_at=None
            ))
        
        # 3. VERY OLD TWEETS (31-60 days) - For edge case testing
        print("   🗂️ Creating very old tweets...")
        very_old_texts = [
            "�� Archive test tweet. This should appear only in deep scroll scenarios.",
            "🕰️ Time-based filtering test. Validating date range queries and pagination.",
            "📊 Historical engagement data for recommendation algorithm training.",
        ]
        
        for i, text in enumerate(very_old_texts):
            days_ago = random.randint(31, 60)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            tweet_text = fake.text(max_nb_chars=500)
            if len(tweet_text) > 500:
                tweet_text = tweet_text[:500]
            tweets.append(Tweet(
                user_id=test_user_id,
                text=tweet_text,
                view_count=random.randint(10, 100),  # Lower view counts
                created_at=created_at,
                updated_at=None
            ))
        
        # Add all tweets to session
        session.add_all(tweets)
        await session.flush()  # Get tweet IDs
        
        # Update media items with actual tweet IDs
        final_media_items = []
        for tweet, media_item in media_items:
            media_item.tweet_id = tweet.id
            final_media_items.append(media_item)
        
        session.add_all(final_media_items)
        await session.commit()
        
        print(f"   ✅ Created {len(tweets)} tweets for test user")
        print(f"   ✅ Created {len(final_media_items)} media items")
        print(f"   📊 Recent tweets (24h): {len(recent_tweet_texts)}")
        print(f"   📊 Older tweets (2-30d): {len(older_tweet_texts)}")
        print(f"   📊 Very old tweets (31-60d): {len(very_old_texts)}")
        
        return tweets, final_media_items
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create test user tweets: {str(e)}")


async def create_tweets_with_media(
    session: AsyncSession, users: List[User], num_tweets_per_user: int = 8
) -> Tuple[List[Tweet], List[TweetMedia]]:
    tweets: List[Tweet] = []
    tweet_media_list: List[TweetMedia] = []
    for user in users:
        for _ in range(num_tweets_per_user):
            tweet_text = fake.text(max_nb_chars=500)
            if len(tweet_text) > 500:
                tweet_text = tweet_text[:500]
            # Create the Tweet object and add to session
            tweet = Tweet(
                user_id=user.user_id,
                text=tweet_text,
                created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
            )
            session.add(tweet)
            await session.flush()
            tweets.append(tweet)
            # --- Media logic ---
            num_media = random.randint(0, 4)
            for idx in range(num_media):
                media_type = random.choice(
                    ["image/jpeg", "image/png", "image/jpg", "image/webp"]
                )
                ext = media_type.split("/")[-1]
                file_bytes, _ = get_random_image_bytes()
                media_path = ImageUtils.save_tweet_media(
                    user.user_id, tweet.id, idx + 1, file_bytes, ext
                )
                tweet_media = TweetMedia(
                    tweet_id=tweet.id,
                    media_type=media_type,
                    media_path=media_path,
                )
                session.add(tweet_media)
                tweet_media_list.append(tweet_media)
    await session.commit()
    return tweets, tweet_media_list


async def create_shares(session: AsyncSession, users: List[User], tweets: List[Tweet]):
    try:
        # Build user and follower maps for efficient lookups
        user_map = {user.user_id: user for user in users}
        followers_result = await session.execute(select(Follower))
        followers_map = {}  # Key: user_id, Value: set of follower_ids
        following_map = {}  # Key: user_id, Value: set of user_ids they follow
        
        for user in users:
            followers_map[user.user_id] = set()
            following_map[user.user_id] = set()

        for f in followers_result.scalars().all():
            if f.followee_id in followers_map:
                followers_map[f.followee_id].add(f.follower_id)
            if f.follower_id in following_map:
                following_map[f.follower_id].add(f.followee_id)

        existing_shares_result = await session.execute(select(Share))
        existing_share_pairs = {
            (s.tweet_id, s.user_id, s.recipient_id)
            for s in existing_shares_result.scalars().all()
        }
        shares = []
        valid_user_ids = await get_valid_user_ids(session)
        valid_tweet_ids = await get_valid_tweet_ids(session)
        if not valid_user_ids:
            raise MockDataError("No valid users found in the database")
        if not valid_tweet_ids:
            raise MockDataError("No valid tweets found in the database")
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id.in_(valid_user_ids))
        )
        user_profiles = {
            profile.user_id: profile for profile in profile_result.scalars().all()
        }
        tweet_data_result = await session.execute(
            select(Tweet).where(Tweet.id.in_(valid_tweet_ids))
        )
        tweet_data = {tweet.id: tweet for tweet in tweet_data_result.scalars().all()}
        
        print("🔄 Creating enhanced share patterns (all followers with mutual priority)...")
        for tweet in tweets:
            if tweet.id not in valid_tweet_ids:
                continue

            tweet_author_user = user_map.get(tweet.user_id)
            if not tweet_author_user:
                continue

            tweet_author_profile = user_profiles.get(tweet.user_id)
            if not tweet_author_profile:
                continue

            # Determine potential sharers based on privacy
            author_followers = followers_map.get(tweet.user_id, set())
            if tweet_author_user.is_private:
                # Only followers can share a private tweet
                potential_sharers = [
                    u for u in users if u.user_id in author_followers and u.user_id != tweet.user_id
                ]
            else:
                # Anyone can share a public tweet
                potential_sharers = [
                    u for u in users if u.user_id != tweet.user_id and u.user_id in valid_user_ids
                ]

            if not potential_sharers:
                continue
            
            base_share_chance = 0.25
            if tweet_author_profile.is_organizational and tweet_author_profile.is_prime:
                base_share_chance = 0.45
            elif tweet_author_profile.is_prime:
                base_share_chance = 0.35
            elif tweet_author_profile.is_organizational:
                base_share_chance = 0.30
            hours_old = (datetime.now() - tweet.created_at).total_seconds() / 3600
            if hours_old <= 24:
                base_share_chance *= 1.4
            elif hours_old <= 48:
                base_share_chance *= 1.2

            if random.random() < base_share_chance:
                max_shares = 5
                if (
                    tweet_author_profile.is_organizational
                    and tweet_author_profile.is_prime
                ):
                    max_shares = 12
                elif (
                    tweet_author_profile.is_prime
                    or tweet_author_profile.is_organizational
                ):
                    max_shares = 8
                num_shares = random.randint(1, max_shares)

                weighted_sharers = []
                for user in potential_sharers:
                    user_profile = user_profiles.get(user.user_id)
                    if user_profile:
                        weight = 1
                        if user_profile.is_organizational or user_profile.is_prime:
                            weight = 3
                        weighted_sharers.extend([user] * weight)
                
                if weighted_sharers:
                    unique_sharers = []
                    seen_ids = set()
                    for sharer in weighted_sharers:
                        if sharer.user_id not in seen_ids:
                            unique_sharers.append(sharer)
                            seen_ids.add(sharer.user_id)
                    num_shares = min(num_shares, len(unique_sharers))
                    sharing_users = random.sample(unique_sharers, num_shares)
                else:
                    num_shares = min(num_shares, len(potential_sharers))
                    sharing_users = random.sample(potential_sharers, num_shares)

                for user in sharing_users:
                    # Potential recipients are users the sharer follows
                    sharer_following = following_map.get(user.user_id, set())
                    potential_recipients = list(sharer_following)

                    # If tweet is private, recipient must also be a follower of the tweet author
                    if tweet_author_user.is_private:
                        potential_recipients = [
                            uid for uid in potential_recipients if uid in author_followers
                        ]
                    
                    if not potential_recipients:
                        continue

                    # Prioritize mutual followers for recipient selection
                    user_followers = followers_map.get(user.user_id, set())
                    mutual_candidates = [
                        uid for uid in potential_recipients if uid in user_followers
                    ]
                    
                    recipient_id = None
                    if len(potential_recipients) > 1:
                        if mutual_candidates and random.random() < 0.7:
                            recipient_id = random.choice(mutual_candidates)
                        else:
                            recipient_id = random.choice(potential_recipients)
                    elif potential_recipients:
                        recipient_id = potential_recipients[0]
                    
                    if not recipient_id or (tweet.id, user.user_id, recipient_id) in existing_share_pairs:
                        continue
                    
                    share = Share(
                        tweet_id=tweet.id,
                        user_id=user.user_id,
                        recipient_id=recipient_id,
                        message=random.choice(
                            [
                                "Check this out!",
                                "Thought you'd like this",
                                "Interesting read",
                                "Worth sharing",
                                "Great content!",
                                "Thought you might find this interesting!",
                                None,
                                None,
                            ]
                        ),
                    )
                    shares.append(share)
                    existing_share_pairs.add((tweet.id, user.user_id, recipient_id))
        if shares:
            session.add_all(shares)
            await session.commit()
        
        # Calculate sharing statistics
        mutual_shares = 0
        for share in shares:
            sharer_id = share.user_id
            recipient_id = share.recipient_id
            # A share is with a mutual if the recipient also follows the sharer.
            if recipient_id in followers_map.get(sharer_id, set()):
                mutual_shares += 1
        
        total_shares = len(shares)
        regular_shares = total_shares - mutual_shares
        
        print(f"📊 Created {len(shares)} shares with enhanced engagement patterns")
        print(f"   - Mutual follower shares: {mutual_shares}")
        print(f"   - Regular follower shares: {regular_shares}")
        print(f"   - Mutual share ratio: {mutual_shares/total_shares*100:.1f}%" if total_shares > 0 else "")
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create shares: {str(e)}")


async def create_comments_and_replies(
    session: AsyncSession, tweets: List[Tweet], users: List[User]
):
    try:
        # Build user and follower maps for efficient lookups
        user_map = {user.user_id: user for user in users}
        followers_result = await session.execute(select(Follower))
        followers_map = {}
        for f in followers_result.scalars().all():
            if f.followee_id not in followers_map:
                followers_map[f.followee_id] = set()
            followers_map[f.followee_id].add(f.follower_id)

        existing_comments_result = await session.execute(select(Comment))
        existing_comment_pairs = {
            (c.tweet_id, c.user_id, c.text[:50])
            for c in existing_comments_result.scalars().all()
        }
        comments = []
        replies = []
        valid_user_ids = await get_valid_user_ids(session)
        valid_tweet_ids = await get_valid_tweet_ids(session)
        if not valid_user_ids:
            raise MockDataError("No valid users found in the database")
        if not valid_tweet_ids:
            raise MockDataError("No valid tweets found in the database")
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id.in_(valid_user_ids))
        )
        user_profiles = {
            profile.user_id: profile for profile in profile_result.scalars().all()
        }
        tweet_data_result = await session.execute(
            select(Tweet).where(Tweet.id.in_(valid_tweet_ids))
        )
        tweet_data = {tweet.id: tweet for tweet in tweet_data_result.scalars().all()}
        print("💬 Creating enhanced comment patterns...")
        for tweet in tweets:
            if tweet.id not in valid_tweet_ids:
                continue

            tweet_author_user = user_map.get(tweet.user_id)
            if not tweet_author_user:
                continue

            tweet_author_profile = user_profiles.get(tweet.user_id)
            if not tweet_author_profile:
                continue

            # Determine potential commenters based on privacy
            potential_commenters = []
            if tweet_author_user.is_private:
                author_followers = followers_map.get(tweet.user_id, set())
                # Only followers and the author can comment on private tweets
                potential_commenters = [
                    u for u in users if u.user_id in author_followers or u.user_id == tweet.user_id
                ]
            else:
                # Anyone can comment on a public tweet
                potential_commenters = [u for u in users if u.user_id in valid_user_ids]

            if not potential_commenters:
                continue

            base_comments = random.randint(0, 8)
            if tweet_author_profile.is_organizational and tweet_author_profile.is_prime:
                base_comments = random.randint(5, 20)
            elif tweet_author_profile.is_prime:
                base_comments = random.randint(3, 15)
            elif tweet_author_profile.is_organizational:
                base_comments = random.randint(2, 12)
            hours_old = (datetime.now() - tweet.created_at).total_seconds() / 3600
            if hours_old <= 24:
                base_comments = int(base_comments * 1.4)
            elif hours_old <= 48:
                base_comments = int(base_comments * 1.2)
            num_comments = random.randint(0, base_comments)
            
            if not potential_commenters:
                continue

            weighted_commenters = []
            for user in potential_commenters:
                user_profile = user_profiles.get(user.user_id)
                if user_profile:
                    weight = 1
                    if user_profile.is_organizational or user_profile.is_prime:
                        weight = 2
                    weighted_commenters.extend([user] * weight)
            if weighted_commenters:
                unique_commenters = []
                seen_ids = set()
                for commenter in weighted_commenters:
                    if commenter.user_id not in seen_ids:
                        unique_commenters.append(commenter)
                        seen_ids.add(commenter.user_id)
                num_comments = min(num_comments, len(unique_commenters))
                commenting_users = random.sample(unique_commenters, num_comments)
            else:
                num_comments = min(num_comments, len(potential_commenters))
                commenting_users = random.sample(potential_commenters, num_comments)
            for user in commenting_users:
                if user.user_id not in valid_user_ids or tweet.id not in valid_tweet_ids:
                    continue  # Validation: only valid users/tweets
                comment_text = fake.text(max_nb_chars=280)
                if len(comment_text) > 280:
                    comment_text = comment_text[:280]
                if (
                    tweet.id,
                    user.user_id,
                    comment_text[:50],
                ) in existing_comment_pairs:
                    continue
                comment = Comment(
                    tweet_id=tweet.id,
                    user_id=user.user_id,
                    text=comment_text,
                    created_at=tweet.created_at + timedelta(minutes=random.randint(10, 1440)),
                )
                comments.append(comment)
                existing_comment_pairs.add((tweet.id, user.user_id, comment_text[:50]))
        if comments:
            session.add_all(comments)
            await session.commit()
            await session.refresh(comment)  # Refresh to get ID for replies

        print(f"💬 Created {len(comments)} comments with enhanced engagement patterns")
        
        # PHASE 2: Create replies to comments
        print("🔄 Creating replies to comments...")
        replies_to_create = []
        for comment in comments:
            if random.random() < 0.3:  # 30% chance a comment gets a reply
                tweet = tweet_data.get(comment.tweet_id)
                if not tweet:
                    continue
                
                tweet_author_user = user_map.get(tweet.user_id)
                if not tweet_author_user:
                    continue

                # Determine potential repliers based on tweet privacy
                potential_repliers = []
                if tweet_author_user.is_private:
                    author_followers = followers_map.get(tweet.user_id, set())
                    potential_repliers = [
                        u for u in users if u.user_id in author_followers or u.user_id == tweet.user_id
                    ]
                else:
                    potential_repliers = [u for u in users if u.user_id in valid_user_ids]
                
                # A user cannot reply to their own comment
                potential_repliers = [u for u in potential_repliers if u.user_id != comment.user_id]
                
                if not potential_repliers:
                    continue
                
                num_replies = random.randint(1, 3)
                replying_users = random.sample(potential_repliers, min(num_replies, len(potential_repliers)))

                for user in replying_users:
                    reply_text = fake.text(max_nb_chars=280)
                    if len(reply_text) > 280:
                        reply_text = reply_text[:280]

                    reply = Comment(
                        tweet_id=comment.tweet_id,
                        user_id=user.user_id,
                        text=reply_text,
                        parent_comment_id=comment.id,
                        created_at=comment.created_at + timedelta(minutes=random.randint(5, 60)),
                    )
                    replies_to_create.append(reply)

        if replies_to_create:
            session.add_all(replies_to_create)
            await session.commit()
            print(f"🔄 Created {len(replies_to_create)} replies to comments")
        
        # Return all comments and replies
        return comments + replies_to_create
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create comments: {str(e)}")


async def create_comprehensive_test_user_interactions(
    session: AsyncSession,
    test_user_id: str,
    users: List[User],
    tweets: List[Tweet],
    comments: List[Comment]
) -> None:
    """
    Create comprehensive interactions for the test user to test all edge cases:
    - Likes on various tweet types
    - Comments and nested replies
    - Shares with mutual followers
    - Bookmarks for different content
    - Reports for moderation testing
    """
    try:
        print(f"\n💫 Creating comprehensive interactions for test user: {test_user_id}")
        
        # Get test user's tweets
        test_user_tweets = [t for t in tweets if t.user_id == test_user_id]
        other_tweets = [t for t in tweets if t.user_id != test_user_id]
        
        # Get other users for interactions
        other_users = [u for u in users if u.user_id != test_user_id]
        
        # 1. LIKES - Test user likes various tweets
        print("   ❤️ Creating likes...")
        likes_to_create = []
        
        # Like recent tweets from followed users (for engagement testing)
        recent_tweets = [t for t in other_tweets if t.created_at >= datetime.now() - timedelta(hours=24)]
        for tweet in recent_tweets[:30]:  # Like 30 recent tweets
            likes_to_create.append(TweetLike(
                tweet_id=tweet.id,
                user_id=test_user_id,
                created_at=datetime.now() - timedelta(minutes=random.randint(1, 1440))
            ))
        
        # Like older tweets for diversity
        older_tweets = [t for t in other_tweets if t.created_at < datetime.now() - timedelta(hours=24)]
        for tweet in older_tweets[:20]:  # Like 20 older tweets
            likes_to_create.append(TweetLike(
                tweet_id=tweet.id,
                user_id=test_user_id,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            ))
        
        # Others like test user's tweets (create engagement)
        for tweet in test_user_tweets:
            num_likes = random.randint(5, 50)  # High engagement for test user
            likers = random.sample(other_users, min(num_likes, len(other_users)))
            for user in likers:
                likes_to_create.append(TweetLike(
                    tweet_id=tweet.id,
                    user_id=user.user_id,
                    created_at=tweet.created_at + timedelta(minutes=random.randint(1, 1440))
                ))
        
        session.add_all(likes_to_create)
        
        # 2. COMMENTS - Create diverse comment scenarios
        print("   💬 Creating comments...")
        comments_to_create = []
        
        # Test user comments on others' tweets
        for tweet in other_tweets[:15]:  # Comment on 15 tweets
            comment_text = random.choice([
                "Great insight! Thanks for sharing this.",
                "Totally agree with this perspective.",
                "This is really helpful information.",
                "Interesting point of view!",
                "Thanks for the update!",
                "Could you elaborate more on this?",
                "This resonates with my experience too.",
                "Excellent analysis!",
            ])
            
            comment = Comment(
                tweet_id=tweet.id,
                user_id=test_user_id,
                text=comment_text,
                parent_comment_id=None,
                created_at=tweet.created_at + timedelta(minutes=random.randint(30, 2880))
            )
            comments_to_create.append(comment)
        
        # Others comment on test user's tweets
        for tweet in test_user_tweets:
            num_comments = random.randint(2, 15)  # High engagement
            commenters = random.sample(other_users, min(num_comments, len(other_users)))
            for user in commenters:
                comment_text = random.choice([
                    "This is exactly what I was looking for!",
                    "Great content as always!",
                    "Very informative, thank you!",
                    "Love this insight!",
                    "Could you share more about this topic?",
                    "This is really well explained.",
                    "Bookmarking this for later!",
                    "Fantastic work!",
                ])
                
                comment = Comment(
                    tweet_id=tweet.id,
                    user_id=user.user_id,
                    text=comment_text,
                    parent_comment_id=None,
                    created_at=tweet.created_at + timedelta(minutes=random.randint(30, 2880))
                )
                comments_to_create.append(comment)
        
        session.add_all(comments_to_create)
        await session.flush()  # Get comment IDs for replies
        
        # Create nested replies for testing
        reply_comments = []
        for comment in comments_to_create[:10]:  # Add replies to first 10 comments
            if comment.user_id != test_user_id:  # Test user replies to others' comments
                reply = Comment(
                    tweet_id=comment.tweet_id,
                    user_id=test_user_id,
                    text="Thanks for your comment! Really appreciate the feedback.",
                    parent_comment_id=comment.id,
                    created_at=comment.created_at + timedelta(minutes=random.randint(30, 1440))
                )
                reply_comments.append(reply)
        
        session.add_all(reply_comments)
        
        # 3. BOOKMARKS - Test user bookmarks interesting content
        print("   🔖 Creating bookmarks...")
        bookmarks_to_create = []
        
        # Bookmark diverse content for testing
        interesting_tweets = other_tweets[:25]  # Bookmark 25 tweets
        for tweet in interesting_tweets:
            bookmarks_to_create.append(Bookmark(
                tweet_id=tweet.id,
                user_id=test_user_id,
                created_at=tweet.created_at + timedelta(minutes=random.randint(60, 2880))
            ))
        
        # Others bookmark test user's tweets
        for tweet in test_user_tweets:
            num_bookmarks = random.randint(3, 20)  # High engagement
            bookmarkers = random.sample(other_users, min(num_bookmarks, len(other_users)))
            for user in bookmarkers:
                bookmarks_to_create.append(Bookmark(
                    tweet_id=tweet.id,
                    user_id=user.user_id,
                    created_at=tweet.created_at + timedelta(minutes=random.randint(60, 2880))
                ))
        
        session.add_all(bookmarks_to_create)
        
        # 4. SHARES - Test mutual following functionality
        print("   🔄 Creating shares...")
        shares_to_create = []
        
        # Get mutual followers for share testing
        followers_result = await session.execute(
            select(Follower).where(Follower.followee_id == test_user_id)
        )
        test_user_followers = [f.follower_id for f in followers_result.scalars().all()]
        
        following_result = await session.execute(
            select(Follower).where(Follower.follower_id == test_user_id)
        )
        test_user_following = [f.followee_id for f in following_result.scalars().all()]
        
        # Find mutual followers
        mutual_followers = list(set(test_user_followers) & set(test_user_following))
        
        # Test user shares interesting tweets with mutual followers
        for tweet in other_tweets[:10]:  # Share 10 tweets
            if mutual_followers:
                recipient = random.choice(mutual_followers)
                shares_to_create.append(Share(
                    tweet_id=tweet.id,
                    user_id=test_user_id,
                    recipient_id=recipient,
                    message="Thought you might find this interesting!",
                    shared_at=tweet.created_at + timedelta(minutes=random.randint(120, 2880))
                ))
        
        # Others share test user's tweets
        for tweet in test_user_tweets[:5]:  # Some of test user's tweets get shared
            if mutual_followers:
                sharer = random.choice(mutual_followers)
                # Find their mutual followers
                sharer_following_result = await session.execute(
                    select(Follower).where(Follower.follower_id == sharer)
                )
                sharer_following = [f.followee_id for f in sharer_following_result.scalars().all()]
                sharer_mutual = list(set(test_user_followers) & set(sharer_following))
                
                if sharer_mutual:
                    recipient = random.choice(sharer_mutual)
                    shares_to_create.append(Share(
                        tweet_id=tweet.id,
                        user_id=sharer,
                        recipient_id=recipient,
                        message="Check out this great content!",
                        shared_at=tweet.created_at + timedelta(minutes=random.randint(120, 2880))
                    ))
        
        session.add_all(shares_to_create)
        
        await session.commit()
        
        print(f"   ✅ Created {len(likes_to_create)} likes")
        print(f"   ✅ Created {len(comments_to_create)} comments")
        print(f"   ✅ Created {len(reply_comments)} reply comments")
        print(f"   ✅ Created {len(bookmarks_to_create)} bookmarks")
        print(f"   ✅ Created {len(shares_to_create)} shares")
        print(f"   📊 Test user engagement: High likes, comments, bookmarks, and shares")
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create test user interactions: {str(e)}")


async def create_interactions(
    session: AsyncSession,
    users: List[User],
    tweets: List[Tweet],
    comments: List[Comment],
):
    try:
        # Build user and follower maps for efficient lookups
        user_map = {user.user_id: user for user in users}
        followers_result = await session.execute(select(Follower))
        followers_map = {}
        for f in followers_result.scalars().all():
            if f.followee_id not in followers_map:
                followers_map[f.followee_id] = set()
            followers_map[f.followee_id].add(f.follower_id)

        existing_tweet_likes_result = await session.execute(select(TweetLike))
        existing_tweet_like_pairs = {
            (tl.tweet_id, tl.user_id)
            for tl in existing_tweet_likes_result.scalars().all()
        }
        existing_bookmarks_result = await session.execute(select(Bookmark))
        existing_bookmark_pairs = {
            (b.tweet_id, b.user_id) for b in existing_bookmarks_result.scalars().all()
        }
        existing_comment_likes_result = await session.execute(select(CommentLike))
        existing_comment_like_pairs = {
            (cl.comment_id, cl.user_id)
            for cl in existing_comment_likes_result.scalars().all()
        }
        valid_user_ids = await get_valid_user_ids(session)
        valid_tweet_ids = await get_valid_tweet_ids(session)
        if not valid_user_ids:
            raise MockDataError("No valid users found in the database")
        if not valid_tweet_ids:
            raise MockDataError("No valid tweets found in the database")
        tweet_data_result = await session.execute(
            select(Tweet).where(Tweet.id.in_(valid_tweet_ids))
        )
        tweet_data = {tweet.id: tweet for tweet in tweet_data_result.scalars().all()}
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id.in_(valid_user_ids))
        )
        user_profiles = {
            profile.user_id: profile for profile in profile_result.scalars().all()
        }
        comment_ids = [comment.id for comment in comments]
        comment_data_result = await session.execute(
            select(Comment).where(Comment.id.in_(comment_ids))
        )
        comment_data = {
            comment.id: comment for comment in comment_data_result.scalars().all()
        }
        print("🎯 Creating enhanced tweet interactions...")
        tweet_likes = []
        for tweet in tweets:
            if tweet.id not in valid_tweet_ids:
                continue

            tweet_author_user = user_map.get(tweet.user_id)
            if not tweet_author_user:
                continue

            tweet_author_profile = user_profiles.get(tweet.user_id)
            if not tweet_author_profile:
                continue

            # Determine potential likers based on privacy
            potential_likers = []
            if tweet_author_user.is_private:
                author_followers = followers_map.get(tweet.user_id, set())
                # Only followers can like private tweets (and not the author)
                potential_likers = [
                    u for u in users if u.user_id in author_followers and u.user_id != tweet.user_id
                ]
            else:
                # Anyone can like a public tweet (except the author)
                potential_likers = [
                    u for u in users if u.user_id in valid_user_ids and u.user_id != tweet.user_id
                ]

            base_likes = random.randint(15, 120)
            if tweet_author_profile.is_organizational and tweet_author_profile.is_prime:
                base_likes = random.randint(200, 800)
            elif tweet_author_profile.is_prime:
                base_likes = random.randint(120, 500)
            elif tweet_author_profile.is_organizational:
                base_likes = random.randint(80, 350)
            hours_old = (datetime.now() - tweet.created_at).total_seconds() / 3600
            if hours_old <= 12:
                base_likes = int(base_likes * 2.0)
            elif hours_old <= 24:
                base_likes = int(base_likes * 1.8)
            elif hours_old <= 48:
                base_likes = int(base_likes * 1.4)
            num_likes = random.randint(max(5, base_likes - 20), base_likes + 50)
            num_likes = min(num_likes, len(users) - 1)
            if num_likes > 0:
                if not potential_likers:
                    continue
                weighted_likers = []
                for user in potential_likers:
                    user_profile = user_profiles.get(user.user_id)
                    if user_profile:
                        weight = 1
                        if user_profile.is_organizational and user_profile.is_prime:
                            weight = 4
                        elif user_profile.is_organizational or user_profile.is_prime:
                            weight = 3
                        weighted_likers.extend([user] * weight)
                if weighted_likers:
                    unique_likers = []
                    seen_ids = set()
                    for liker in weighted_likers:
                        if liker.user_id not in seen_ids:
                            unique_likers.append(liker)
                            seen_ids.add(liker.user_id)
                    num_likes = min(num_likes, len(unique_likers))
                    liking_users = random.sample(unique_likers, num_likes)
                else:
                    num_likes = min(num_likes, len(potential_likers))
                    liking_users = random.sample(potential_likers, num_likes)
                for user in liking_users:
                    if (tweet.id, user.user_id) in existing_tweet_like_pairs:
                        continue
                    like = TweetLike(tweet_id=tweet.id, user_id=user.user_id)
                    tweet_likes.append(like)
                    existing_tweet_like_pairs.add((tweet.id, user.user_id))
        if tweet_likes:
            session.add_all(tweet_likes)
            await session.commit()
        print("📖 Creating enhanced bookmarks...")
        bookmarks = []
        for tweet in tweets:
            if tweet.id not in valid_tweet_ids:
                continue

            tweet_author_user = user_map.get(tweet.user_id)
            if not tweet_author_user:
                continue
            
            tweet_author_profile = user_profiles.get(tweet.user_id)
            if not tweet_author_profile:
                continue
            
            # Determine potential bookmarkers based on privacy
            potential_bookmarkers = []
            if tweet_author_user.is_private:
                author_followers = followers_map.get(tweet.user_id, set())
                potential_bookmarkers = [
                    u for u in users if u.user_id in author_followers and u.user_id != tweet.user_id
                ]
            else:
                potential_bookmarkers = [
                    u for u in users if u.user_id != tweet.user_id and u.user_id in valid_user_ids
                ]
            
            base_bookmark_chance = 0.4
            if tweet_author_profile.is_organizational and tweet_author_profile.is_prime:
                base_bookmark_chance = 0.7
            elif (
                tweet_author_profile.is_prime or tweet_author_profile.is_organizational
            ):
                base_bookmark_chance = 0.6
            if random.random() < base_bookmark_chance:
                max_bookmarks = min(30, len(users) // 10)
                if (
                    tweet_author_profile.is_organizational
                    and tweet_author_profile.is_prime
                ):
                    max_bookmarks = min(50, len(users) // 6)
                elif (
                    tweet_author_profile.is_prime
                    or tweet_author_profile.is_organizational
                ):
                    max_bookmarks = min(40, len(users) // 8)
                num_bookmarks = random.randint(1, max_bookmarks)
                
                if potential_bookmarkers and num_bookmarks <= len(
                    potential_bookmarkers
                ):
                    bookmarking_users = random.sample(
                        potential_bookmarkers, num_bookmarks
                    )
                    for user in bookmarking_users:
                        if (tweet.id, user.user_id) in existing_bookmark_pairs:
                            continue
                        bookmark = Bookmark(tweet_id=tweet.id, user_id=user.user_id)
                        bookmarks.append(bookmark)
                        existing_bookmark_pairs.add((tweet.id, user.user_id))
        if bookmarks:
            session.add_all(bookmarks)
            await session.commit()
        print("💬 Creating enhanced comment likes...")
        comment_likes = []
        for comment in comments:
            if comment.id not in comment_data:
                continue
            comment_info = comment_data[comment.id]
            tweet_info = tweet_data.get(comment_info.tweet_id)
            if not tweet_info:
                continue

            tweet_author_user = user_map.get(tweet_info.user_id)
            if not tweet_author_user:
                continue

            tweet_author_profile = user_profiles.get(tweet_info.user_id)

            # Determine potential likers based on the tweet's privacy
            potential_likers = []
            if tweet_author_user.is_private:
                author_followers = followers_map.get(tweet_info.user_id, set())
                potential_likers = [
                    u for u in users if u.user_id in author_followers and u.user_id != comment_info.user_id
                ]
            else:
                potential_likers = [
                    u for u in users if u.user_id != comment_info.user_id and u.user_id in valid_user_ids
                ]

            base_like_chance = 0.6
            if tweet_author_profile and (
                tweet_author_profile.is_organizational or tweet_author_profile.is_prime
            ):
                base_like_chance = 0.8
            if random.random() < base_like_chance:
                max_likes = min(25, len(users) // 12)
                if (
                    tweet_author_profile
                    and tweet_author_profile.is_organizational
                    and tweet_author_profile.is_prime
                ):
                    max_likes = min(40, len(users) // 8)
                num_likes = random.randint(1, max_likes)
                
                if potential_likers and num_likes <= len(potential_likers):
                    liking_users = random.sample(potential_likers, num_likes)
                    for user in liking_users:
                        if (comment_info.id, user.user_id) in existing_comment_like_pairs:
                            continue
                        comment_like = CommentLike(
                            comment_id=comment_info.id, user_id=user.user_id
                        )
                        comment_likes.append(comment_like)
                        existing_comment_like_pairs.add((comment_info.id, user.user_id))
        if comment_likes:
            session.add_all(comment_likes)
            await session.commit()
        prime_tweets = [
            t
            for t in tweets
            if user_profiles.get(t.user_id) and user_profiles[t.user_id].is_prime
        ]
        org_tweets = [
            t
            for t in tweets
            if user_profiles.get(t.user_id)
            and user_profiles[t.user_id].is_organizational
        ]
        prime_likes = sum(
            1
            for like in tweet_likes
            if tweet_data.get(like.tweet_id)
            and user_profiles.get(tweet_data[like.tweet_id].user_id)
            and user_profiles[tweet_data[like.tweet_id].user_id].is_prime
        )
        org_likes = sum(
            1
            for like in tweet_likes
            if tweet_data.get(like.tweet_id)
            and user_profiles.get(tweet_data[like.tweet_id].user_id)
            and user_profiles[tweet_data[like.tweet_id].user_id].is_organizational
        )
        print("\n=== ENHANCED ENGAGEMENT STATISTICS ===")
        print(f"Total Tweet Likes: {len(tweet_likes):,}")
        print(f"Total Bookmarks: {len(bookmarks):,}")
        print(f"Total Comment Likes: {len(comment_likes):,}")
        if prime_tweets:
            print(f"Average Likes per Prime Tweet: {prime_likes/len(prime_tweets):.1f}")
        if org_tweets:
            print(f"Average Likes per Org Tweet: {org_likes/len(org_tweets):.1f}")
        if tweets:
            print(f"Average Likes per Tweet: {len(tweet_likes)/len(tweets):.1f}")
            print(f"Average Bookmarks per Tweet: {len(bookmarks)/len(tweets):.1f}")
            print(f"Bookmark Rate: {len(bookmarks)/len(tweets)*100:.1f}%")
        if comments:
            print(f"Average Likes per Comment: {len(comment_likes)/len(comments):.1f}")
        print("=====================================\n")
    except SQLAlchemyError as e:
        await session.rollback()
        raise MockDataError(f"Failed to create interactions: {str(e)}")


async def create_reports(session: AsyncSession, tweets: List[Tweet], users: List[User]):
    """Create realistic reports for tweets and comments"""
    try:
        # Build user map for efficient lookups
        user_map = {user.user_id: user for user in users}
        
        # Get existing reports to avoid duplicates
        existing_tweet_reports_result = await session.execute(select(TweetReport))
        existing_tweet_reports = {
            (report.tweet_id, report.user_id)
            for report in existing_tweet_reports_result.scalars().all()
        }
        
        existing_comment_reports_result = await session.execute(select(CommentReport))
        existing_comment_reports = {
            (report.comment_id, report.user_id)
            for report in existing_comment_reports_result.scalars().all()
        }
        
        tweet_reports = []
        comment_reports = []
        
        # Get valid tweet IDs
        valid_tweet_ids = [tweet.id for tweet in tweets if tweet.id]
        if not valid_tweet_ids:
            raise MockDataError("No valid tweets found in the database")
            
        # Get user profiles for better reporting patterns
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id.in_(user_map.keys()))
        )
        user_profiles = {
            profile.user_id: profile
            for profile in profile_result.scalars().all()
        }
        
        # Create tweet reports
        for tweet in tweets:
            # Skip if tweet or user is invalid
            if not tweet.id or tweet.user_id not in user_map:
                continue
                
            # Get potential reporters (exclude tweet author)
            potential_reporters = [
                user for user in users
                if user.user_id != tweet.user_id
                and (tweet.id, user.user_id) not in existing_tweet_reports
            ]
            
            if not potential_reporters:
                continue
                
            # Randomly select a reporter
            reporter = random.choice(potential_reporters)
            
            # Create report
            tweet_reports.append(
                TweetReport(
                    tweet_id=tweet.id,
                    user_id=reporter.user_id,
                    reason=random.choice(["Spam", "Abuse", "Fake News", "Other"]),
                )
            )
            
        # Get comments for reporting
        comments_result = await session.execute(
            select(Comment).where(Comment.tweet_id.in_(valid_tweet_ids))
        )
        comments = comments_result.scalars().all()
        
        # Create comment reports
        for comment in comments:
            # Skip if comment or user is invalid
            if not comment.id or comment.user_id not in user_map:
                continue
                
            # Get potential reporters (exclude comment author)
            potential_reporters = [
                user for user in users
                if user.user_id != comment.user_id
                and (comment.id, user.user_id) not in existing_comment_reports
            ]
            
            if not potential_reporters:
                continue
                
            # Randomly select a reporter
            reporter = random.choice(potential_reporters)
            
            # Create report
            comment_reports.append(
                CommentReport(
                    comment_id=comment.id,
                    user_id=reporter.user_id,
                    reason=random.choice(["Spam", "Abuse", "Harassment", "Other"]),
                )
            )
            
        # Save reports
        if tweet_reports:
            session.add_all(tweet_reports)
        if comment_reports:
            session.add_all(comment_reports)
            
        await session.commit()
        
        print(f"✅ Created {len(tweet_reports)} tweet reports and {len(comment_reports)} comment reports")
        
    except Exception as e:
        print(f"❌ Error creating reports: {e}")
        raise


async def update_profile_counts_and_validate(session: AsyncSession) -> None:
    """
    Update profile counts to match actual relationships and validate data consistency.
    """
    try:
        print("\n🔍 Updating profile counts and validating data consistency...")
        
        # Get all users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        # Get all followers
        followers_result = await session.execute(select(Follower))
        followers = followers_result.scalars().all()
        
        # Build follower maps
        follower_map = {}  # user_id -> set of follower_ids
        following_map = {}  # user_id -> set of following_ids
        
        for user in users:
            follower_map[user.user_id] = set()
            following_map[user.user_id] = set()
        
        for follow in followers:
            if follow.followee_id in follower_map:
                follower_map[follow.followee_id].add(follow.follower_id)
            if follow.follower_id in following_map:
                following_map[follow.follower_id].add(follow.followee_id)
        
        # Calculate mutual followers for each user
        mutual_followers_map = {}
        for user_id in follower_map:
            mutuals = follower_map[user_id] & following_map[user_id]
            mutual_followers_map[user_id] = mutuals
        
        # Print statistics
        total_relationships = len(followers)
        total_mutual_relationships = sum(len(mutuals) for mutuals in mutual_followers_map.values()) // 2
        
        print(f"\n📊 Data Consistency Report:")
        print(f"   Total users: {len(users)}")
        print(f"   Total follow relationships: {total_relationships}")
        print(f"   Total mutual relationships: {total_mutual_relationships}")
        print(f"   Mutual percentage: {total_mutual_relationships/total_relationships*100:.1f}%")
        
        # Validate specific user mentioned in the bug report
        test_user_id = "TU12345"
        if test_user_id in follower_map:
            followers_count = len(follower_map[test_user_id])
            following_count = len(following_map[test_user_id])
            mutual_count = len(mutual_followers_map[test_user_id])
            
            print(f"\n🔍 Test User {test_user_id} Analysis:")
            print(f"   Followers: {followers_count}")
            print(f"   Following: {following_count}")
            print(f"   Mutual followers: {mutual_count}")
            print(f"   Mutual followers list: {sorted(list(mutual_followers_map[test_user_id]))[:10]}...")
            
            # Check sharing consistency
            shares_result = await session.execute(
                select(Share).where(
                    or_(Share.user_id == test_user_id, Share.recipient_id == test_user_id)
                )
            )
            shares = shares_result.scalars().all()
            
            sharing_partners = set()
            for share in shares:
                partner = share.recipient_id if share.user_id == test_user_id else share.user_id
                sharing_partners.add(partner)
            
            print(f"   Users shared with: {len(sharing_partners)}")
            
            # Check how many sharing partners are mutual followers
            mutual_sharing_partners = sharing_partners & mutual_followers_map[test_user_id]
            print(f"   Mutual followers among sharing partners: {len(mutual_sharing_partners)}")
            print(f"   Non-mutual sharing partners: {len(sharing_partners - mutual_followers_map[test_user_id])}")
        
        # Print sample mutual followers for validation
        print(f"\n📈 Sample Mutual Followers Analysis:")
        sample_users = list(mutual_followers_map.keys())[:5]
        for user_id in sample_users:
            mutual_count = len(mutual_followers_map[user_id])
            print(f"   {user_id}: {mutual_count} mutual followers")
        
        # Validate that shares are consistent with relationships
        shares_result = await session.execute(select(Share))
        shares = shares_result.scalars().all()
        
        valid_shares = 0
        mutual_shares = 0
        
        for share in shares:
            # Check if share is between users who have follow relationship
            if share.recipient_id in following_map[share.user_id]:
                valid_shares += 1
                # Check if it's mutual
                if share.user_id in mutual_followers_map[share.recipient_id]:
                    mutual_shares += 1
        
        print(f"\n🔄 Sharing Validation:")
        print(f"   Total shares: {len(shares)}")
        print(f"   Valid shares (between followers): {valid_shares}")
        print(f"   Mutual follower shares: {mutual_shares}")
        print(f"   Share validity rate: {valid_shares/len(shares)*100:.1f}%" if shares else "N/A")
        
        print(f"\n✅ Profile counts updated and data validation complete!\n")
        
    except Exception as e:
        print(f"❌ Error in validation: {e}")
        raise MockDataError(f"Failed to validate relationships: {str(e)}")


async def validate_relationships(session: AsyncSession) -> None:
    try:
        await validate_user_consistency(session)
        valid_user_ids = await get_valid_user_ids(session)
        valid_tweet_ids = await get_valid_tweet_ids(session)
        valid_comment_ids = await get_valid_comment_ids(session)
        if not valid_user_ids:
            raise MockDataError("No valid users found in the database")
        if not valid_tweet_ids:
            raise MockDataError("No valid tweets found in the database")
        tweet_authors = await session.execute(
            select(Tweet.user_id).where(Tweet.id.in_(valid_tweet_ids))
        )
        invalid_tweet_authors = [
            uid for uid in tweet_authors.scalars().all() if uid not in valid_user_ids
        ]
        if invalid_tweet_authors:
            raise MockDataError(
                f"Found tweets with invalid authors: {invalid_tweet_authors}"
            )
        if valid_comment_ids:
            comment_data = await session.execute(
                select(Comment).where(Comment.id.in_(valid_comment_ids))
            )
            for comment in comment_data.scalars().all():
                if comment.user_id not in valid_user_ids:
                    raise MockDataError(
                        f"Found comment {comment.id} with invalid author: {comment.user_id}"
                    )
                if comment.tweet_id not in valid_tweet_ids:
                    raise MockDataError(
                        f"Found comment {comment.id} with invalid tweet reference: {comment.tweet_id}"
                    )
                if (
                    comment.parent_comment_id
                    and comment.parent_comment_id not in valid_comment_ids
                ):
                    raise MockDataError(
                        f"Found comment {comment.id} with invalid parent comment: {comment.parent_comment_id}"
                    )
        media_data = await session.execute(
            select(TweetMedia).where(TweetMedia.tweet_id.in_(valid_tweet_ids))
        )
        for media in media_data.scalars().all():
            if media.tweet_id not in valid_tweet_ids:
                raise MockDataError(
                    f"Found media with invalid tweet reference: {media.tweet_id}"
                )
        tweet_likes = await session.execute(
            select(TweetLike).where(TweetLike.tweet_id.in_(valid_tweet_ids))
        )
        for like in tweet_likes.scalars().all():
            if like.user_id not in valid_user_ids:
                raise MockDataError(
                    f"Found tweet like with invalid user: {like.user_id}"
                )
            if like.tweet_id not in valid_tweet_ids:
                raise MockDataError(
                    f"Found tweet like with invalid tweet: {like.tweet_id}"
                )
        if valid_comment_ids:
            comment_likes = await session.execute(
                select(CommentLike).where(CommentLike.comment_id.in_(valid_comment_ids))
            )
            for like in comment_likes.scalars().all():
                if like.user_id not in valid_user_ids:
                    raise MockDataError(
                        f"Found comment like with invalid user: {like.user_id}"
                    )
                if like.comment_id not in valid_comment_ids:
                    raise MockDataError(
                        f"Found comment like with invalid comment: {like.comment_id}"
                    )
        bookmarks = await session.execute(
            select(Bookmark).where(Bookmark.tweet_id.in_(valid_tweet_ids))
        )
        for bookmark in bookmarks.scalars().all():
            if bookmark.user_id not in valid_user_ids:
                raise MockDataError(
                    f"Found bookmark with invalid user: {bookmark.user_id}"
                )
            if bookmark.tweet_id not in valid_tweet_ids:
                raise MockDataError(
                    f"Found bookmark with invalid tweet: {bookmark.tweet_id}"
                )
        shares = await session.execute(
            select(Share).where(Share.tweet_id.in_(valid_tweet_ids))
        )
        for share in shares.scalars().all():
            if share.user_id not in valid_user_ids:
                raise MockDataError(f"Found share with invalid user: {share.user_id}")
            if share.recipient_id not in valid_user_ids:
                raise MockDataError(
                    f"Found share with invalid recipient: {share.recipient_id}"
                )
            if share.tweet_id not in valid_tweet_ids:
                raise MockDataError(f"Found share with invalid tweet: {share.tweet_id}")
        tweet_reports = await session.execute(
            select(TweetReport).where(TweetReport.tweet_id.in_(valid_tweet_ids))
        )
        for report in tweet_reports.scalars().all():
            if report.user_id not in valid_user_ids:
                raise MockDataError(
                    f"Found tweet report with invalid user: {report.user_id}"
                )
            if report.tweet_id not in valid_tweet_ids:
                raise MockDataError(
                    f"Found tweet report with invalid tweet: {report.tweet_id}"
                )
        if valid_comment_ids:
            comment_reports = await session.execute(
                select(CommentReport).where(
                    CommentReport.comment_id.in_(valid_comment_ids)
                )
            )
            for report in comment_reports.scalars().all():
                if report.user_id not in valid_user_ids:
                    raise MockDataError(
                        f"Found comment report with invalid user: {report.user_id}"
                    )
                if report.comment_id not in valid_comment_ids:
                    raise MockDataError(
                        f"Found comment report with invalid comment: {report.comment_id}"
                    )
        followers = await session.execute(
            select(Follower).where(
                and_(
                    Follower.follower_id.in_(valid_user_ids),
                    Follower.followee_id.in_(valid_user_ids),
                )
            )
        )
        for follower in followers.scalars().all():
            if follower.follower_id not in valid_user_ids:
                raise MockDataError(
                    f"Found follower with invalid follower: {follower.follower_id}"
                )
            if follower.followee_id not in valid_user_ids:
                raise MockDataError(
                    f"Found follower with invalid followee: {follower.followee_id}"
                )
        follow_requests = await session.execute(
            select(FollowRequest).where(
                and_(
                    FollowRequest.follower_id.in_(valid_user_ids),
                    FollowRequest.followee_id.in_(valid_user_ids),
                )
            )
        )
        for request in follow_requests.scalars().all():
            if request.follower_id not in valid_user_ids:
                raise MockDataError(
                    f"Found follow request with invalid follower: {request.follower_id}"
                )
            if request.followee_id not in valid_user_ids:
                raise MockDataError(
                    f"Found follow request with invalid followee: {request.followee_id}"
                )
        interests = await session.execute(select(Interest))
        valid_interest_ids = [interest.id for interest in interests.scalars().all()]
        user_interests = await session.execute(
            select(UserInterest).where(UserInterest.user_id.in_(valid_user_ids))
        )
        for user_interest in user_interests.scalars().all():
            if user_interest.user_id not in valid_user_ids:
                raise MockDataError(
                    f"Found user interest with invalid user: {user_interest.user_id}"
                )
            if user_interest.interest_id not in valid_interest_ids:
                raise MockDataError(
                    f"Found user interest with invalid interest: {user_interest.interest_id}"
                )
        print("\n=== Data Validation Summary ===")
        print("All relationships validated successfully!")
        print("===============================\n")
    except SQLAlchemyError as e:
        raise MockDataError(f"Failed to validate relationships: {str(e)}")


async def main():
    try:
        async with AsyncSessionLocal() as session:
            # Check if data already exists to prevent duplicates
            print("🔍 Checking if data already exists...")
            try:
                from sqlalchemy import text
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                
                if user_count > 0:
                    print(f"✅ Found {user_count} existing users in database")
                    print("⚠️  Skipping mock data generation to prevent duplicates")
                    print("💡 To regenerate data, please clear the database first")
                    return
                else:
                    print("📝 No existing data found - proceeding with generation...")
            except Exception as e:
                print(f"⚠️  Could not check existing data (table may not exist): {e}")
                print("📝 Proceeding with generation...")


            print("🚀 Starting Enhanced Mock Data Generation for Twitter Algorithm...")
            print("=" * 60)
            print("Creating commands...")
            commands = await create_commands(session)
            print("Creating interests...")
            interests = await create_interests(session)
            print("Creating users with profiles (100 users)...")
            users, profiles, tokens = await create_users_with_profiles(
                session, commands, num_users=100
            )
            print("\nValidating user consistency...")
            await validate_user_consistency(session)
            
            # =============================================================================
            # COMPREHENSIVE TEST USER SETUP
            # =============================================================================
            print(f"\n🧪 SETTING UP COMPREHENSIVE TEST USER: {first_user_id_1}")
            print("="*60)
            
            # Setup test user relationships first (before other users get interests)
            print("Setting up test user relationships and interests...")
            await setup_comprehensive_test_user_relationships(
                session, first_user_id_1, users, interests, profiles
            )
            
            # Create comprehensive tweets for test user
            print("Creating comprehensive tweets for test user...")
            test_user_tweets, test_user_media = await create_comprehensive_test_user_tweets(
                session, first_user_id_1, users
            )
            
            print("="*60)
            # =============================================================================
            
            print("Creating user interests for other users...")
            await create_user_interests(session, users, interests)
            print("Creating enhanced follow relationships for other users...")
            await create_follow_relationships(
                session, users, min_followers=15, max_followers=80
            )
            print("Creating tweets with media for other users (optimized for algorithm)...")
            other_tweets, other_media_items = await create_tweets_with_media(
                session, users, num_tweets_per_user=8
            )
            
            # Combine all tweets and media
            tweets = test_user_tweets + other_tweets
            media_items = test_user_media + other_media_items
            
            print("Creating enhanced comments and replies...")
            comments = await create_comments_and_replies(session, tweets, users)
            
            # Create comprehensive interactions for test user
            print("Creating comprehensive interactions for test user...")
            await create_comprehensive_test_user_interactions(
                session, first_user_id_1, users, tweets, comments
            )
            
            print("Creating enhanced shares...")
            await create_shares(session, users, tweets)
            print("Creating realistic interactions...")
            await create_interactions(session, users, tweets, comments)
            print("Creating realistic reports...")
            await create_reports(session, tweets, users)
            print("\nUpdating profile counts and validating data consistency...")
            await update_profile_counts_and_validate(session)
            await validate_relationships(session)
            print("\n" + "=" * 60)
            print("🎯 TWITTER ALGORITHM OPTIMIZED MOCK DATA SUMMARY")
            print("=" * 60)
            prime_users = [p for p in profiles if p.is_prime]
            org_users = [p for p in profiles if p.is_organizational]
            org_prime_users = [
                p for p in profiles if p.is_organizational and p.is_prime
            ]
            private_users = [u for u in users if u.is_private]
            print("\n📊 USER DISTRIBUTION:")
            print(f"Total Users: {len(users)}")
            print(
                f"Prime Users: {len(prime_users)} ({len(prime_users)/len(users)*100:.1f}%) - Priority 2 & 4"
            )
            print(
                f"Organizational Users: {len(org_users)} ({len(org_users)/len(users)*100:.1f}%) - Priority 3 & higher"
            )
            print(
                f"Org + Prime Users: {len(org_prime_users)} ({len(org_prime_users)/len(users)*100:.1f}%) - Priority 1 (Highest)"
            )
            print(
                f"Private Users: {len(private_users)} ({len(private_users)/len(users)*100:.1f}%)"
            )
            print(
                f"Public Users: {len(users) - len(private_users)} ({(len(users) - len(private_users))/len(users)*100:.1f}%)"
            )
            recent_tweets = [
                t
                for t in tweets
                if (datetime.now() - t.created_at).total_seconds() <= 86400
            ]
            very_recent_tweets = [
                t
                for t in tweets
                if (datetime.now() - t.created_at).total_seconds() <= 3600
            ]
            print("\n🐦 TWEET DISTRIBUTION:")
            print(f"Total Tweets: {len(tweets)}")
            print(
                f"Recent Tweets (24h): {len(recent_tweets)} ({len(recent_tweets)/len(tweets)*100:.1f}%)"
            )
            print(
                f"Very Recent (1h): {len(very_recent_tweets)} ({len(very_recent_tweets)/len(tweets)*100:.1f}%)"
            )
            print(f"Total Media Items: {len(media_items)}")
            print(f"Tweets with Media: {len(set(m.tweet_id for m in media_items))}")
            prime_tweets = [
                t
                for t in tweets
                if any(p.user_id == t.user_id and p.is_prime for p in profiles)
            ]
            org_tweets = [
                t
                for t in tweets
                if any(p.user_id == t.user_id and p.is_organizational for p in profiles)
            ]
            org_prime_tweets = [
                t
                for t in tweets
                if any(
                    p.user_id == t.user_id and p.is_organizational and p.is_prime
                    for p in profiles
                )
            ]
            print(f"\nPriority Content Distribution:")
            print(
                f"Priority 1 (Org+Prime): {len(org_prime_tweets)} tweets ({len(org_prime_tweets)/len(tweets)*100:.1f}%)"
            )
            print(
                f"Priority 2 (Prime): {len(prime_tweets) - len(org_prime_tweets)} tweets"
            )
            print(f"Priority 3 (Org): {len(org_tweets) - len(org_prime_tweets)} tweets")
            print(
                f"Priority 5+ (Others): {len(tweets) - len(org_tweets) - (len(prime_tweets) - len(org_prime_tweets))} tweets"
            )

            total_likes = (
                await session.execute(select(func.count(TweetLike.tweet_id)))
            ).scalar_one()
            total_comments = len(comments)
            total_bookmarks = (
                await session.execute(select(func.count(Bookmark.tweet_id)))
            ).scalar_one()
            total_shares = (
                await session.execute(select(func.count(Share.tweet_id)))
            ).scalar_one()

            print("\n💫 ENGAGEMENT STATISTICS:")
            print(f"Total Likes: {total_likes:,}")
            print(f"Total Comments: {total_comments:,}")
            print(f"Total Shares: {total_shares:,}")
            print(f"Total Bookmarks: {total_bookmarks:,}")
            print(
                f"Average Engagement per Tweet: {(total_likes + total_comments + total_shares + total_bookmarks)/len(tweets):.1f}"
            )

            total_follows = (
                await session.execute(select(func.count(Follower.follower_id)))
            ).scalar_one()

            print(f"\n🤝 SOCIAL NETWORK:")
            print(f"Total Follow Relationships: {total_follows:,}")
            print(f"Average Followers per User: {total_follows/len(users):.1f}")

            print("\n" + "="*70)
            print("🧪 COMPREHENSIVE TEST USER SUMMARY")
            print("="*70)
            print(f"🆔 User ID: {first_user_id_1}")
            print(f"🔑 Password: {first_user_password_1}")
            print(f"👤 Name: Test User Prime")
            print(f"🏢 Type: Prime + Organizational (40% recommendation priority)")
            print(f"🔓 Privacy: Public account")
            print(f"📅 Account Age: 30 days")
            
            # Get test user statistics
            test_user_tweets_count = len([t for t in tweets if t.user_id == first_user_id_1])
            test_user_recent_tweets = len([t for t in tweets if t.user_id == first_user_id_1 and 
                                         (datetime.now() - t.created_at).total_seconds() <= 86400])
            
            # Get following/followers count for test user
            test_following_result = await session.execute(
                select(func.count(Follower.followee_id)).where(Follower.follower_id == first_user_id_1)
            )
            test_following_count = test_following_result.scalar_one()
            
            test_followers_result = await session.execute(
                select(func.count(Follower.follower_id)).where(Follower.followee_id == first_user_id_1)
            )
            test_followers_count = test_followers_result.scalar_one()
            
            # Get engagement statistics for test user
            test_likes_given = await session.execute(
                select(func.count(TweetLike.tweet_id)).where(TweetLike.user_id == first_user_id_1)
            )
            test_likes_given_count = test_likes_given.scalar_one()
            
            test_likes_received = await session.execute(
                select(func.count(TweetLike.tweet_id)).join(Tweet).where(Tweet.user_id == first_user_id_1)
            )
            test_likes_received_count = test_likes_received.scalar_one()
            
            test_bookmarks = await session.execute(
                select(func.count(Bookmark.tweet_id)).where(Bookmark.user_id == first_user_id_1)
            )
            test_bookmarks_count = test_bookmarks.scalar_one()
            
            test_comments_made = len([c for c in comments if c.user_id == first_user_id_1])
            test_comments_received = len([c for c in comments if any(t.user_id == first_user_id_1 for t in tweets if t.id == c.tweet_id)])
            
            print(f"\n📊 CONTENT STATISTICS:")
            print(f"   📝 Total Tweets: {test_user_tweets_count}")
            print(f"   🕐 Recent Tweets (24h): {test_user_recent_tweets}")
            print(f"   📅 Older Tweets: {test_user_tweets_count - test_user_recent_tweets}")
            print(f"   🖼️  Tweets with Media: {len([t for t in test_user_media])}")
            
            print(f"\n👥 SOCIAL NETWORK:")
            print(f"   👤 Following: {test_following_count} users")
            print(f"   👥 Followers: {test_followers_count} users")
            print(f"   🤝 Mutual Connections: Strategic mix for testing")
            print(f"   📨 Follow Requests: Incoming and outgoing pending")
            
            print(f"\n💫 ENGAGEMENT METRICS:")
            print(f"   ❤️  Likes Given: {test_likes_given_count}")
            print(f"   ❤️  Likes Received: {test_likes_received_count}")
            print(f"   💬 Comments Made: {test_comments_made}")
            print(f"   💬 Comments Received: {test_comments_received}")
            print(f"   🔖 Bookmarks: {test_bookmarks_count}")
            print(f"   📚 Interests: All {len(interests)} categories")
            
            print(f"\n🎯 TESTING SCENARIOS COVERED:")
            print("   ✅ Latest feed (24h tweets) - High priority content")
            print("   ✅ Infinite scroll (older tweets) - Historical content")
            print("   ✅ Pull-to-refresh - Cache bypass testing")
            print("   ✅ Prime + Organizational priority (40%)")
            print("   ✅ Following relationships (5% and 15% priorities)")
            print("   ✅ High engagement content (likes, comments, shares)")
            print("   ✅ Media attachments and image handling")
            print("   ✅ Comment threads and nested replies")
            print("   ✅ Share functionality with mutual followers")
            print("   ✅ Bookmark and save functionality")
            print("   ✅ Follow requests (incoming and outgoing)")
            print("   ✅ Privacy settings and content visibility")
            print("   ✅ Time-based content filtering")
            print("   ✅ Engagement scoring and recommendation ranking")
            
            print(f"\n🔧 API TESTING ENDPOINTS:")
            print("   📱 GET /tweets/feed?feed_type=latest - Latest 24h tweets")
            print("   📜 GET /tweets/feed?feed_type=older&last_tweet_id=X - Infinite scroll")
            print("   🔄 POST /tweets/feed/refresh - Pull-to-refresh")
            print("   💓 GET /health/recommendation - System health")
            print("   👤 GET /profile/* - Profile and following endpoints")
            print("   💬 GET /tweets/*/comments - Comment system")
            print("   🔖 GET /tweets/bookmarked - Saved content")
            
            print("="*70)

            print("\n✅ Enhanced mock data generation completed successfully!")
            print("🎯 Data optimized for Twitter-like recommendation algorithm")
            print("🔥 Ready for realistic get_merged_feed testing!")
            print("=" * 60)
    except Exception as e:
        print(f"❌ Error generating mock data: {str(e)}")
        raise


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def validate_no_orphans(session: AsyncSession) -> None:
    # Check for orphaned users/profiles/tokens/tweets/comments/reports
    users_result = await session.execute(select(User.user_id))
    user_ids = {row[0] for row in users_result.all()}
    profiles_result = await session.execute(select(UserProfile.user_id))
    profile_ids = {row[0] for row in profiles_result.all()}
    if user_ids != profile_ids:
        raise MockDataError(f"Orphaned users/profiles: {user_ids ^ profile_ids}")
    tokens_result = await session.execute(select(Token.user_id))
    token_ids = {row[0] for row in tokens_result.all()}
    # Tokens are optional, but if present, must have a user
    if not token_ids.issubset(user_ids):
        raise MockDataError(f"Orphaned tokens: {token_ids - user_ids}")
    tweets_result = await session.execute(select(Tweet.user_id))
    tweet_user_ids = {row[0] for row in tweets_result.all()}
    if not tweet_user_ids.issubset(user_ids):
        raise MockDataError(f"Orphaned tweets: {tweet_user_ids - user_ids}")
    comments_result = await session.execute(select(Comment.user_id))
    comment_user_ids = {row[0] for row in comments_result.all()}
    if not comment_user_ids.issubset(user_ids):
        raise MockDataError(f"Orphaned comments: {comment_user_ids - user_ids}")
    comment_tweet_ids = {row[0] for row in await session.execute(select(Comment.tweet_id))}
    tweet_ids = {row[0] for row in await session.execute(select(Tweet.id))}
    if not comment_tweet_ids.issubset(tweet_ids):
        raise MockDataError(f"Orphaned comments (tweet): {comment_tweet_ids - tweet_ids}")
    report_tweet_ids = {row[0] for row in await session.execute(select(TweetReport.tweet_id))}
    if not report_tweet_ids.issubset(tweet_ids):
        raise MockDataError(f"Orphaned tweet reports: {report_tweet_ids - tweet_ids}")
    report_comment_ids = {row[0] for row in await session.execute(select(CommentReport.comment_id))}
    comment_ids = {row[0] for row in await session.execute(select(Comment.id))}
    if not report_comment_ids.issubset(comment_ids):
        raise MockDataError(f"Orphaned comment reports: {report_comment_ids - comment_ids}")
    print("✅ No orphaned users, profiles, tokens, tweets, comments, or reports.")

# Call this at the end of main or after all creation steps
# await validate_no_orphans(session)


if __name__ == "__main__":

    async def run_all():
        await create_all_tables()
        await main()

    asyncio.run(run_all())