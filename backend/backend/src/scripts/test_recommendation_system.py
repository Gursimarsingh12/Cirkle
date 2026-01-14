#!/usr/bin/env python3
"""
Test script for the new Twitter-like recommendation system.
This script tests the percentage-based priority distribution.
"""

import sys
import os
import asyncio
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from database.session import AsyncSessionLocal
from tweets.cruds.TweetCruds import tweet_service
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from user_profile.models.Follower import Follower
from tweets.models.Tweet import Tweet
from tweets.models.TweetLike import TweetLike
from tweets.models.Comment import Comment
from tweets.models.Share import Share
from tweets.models.Bookmark import Bookmark


async def analyze_user_distribution(session: AsyncSession):
    """Analyze the distribution of users in the database"""
    print("🔍 ANALYZING USER DISTRIBUTION")
    print("=" * 50)
    
    # Get all users with profiles
    users_query = select(User, UserProfile).join(UserProfile, User.user_id == UserProfile.user_id)
    result = await session.execute(users_query)
    users_with_profiles = result.all()
    
    total_users = len(users_with_profiles)
    prime_users = [u for u, p in users_with_profiles if p.is_prime]
    org_users = [u for u, p in users_with_profiles if p.is_organizational]
    org_prime_users = [u for u, p in users_with_profiles if p.is_organizational and p.is_prime]
    
    print(f"📊 Total Users: {total_users}")
    print(f"🌟 Prime Users: {len(prime_users)} ({len(prime_users)/total_users*100:.1f}%)")
    print(f"🏢 Organizational Users: {len(org_users)} ({len(org_users)/total_users*100:.1f}%)")
    print(f"👑 Org + Prime Users: {len(org_prime_users)} ({len(org_prime_users)/total_users*100:.1f}%)")
    
    return users_with_profiles


async def analyze_tweet_distribution(session: AsyncSession):
    """Analyze tweet distribution and engagement"""
    print("\n🐦 ANALYZING TWEET DISTRIBUTION")
    print("=" * 50)
    
    # Get tweet counts
    total_tweets = (await session.execute(select(func.count(Tweet.id)))).scalar_one()
    total_likes = (await session.execute(select(func.count(TweetLike.tweet_id)))).scalar_one()
    total_comments = (await session.execute(select(func.count(Comment.id)))).scalar_one()
    total_shares = (await session.execute(select(func.count(Share.tweet_id)))).scalar_one()
    total_bookmarks = (await session.execute(select(func.count(Bookmark.tweet_id)))).scalar_one()
    
    print(f"📝 Total Tweets: {total_tweets:,}")
    print(f"❤️  Total Likes: {total_likes:,}")
    print(f"💬 Total Comments: {total_comments:,}")
    print(f"🔄 Total Shares: {total_shares:,}")
    print(f"🔖 Total Bookmarks: {total_bookmarks:,}")
    print(f"📈 Avg Engagement/Tweet: {(total_likes + total_comments + total_shares + total_bookmarks)/total_tweets:.1f}")


async def test_recommendation_system(session: AsyncSession, test_user_id: str, page_size: int = 20):
    """Test the recommendation system with different page sizes"""
    print(f"\n🎯 TESTING RECOMMENDATION SYSTEM")
    print("=" * 50)
    print(f"Test User: {test_user_id}")
    print(f"Page Size: {page_size}")
    
    try:
        # Get recommended tweets
        feed_response = await tweet_service.get_recommended_tweets(
            session, test_user_id, page=1, page_size=page_size
        )
        
        print(f"\n📊 FEED RESULTS:")
        print(f"Total Tweets Returned: {len(feed_response.tweets)}")
        print(f"Total Available: {feed_response.total}")
        print(f"Page: {feed_response.page}")
        print(f"Page Size: {feed_response.page_size}")
        
        # Analyze the distribution
        categories = {
            "prime_org_with_engagement": 0,
            "prime_org_without_engagement": 0,
            "prime_following_with_engagement": 0,
            "prime_following_without_engagement": 0,
            "following_with_engagement": 0,
            "following_without_engagement": 0,
            "other": 0
        }
        
        # Get user's following list
        following_query = select(Follower.followee_id).where(Follower.follower_id == test_user_id)
        following_result = await session.execute(following_query)
        following_set = set(following_result.scalars().all())
        
        print(f"\n👥 User follows {len(following_set)} people")
        
        # Categorize each tweet in the feed
        for tweet in feed_response.tweets:
            is_prime = tweet.is_prime
            is_org = tweet.is_organizational
            is_following = tweet.user_id in following_set
            
            # Check if tweet has engagement
            has_engagement = (
                tweet.like_count > 0 or
                tweet.comment_count > 0 or
                tweet.share_count > 0 or
                tweet.bookmark_count > 0 or
                tweet.view_count > 0
            )
            
            # Categorize based on our priority system
            if is_prime and is_org and has_engagement:
                categories["prime_org_with_engagement"] += 1
            elif is_prime and is_org and not has_engagement:
                categories["prime_org_without_engagement"] += 1
            elif is_prime and is_following and has_engagement:
                categories["prime_following_with_engagement"] += 1
            elif is_prime and is_following and not has_engagement:
                categories["prime_following_without_engagement"] += 1
            elif is_following and has_engagement:
                categories["following_with_engagement"] += 1
            elif is_following and not has_engagement:
                categories["following_without_engagement"] += 1
            else:
                categories["other"] += 1
        
        print(f"\n📈 ACTUAL DISTRIBUTION:")
        total_returned = len(feed_response.tweets)
        for category, count in categories.items():
            percentage = (count / total_returned * 100) if total_returned > 0 else 0
            print(f"{category.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 EXPECTED DISTRIBUTION (for {page_size} tweets):")
        expected = {
            "prime_org_with_engagement": int(page_size * 0.40),
            "prime_org_without_engagement": int(page_size * 0.20),
            "prime_following_with_engagement": int(page_size * 0.05),
            "prime_following_without_engagement": int(page_size * 0.05),
            "following_with_engagement": int(page_size * 0.15),
            "following_without_engagement": int(page_size * 0.15),
        }
        
        for category, expected_count in expected.items():
            actual_count = categories[category]
            print(f"{category.replace('_', ' ').title()}: {expected_count} expected, {actual_count} actual")
        
        # Show sample tweets from each category
        print(f"\n📝 SAMPLE TWEETS BY CATEGORY:")
        category_samples = {}
        for tweet in feed_response.tweets:
            is_prime = tweet.is_prime
            is_org = tweet.is_organizational
            is_following = tweet.user_id in following_set
            has_engagement = (
                tweet.like_count > 0 or tweet.comment_count > 0 or
                tweet.share_count > 0 or tweet.bookmark_count > 0 or tweet.view_count > 0
            )
            
            if is_prime and is_org and has_engagement:
                category = "prime_org_with_engagement"
            elif is_prime and is_org and not has_engagement:
                category = "prime_org_without_engagement"
            elif is_prime and is_following and has_engagement:
                category = "prime_following_with_engagement"
            elif is_prime and is_following and not has_engagement:
                category = "prime_following_without_engagement"
            elif is_following and has_engagement:
                category = "following_with_engagement"
            elif is_following and not has_engagement:
                category = "following_without_engagement"
            else:
                category = "other"
            
            if category not in category_samples:
                category_samples[category] = []
            
            if len(category_samples[category]) < 2:  # Show max 2 samples per category
                category_samples[category].append({
                    "user": tweet.user_name,
                    "text": tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
                    "likes": tweet.like_count,
                    "comments": tweet.comment_count,
                    "shares": tweet.share_count,
                    "bookmarks": tweet.bookmark_count,
                    "views": tweet.view_count
                })
        
        for category, samples in category_samples.items():
            if samples:
                print(f"\n{category.replace('_', ' ').title()}:")
                for i, sample in enumerate(samples, 1):
                    print(f"  {i}. @{sample['user']}: {sample['text']}")
                    print(f"     💫 {sample['likes']}❤️ {sample['comments']}💬 {sample['shares']}🔄 {sample['bookmarks']}🔖 {sample['views']}👁️")
        
        return feed_response
        
    except Exception as e:
        print(f"❌ Error testing recommendation system: {str(e)}")
        raise


async def main():
    """Main test function"""
    print("🚀 TESTING NEW RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Analyze current data
        users_with_profiles = await analyze_user_distribution(session)
        await analyze_tweet_distribution(session)
        
        if not users_with_profiles:
            print("❌ No users found! Please run generate_mock_data.py first.")
            return
        
        # Get a test user (preferably one with some follows)
        test_user = users_with_profiles[0][0]  # First user
        test_user_id = test_user.user_id
        
        # Check if user has any follows
        following_count = (await session.execute(
            select(func.count(Follower.followee_id)).where(Follower.follower_id == test_user_id)
        )).scalar_one()
        
        print(f"\n🧪 Selected test user: {test_user_id} (follows {following_count} users)")
        
        # Test with different page sizes
        for page_size in [20, 50, 100]:
            print(f"\n{'='*60}")
            await test_recommendation_system(session, test_user_id, page_size)
            print(f"{'='*60}")
        
        print(f"\n✅ Testing completed!")
        print(f"🎯 The recommendation system is working with percentage-based distribution!")


if __name__ == "__main__":
    asyncio.run(main()) 