package com.app.cirkle.data.remote.api

import com.app.cirkle.core.utils.constants.CirkleUrlConstants.BOOKMARK_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.DELETE_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.EDIT_COMMENT
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.EDIT_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_BOOKMARKED
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_LIKED
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_MY_TWEETS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_SHARED
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_TWEET_BY_ID
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_TWEET_FEED
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_USER_TWEETS
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.LIKE_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.POST_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.REPORT_COMMENT
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.REPORT_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.SHARE_TWEET
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_SENT_SHARES
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.GET_RECEIVED_SHARES
import com.app.cirkle.data.model.common.ActionResponse
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.tweets.request.BookmarkTweetRequest
import com.app.cirkle.data.model.tweets.request.CommentReportRequest
import com.app.cirkle.data.model.tweets.request.LikeCommentRequest
import com.app.cirkle.data.model.tweets.request.LikeTweetRequest
import com.app.cirkle.data.model.tweets.request.PostCommentRequest
import com.app.cirkle.data.model.tweets.request.ShareTweetRequest
import com.app.cirkle.data.model.tweets.request.TweetReportRequest
import com.app.cirkle.data.model.tweets.response.CommentPagedResponse
import com.app.cirkle.data.model.tweets.response.CommentResponse
import com.app.cirkle.data.model.tweets.response.PaginatedTweetResponse
import com.app.cirkle.data.model.tweets.response.PostRequestStatus
import com.app.cirkle.data.model.tweets.response.SharedTweetResponse
import com.app.cirkle.data.model.tweets.response.TweetResponse
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.QueryMap

interface TweetsApiService {

    @Multipart
    @POST(POST_TWEET)
    suspend fun postTweet(
        @Part("text") text: RequestBody,              // Text content of the tweet
        @Part mediaFiles: List<MultipartBody.Part>,  // List of media files (as parts)
        @Part mediaTypes: List<MultipartBody.Part>          // List of media types (as request bodies)
    ): TweetResponse

    @GET(GET_TWEET_FEED)
    suspend fun getTweetFeed(@Query("page") page: Int = 1): PaginatedTweetResponse

    @GET("/tweets/my-comments")
    suspend fun getMyComments(@Query("page") page:Int=1): List<CommentResponse>

    @GET("/tweets/{tweet_id}/comments")
    suspend fun getTweetComments(@Path("tweet_id")id:Long,@Query("page") page: Int): CommentPagedResponse

    @GET("/tweets/comment/{comment_id}/replies")
    suspend fun getCommentReplies(@Path("comment_id") commentId: Long, @Query("page") page:Int):List<CommentResponse>

    @POST("/tweets/comment")
    suspend fun postComment(
        @Body request: PostCommentRequest
    ): CommentResponse

    @POST("/tweets/comment/like")
    suspend fun likeComment(
        @Body request: LikeCommentRequest
    ): MessageResponse

    @DELETE("/tweets/comment/{comment_id}")
    suspend fun deleteComment(
        @Path("comment_id") commentId: Long
    ): MessageResponse

    @GET(GET_MY_TWEETS)
    suspend fun getMyTweets(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): PaginatedTweetResponse

    @GET("/tweets/feed")
    suspend fun getFeed(@QueryMap(encoded = true) params: Map<String, @JvmSuppressWildcards Any?>): PaginatedTweetResponse

    @POST("/tweets/feed/refresh")
    suspend fun refreshTweets(@Query("page_size") pageSize: Int=1,@Query("include_recommendation") includeRecommendation:Boolean=true): PaginatedTweetResponse


    @GET(GET_LIKED)
    suspend fun getLiked(@Query("page") page: Int = 1): PaginatedTweetResponse

    @GET(GET_BOOKMARKED)
    suspend fun getBookmarked(@Query("page") page: Int = 1): PaginatedTweetResponse

    @GET(GET_SHARED)
    suspend fun getShared(
        @Query("page") page: Int = 1
    ): List<SharedTweetResponse>

    @GET(GET_SENT_SHARES)
    suspend fun getSentShares(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): List<SharedTweetResponse>

    @GET(GET_RECEIVED_SHARES)
    suspend fun getReceivedShares(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): List<SharedTweetResponse>

    @GET(GET_TWEET_BY_ID)
    suspend fun getTweetById(@Path("tweet_id") tweetId: Long): TweetResponse

    @POST(SHARE_TWEET)
    suspend fun shareTweet(
        @Body request: ShareTweetRequest
    ): ActionResponse

    @POST(LIKE_TWEET)
    suspend fun likeTweet(
        @Body request: LikeTweetRequest
    ): PostRequestStatus

    @POST(BOOKMARK_TWEET)
    suspend fun bookmarkTweet(
        @Body request: BookmarkTweetRequest
    ): PostRequestStatus

    @GET(GET_USER_TWEETS)
    suspend fun getUserTweets(
        @Path("user_id") userId: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20
    ): PaginatedTweetResponse

    @POST(REPORT_COMMENT)
    suspend fun reportComment(@Body request: CommentReportRequest): MessageResponse

    @POST(REPORT_TWEET)
    suspend fun reportTweet(
        @Body request: TweetReportRequest
    ): MessageResponse

    @DELETE(DELETE_TWEET)
    suspend fun deleteTweet(
        @Path("tweet_id") tweetId:Long
    ): MessageResponse

    @Multipart
    @PATCH(EDIT_TWEET)
    suspend fun editTweet(
        @Path("tweet_id") tweetId: Long,
        @Part("text") text: RequestBody?,
        @Part mediaFiles: List<MultipartBody.Part>?,
        @Part mediaTypes: List<MultipartBody.Part>?,
        @Part existingMediaPaths: List<MultipartBody.Part>?
    ): TweetResponse

    @PATCH(EDIT_COMMENT)
    suspend fun editComment(
        @Path("comment_id") commentId: Long,
        @Body text: String
    ): CommentResponse
}