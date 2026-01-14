package com.app.cirkle.domain.repository

import androidx.paging.PagingData
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.data.model.user.request.AcceptFollowRequest
import com.app.cirkle.data.model.user.request.AddInterestsRequest
import com.app.cirkle.data.model.user.request.UpdateProfileRequest
import com.app.cirkle.data.model.user.response.FollowersResponse
import com.app.cirkle.data.model.user.response.FollowingResponse
import com.app.cirkle.data.model.user.response.FollowRequestsResponse
import com.app.cirkle.data.model.user.response.InterestListResponse
import com.app.cirkle.data.model.user.response.MyProfileResponse
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.model.user.User
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.domain.model.user.MyFollowFollowing
import com.app.cirkle.domain.model.user.UserProfile
import kotlinx.coroutines.flow.Flow
import java.io.File
import com.app.cirkle.presentation.features.onboarding.follow.FollowUser

interface UserRepository {
    fun getMyProfile(): Flow<ResultWrapper<MyProfileResponse>>
    fun getUserProfile(userId: String): Flow<ResultWrapper<UserProfile>>
    fun updateProfile(request: UpdateProfileRequest,profileImage:File?=null,bannerImage:File?=null):Flow<ResultWrapper<MyProfileResponse>>
    fun getFollowers(): Flow<PagingData<MyFollowFollowing>>
    fun getFollowing(): Flow<PagingData<MyFollowFollowing>>
    fun getMutualFollowers(): Flow<PagingData<MyFollowFollowing>>
    fun getOtherUserFollowers(userId: String, page: Int = 1, pageSize: Int = 20): Flow<ResultWrapper<FollowersResponse>>
    fun getOtherUserFollowing(userId: String, page: Int = 1, pageSize: Int = 20): Flow<ResultWrapper<FollowingResponse>>
    fun getFollowRequests(page: Int, pageSize: Int): Flow<ResultWrapper<FollowRequestsResponse>>
    fun followUser(followeeId: String): Flow<ResultWrapper<BaseMessageResponse>>
    fun respondToFollowRequest(followerId: String, request: AcceptFollowRequest): Flow<ResultWrapper<BaseMessageResponse>>
    fun unfollowUser(followeeId: String): Flow<ResultWrapper<BaseMessageResponse>>
    fun getInterests(): Flow<ResultWrapper<InterestListResponse>>
    fun addInterest(interestId: Int): Flow<ResultWrapper<BaseMessageResponse>>
    fun getAllInterests(): Flow<ResultWrapper<List<Interest>>>
    fun removeInterest(interestId: Int): Flow<ResultWrapper<BaseMessageResponse>>
    fun addMultipleInterests(request: AddInterestsRequest):Flow<ResultWrapper<MessageResponse>>
    fun getTopAccounts(limit:Int=10):Flow<ResultWrapper<List<FollowUser>>>
    fun searchUsers(searchQuery: String, page: Int = 1): Flow<ResultWrapper<List<User>>>
    fun isFollowingUser(userId: String): Flow<ResultWrapper<Boolean>>
}