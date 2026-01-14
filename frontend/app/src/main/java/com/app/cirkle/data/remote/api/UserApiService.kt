package com.app.cirkle.data.remote.api

import com.app.cirkle.core.utils.constants.CirkleUrlConstants.ADD_INTEREST
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.ADD_MULTIPLE_INTERESTS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.FOLLOW_USER
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_ALL_INTERESTS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_FOLLOWERS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_FOLLOWING
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_FOLLOW_REQUESTS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_INTERESTS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_MUTUAL_FOLLOWERS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_MY_PROFILE
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_OTHER_USERS_FOLLOWERS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_OTHER_USERS_FOLLOWING
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_TOP_ACCOUNTS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_USER_PROFILE
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.REMOVE_INTEREST
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.RESPOND_FOLLOW_REQUEST
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.SEARCH_USERS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.UNFOLLOW_USER
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.UPDATE_PROFILE
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.auth.response.AllInterestsResponse
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.data.model.user.request.AcceptFollowRequest
import com.app.cirkle.data.model.user.request.AddInterestsRequest
import com.app.cirkle.data.model.user.request.SearchUsersRequest
import com.app.cirkle.data.model.user.response.FollowersResponse
import com.app.cirkle.data.model.user.response.FollowRequestsResponse
import com.app.cirkle.data.model.user.response.FollowingResponse
import com.app.cirkle.data.model.user.response.MutualFollowersResponse
import com.app.cirkle.data.model.user.response.InterestListResponse
import com.app.cirkle.data.model.user.response.SearchUsersResponse
import com.app.cirkle.data.model.user.response.TopAccountsResponse
import com.app.cirkle.data.model.user.response.MyProfileResponse
import com.app.cirkle.data.model.user.response.UserProfileResponse
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

interface UserApiService {

    @GET(GET_MY_PROFILE)
    suspend fun getMyProfile(): MyProfileResponse

    @GET(GET_USER_PROFILE)
    suspend fun getUserProfile(@Path("user_id") userId: String): UserProfileResponse

    @Multipart
    @PUT(UPDATE_PROFILE)
    suspend fun updateProfile(
        @Part parts: List<MultipartBody.Part>
    ): MyProfileResponse

    @GET(GET_FOLLOWERS)
    suspend fun getFollowers(@Query("page") page: Int, @Query("page_size") pageSize: Int): FollowersResponse

    @GET(GET_FOLLOWING)
    suspend fun getFollowing(@Query("page") page: Int, @Query("page_size") pageSize: Int): FollowingResponse

    @GET(GET_FOLLOW_REQUESTS)
    suspend fun getFollowRequests(@Query("page") page: Int, @Query("page_size") pageSize: Int): FollowRequestsResponse

    @POST(FOLLOW_USER)
    suspend fun followUser(@Path("followee_id") followeeId: String): BaseMessageResponse

    @PUT(RESPOND_FOLLOW_REQUEST)
    suspend fun respondFollowRequest(
        @Path("follower_id") followerId: String,
        @Body body: AcceptFollowRequest
    ): BaseMessageResponse

    @DELETE(UNFOLLOW_USER)
    suspend fun unfollowUser(@Path("followee_id") followeeId: String): BaseMessageResponse

    @GET(GET_ALL_INTERESTS)
    suspend fun getAllInterests(): AllInterestsResponse

    @GET(GET_INTERESTS)
    suspend fun getInterests(): InterestListResponse

    @POST(ADD_INTEREST)
    suspend fun addInterest(@Query("interest_id") interestId: Int): BaseMessageResponse

    @DELETE(REMOVE_INTEREST)
    suspend fun removeInterest(@Path("interest_id") interestId: Int): BaseMessageResponse

    @POST(ADD_MULTIPLE_INTERESTS)
    suspend fun addMultipleInterests(@Body request: AddInterestsRequest): MessageResponse

    @GET(GET_TOP_ACCOUNTS)
    suspend fun getTopAccounts(
        @Query("limit") limit: Int = 10
    ): TopAccountsResponse

    @POST(SEARCH_USERS)
    suspend fun searchUsers(@Body request: SearchUsersRequest): SearchUsersResponse

    @GET(GET_OTHER_USERS_FOLLOWERS)
    suspend fun getOtherUserFollowers(
        @Path("target_user_id") targetUserId: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): FollowersResponse

    @GET(GET_OTHER_USERS_FOLLOWING)
    suspend fun getOtherUserFollowing(
        @Path("target_user_id") targetUserId: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): FollowingResponse

    @GET(GET_MUTUAL_FOLLOWERS)
    suspend fun getMutualFollowers(
        @Query("page") page: Int,
        @Query("page_size") pageSize: Int
    ): MutualFollowersResponse
}