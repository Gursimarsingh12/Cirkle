package com.app.cirkle.data.repositoryimpl

import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomainModel
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.data.model.user.request.AcceptFollowRequest
import com.app.cirkle.data.model.user.request.AddInterestsRequest
import com.app.cirkle.data.model.user.request.SearchUsersRequest
import com.app.cirkle.data.model.user.request.UpdateProfileRequest
import com.app.cirkle.data.model.user.response.FollowersResponse
import com.app.cirkle.data.model.user.response.FollowingResponse
import com.app.cirkle.data.model.user.response.FollowRequestsResponse
import com.app.cirkle.data.model.user.response.InterestListResponse
import com.app.cirkle.data.model.user.response.MyProfileResponse
import com.app.cirkle.data.remote.api.UserApiService
import com.app.cirkle.domain.model.user.Interest
import com.app.cirkle.domain.model.user.User
import com.app.cirkle.domain.repository.UserRepository
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomain
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toFollowUserModel
import com.app.cirkle.data.remote.mappers.toDomainModelList
import com.app.cirkle.data.remote.paging.MyFollowFollowingPagingSource
import com.app.cirkle.domain.model.user.MyFollowFollowing
import com.app.cirkle.domain.model.user.UserProfile
import com.app.cirkle.domain.repository.BaseRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import javax.inject.Inject
import com.app.cirkle.presentation.features.onboarding.follow.FollowUser

class UserRepositoryImpl @Inject constructor(
    private val api: UserApiService,
    private val tokenManager: TokenManager,
    private val prefs: com.app.cirkle.data.local.SecuredSharedPreferences
) : UserRepository, BaseRepository(tokenManager) {

    override fun getMyProfile(): Flow<ResultWrapper<MyProfileResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getMyProfile() }
        emit(result)
    }

    override fun getUserProfile(userId: String): Flow<ResultWrapper<UserProfile>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getUserProfile(userId).toDomain() }
        emit(result)
    }

    override fun updateProfile(
        request: UpdateProfileRequest,
        profileImage: File?,               // Can be null
        bannerImage: File?                 // Can be null
    ): Flow<ResultWrapper<MyProfileResponse>> = flow {

        val parts = mutableListOf<MultipartBody.Part>()

        // Helper to safely add text fields
        fun addPart(key: String, value: String?) {
            value?.let {
                parts.add(MultipartBody.Part.createFormData(key, it))
            }
        }
        // Convert interest list to comma-separated string
        val interestIdsStr = request.interestIds?.joinToString(",")
        // Add standard fields
        addPart("name", request.name)
        addPart("bio", request.bio)
        addPart("is_private", request.isPrivate?.toString())
        addPart("command_id", request.commandId?.toString())
        addPart("interest_ids", interestIdsStr)
        // Add image files if present (assuming JPEG from camera)
        profileImage?.let { file ->
            val mediaType = "image/jpeg".toMediaType()
            val body = file.asRequestBody(mediaType)
            parts.add(MultipartBody.Part.createFormData("photo_file", file.name, body))
            addPart("photo_content_type", "image/jpeg")
        }
        bannerImage?.let { file ->
            val mediaType = "image/jpeg".toMediaType()
            val body = file.asRequestBody(mediaType)
            parts.add(MultipartBody.Part.createFormData("banner_file", file.name, body))
            addPart("banner_content_type", "image/jpeg")
        }
        // Make network call
        val result = safeApiCallWithTokenRefresh {
            api.updateProfile(parts)
        }

        if (result is com.app.cirkle.core.utils.common.ResultWrapper.Success) {
            // Update local signature timestamp so cached profile images refresh
            prefs.saveUserProfileUpdatedAt(System.currentTimeMillis().toString())
        }
        emit(result)
    }


    override fun getFollowers(): Flow<PagingData<MyFollowFollowing>> = Pager(
        config = PagingConfig(pageSize = 20, enablePlaceholders = false),
        pagingSourceFactory = {
            MyFollowFollowingPagingSource(
                apiService = api,
                tokenManager = tokenManager,
                type = MyFollowFollowingPagingSource.RequestType.MY_FOLLOWERS
            )
        }
    ).flow

    override fun getFollowing(): Flow<PagingData<MyFollowFollowing>> = Pager(
        config = PagingConfig(pageSize = 20, enablePlaceholders = false),
        pagingSourceFactory = {
            MyFollowFollowingPagingSource(
                apiService = api,
                tokenManager = tokenManager,
                type = MyFollowFollowingPagingSource.RequestType.MY_FOLLOWING
            )
        }
    ).flow

    override fun getMutualFollowers(): Flow<PagingData<MyFollowFollowing>> = Pager(
        config = PagingConfig(pageSize = 20, enablePlaceholders = false),
        pagingSourceFactory = {
            MyFollowFollowingPagingSource(
                apiService = api,
                tokenManager = tokenManager,
                type = MyFollowFollowingPagingSource.RequestType.MUTUAL
            )
        }
    ).flow


    override fun getOtherUserFollowers(userId: String, page: Int, pageSize: Int): Flow<ResultWrapper<FollowersResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getOtherUserFollowers(userId, page, pageSize) }
        emit(result)
    }

    override fun getOtherUserFollowing(userId: String, page: Int, pageSize: Int): Flow<ResultWrapper<FollowingResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getOtherUserFollowing(userId, page, pageSize) }
        emit(result)
    }

    override fun getFollowRequests(page: Int, pageSize: Int): Flow<ResultWrapper<FollowRequestsResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getFollowRequests(page, pageSize) }
        emit(result)
    }

    override fun followUser(followeeId: String): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.followUser(followeeId) }
        emit(result)
    }

    override fun respondToFollowRequest(
        followerId: String,
        request: AcceptFollowRequest
    ): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.respondFollowRequest(followerId, request) }
        emit(result)
    }

    override fun unfollowUser(followeeId: String): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.unfollowUser(followeeId) }
        emit(result)
    }

    override fun getInterests(): Flow<ResultWrapper<InterestListResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getInterests() }
        emit(result)
    }

    override fun addInterest(interestId: Int): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.addInterest(interestId) }
        emit(result)
    }

    override fun removeInterest(interestId: Int): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.removeInterest(interestId) }
        emit(result)
    }

    override fun getAllInterests(): Flow<ResultWrapper<List<Interest>>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getAllInterests() }
        when (result) {
            is ResultWrapper.Success -> {
                emit(ResultWrapper.Success(result.value.toDomainModel()))
            }
            is ResultWrapper.GenericError -> emit(result)
            is ResultWrapper.NetworkError -> emit(result)
        }
    }

    override fun addMultipleInterests(request: AddInterestsRequest): Flow<ResultWrapper<MessageResponse>> = flow {
        val result = safeApiCallWithTokenRefresh { api.addMultipleInterests(request) }
        emit(result)
    }

    override fun getTopAccounts(limit: Int): Flow<ResultWrapper<List<FollowUser>>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getTopAccounts(limit) }
        when (result) {
            is ResultWrapper.Success -> {
                emit(ResultWrapper.Success(result.value.toFollowUserModel()))
            }
            is ResultWrapper.GenericError -> emit(result)
            is ResultWrapper.NetworkError -> emit(result)
        }
    }

    override fun searchUsers(searchQuery: String, page: Int): Flow<ResultWrapper<List<User>>> = flow {
        val result = safeApiCallWithTokenRefresh {
            api.searchUsers(SearchUsersRequest(searchQuery, page))
        }
        when (result) {
            is ResultWrapper.Success -> {
                emit(ResultWrapper.Success(result.value.users.toDomainModelList()))
            }
            is ResultWrapper.GenericError -> emit(result)
            is ResultWrapper.NetworkError -> emit(result)
        }
    }

    override fun isFollowingUser(userId: String): Flow<ResultWrapper<Boolean>> = flow {
        val result = safeApiCallWithTokenRefresh { api.getFollowing(1, 20) }
        when (result) {
            is ResultWrapper.Success -> {
                val isFollowing = result.value.following.any { it.follower_id == userId }
                emit(ResultWrapper.Success(isFollowing))
            }
            is ResultWrapper.GenericError -> emit(result)
            is ResultWrapper.NetworkError -> emit(result)
        }
    }

}