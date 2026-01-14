package com.app.cirkle.data.remote.mappers

import android.util.Log
import com.app.cirkle.data.model.auth.response.AllInterestsResponse
import com.app.cirkle.data.model.user.response.FollowersResponse
import com.app.cirkle.data.model.user.response.FollowingResponse
import com.app.cirkle.data.model.user.response.MutualFollowersResponse
import com.app.cirkle.data.model.user.response.TopAccountsResponse
import com.app.cirkle.data.model.user.response.MyProfileResponse
import com.app.cirkle.data.model.user.response.UserProfileResponse
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.model.user.MyFollowFollowing
import com.app.cirkle.domain.model.user.User
import com.app.cirkle.domain.model.user.MyProfile
import com.app.cirkle.domain.model.user.UserProfile
import com.app.cirkle.presentation.features.onboarding.follow.FollowUser

object UserProfileMapper{
    fun MyProfileResponse.toDomainModel(): MyProfile {
        return MyProfile(
            id = this.user_id,
            name = this.name,
            followerCount = this.followers_count.toString(), // Convert followers_count to String
            followingCount = this.following_count.toString(), // Convert following_count to String
            profileUrl = this.photo ?: "", // Provide a default if photo_url is null
            checkMarkState = when {
                is_prime&&is_organizational->3
                is_prime -> 0 // Example mapping for "prime" state
                is_organizational -> 1 // Example mapping for "organizational" state
                else -> 2 // Default state
            },
            bio = this.bio ?: "", // Provide a default for nullable bio
            bannerUrl = this.banner ?: "", // Provide a default for nullable banner_url
            interests = this.interests, // Pass interests directly,
            updatedAt=updated_at
        )
    }

    fun TopAccountsResponse.toFollowUserModel():List<FollowUser>{
        return accounts.map {
                account->
            FollowUser(
                id =account.userId,
                name = account.name,
                followerCount = account.followersCount.toString(),
                profileUrl = account.photoUrl?:"",
                checkMarkState =when {
                    account.isPrime && account.isOrganizational -> 3
                    account.isPrime -> 2
                    account.isOrganizational-> 1
                    else -> 0
                },
                isFollowing = false )
        }
    }
    fun AllInterestsResponse.toDomainModel(): List<Interest>{
        return interests.map{ Interest(it.id,it.name,false) }
    }

    fun TopAccountsResponse.toDomainModel(): List<User> {
        return accounts.map { account ->
            User(
                id = account.userId,
                name = account.name,
                followerCount = account.followersCount.toString(),
                profileUrl = account.photoUrl?:"",
                checkMarkState = when {
                    account.isPrime && account.isOrganizational -> 3
                    account.isPrime -> 2
                    account.isOrganizational-> 1
                    else -> 0
                }
            )
        }
    }

    fun FollowingResponse.toDomainModelList(): List<MyFollowFollowing> = following.map {
        accounts ->
        MyFollowFollowing(
            followerName = accounts.name,
            isPrime = accounts.is_prime,
            timestamp = accounts.created_at,
            followerProfileUrl = accounts.photo ?: "",
            isOrganizational = accounts.is_organizational,
            followerId = accounts.follower_id
        )
    }

    fun FollowersResponse.toDomainModelList(): List<MyFollowFollowing> = followers.map {
            accounts ->
        MyFollowFollowing(
            followerName = accounts.name,
            isPrime = accounts.is_prime,
            timestamp = accounts.created_at,
            followerProfileUrl = accounts.photo ?: "",
            isOrganizational = accounts.is_organizational,
            followerId = accounts.follower_id
        )
    }

    fun MutualFollowersResponse.toDomainModelList(): List<MyFollowFollowing> = followers.map {
            accounts ->
        MyFollowFollowing(
            followerName = accounts.name,
            isPrime = accounts.is_prime,
            timestamp = accounts.created_at,
            followerProfileUrl = accounts.photo ?: "",
            isOrganizational = accounts.is_organizational,
            followerId = accounts.follower_id
        )
    }



    fun UserProfileResponse.toDomain(): UserProfile {
        val checkMark = when {
            isPrime && isOrganizational -> 3
            isPrime -> 2
            isOrganizational -> 1
            else -> 0
        }
        
        // Use follow_status from API response, fallback to message-based determination
        Log.d("UserProfileMapper", "API Response - follow_status: '$followStatus', message: '$message', isPrivate: $isPrivate, isOrganizational: $isOrganizational")
        
        val actualFollowStatus = when {
            !followStatus.isNullOrBlank() -> {
                Log.d("UserProfileMapper", "Using follow_status from API: $followStatus")
                when(followStatus.lowercase()) {
                    "following" -> "following"
                    "requested", "pending" -> "pending"
                    "not_following", "none" -> "not_following"
                    else -> followStatus
                }
            }
            message.contains("You follow this account", ignoreCase = true) -> {
                Log.d("UserProfileMapper", "Message indicates following")
                "following"
            }
            message.contains("Follow request sent", ignoreCase = true) || 
            message.contains("request sent", ignoreCase = true) -> {
                Log.d("UserProfileMapper", "Message indicates pending request")
                "pending"
            }
            message.contains("You can follow this account", ignoreCase = true) -> {
                Log.d("UserProfileMapper", "Message indicates not following")
                "not_following"
            }
            else -> {
                Log.d("UserProfileMapper", "Default to not_following for message: '$message'")
                "not_following"
            }
        }
        Log.d("UserProfileMapper", "Final follow status: $actualFollowStatus")

        return UserProfile(
            id = id,
            name = name,
            followerCount = followerCount.toString(),
            followingCount = followingCount.toString(),
            profileUrl = profileUrl ?: "",
            checkMarkState = checkMark,
            bio = bio?:"Hey I am on Cirkle!",
            bannerUrl = bannerUrl?:"",
            interests = interests,
            isFollowing = actualFollowStatus == "following",
            followStatus = actualFollowStatus,
            isPrivate = isPrivate,
            isOrganizational = isOrganizational,
            canViewContent = canViewContent,
            updatedAt = updatedAt
        )
    }

}

