package com.app.cirkle.domain.repository

import androidx.paging.PagingData
import com.app.cirkle.data.model.tweets.request.BookmarkTweetRequest
import com.app.cirkle.data.model.tweets.request.LikeTweetRequest
import com.app.cirkle.data.model.tweets.request.ShareTweetRequest
import com.app.cirkle.data.model.common.ActionResponse
import com.app.cirkle.data.model.tweets.response.PostRequestStatus
import com.app.cirkle.data.model.tweets.response.SharedTweetResponse
import com.app.cirkle.domain.model.tweet.SharedTweet
import com.app.cirkle.data.model.tweets.response.TweetResponse
import com.app.cirkle.domain.model.tweet.PaginatedTweets
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.tweets.request.LikeCommentRequest
import com.app.cirkle.data.model.tweets.request.PostCommentRequest
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.model.tweet.MyComment
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.tweet.TweetComplete
import kotlinx.coroutines.flow.Flow
import java.io.File
import com.app.cirkle.presentation.features.post.EditTweetImage

interface TweetRepository {
    fun postTweet(text: String, files: List<File> =emptyList()): Flow<ResultWrapper<TweetResponse>>

//    fun getRecommended(page: Int): Flow<ResultWrapper<PaginatedTweets>>
    fun getMyTweets(page: Int, pageSize: Int): Flow<ResultWrapper<PaginatedTweets>>
    fun getUserTweets(userId: String, page:Int, pageSize: Int): Flow<ResultWrapper<PaginatedTweets>>
    fun getLiked(page: Int): Flow<ResultWrapper<PaginatedTweets>>
    fun getBookmarkedPaged(page: Int): Flow<ResultWrapper<PaginatedTweets>>
    fun getShared(page: Int): Flow<ResultWrapper<List<SharedTweet>>>
    fun getSentSharesPaged(): Flow<PagingData<SharedTweet>>
    fun getReceivedSharesPaged(): Flow<PagingData<SharedTweet>>
    fun getTweetById(id: Long): Flow<ResultWrapper<TweetComplete>>
    fun likeTweet(body: LikeTweetRequest):Flow<ResultWrapper<PostRequestStatus>>
    fun bookmarkTweet(body: BookmarkTweetRequest):Flow<ResultWrapper<PostRequestStatus>>
    fun shareTweet(body: ShareTweetRequest): Flow<ResultWrapper<ActionResponse>>

    fun postComment(body: PostCommentRequest):Flow<ResultWrapper<Comment>>
    fun deleteComment(commentId:Long): Flow<ResultWrapper<MessageResponse>>
    fun likeComment(body: LikeCommentRequest): Flow<ResultWrapper<MessageResponse>>

    fun getPostCommentPaged(postId:Long): Flow<PagingData<Comment>>
    fun getRecommendedPaged(): Flow<PagingData<Tweet>>
    fun getMyTweetsPaged():Flow<PagingData<Tweet>>
    fun getUserTweetsPaged(userId:String):Flow<PagingData<Tweet>>
    fun getLikedPaged():Flow<PagingData<Tweet>>
    fun getBookmarkedPaged():Flow<PagingData<Tweet>>
    fun getMyCommentsPaged():Flow<PagingData<Comment>>
    fun getCommentRepliesPaged(commentId: Long):Flow<PagingData<Comment>>

    fun refreshTweets():Flow<Boolean>

    fun reportTweet(tweetId:Long,message:String):Flow<ResultWrapper<MessageResponse>>
    fun reportComment(commentId: Long,message: String):Flow<ResultWrapper<MessageResponse>>
    fun deleteTweet(tweetId:Long):Flow<ResultWrapper<MessageResponse>>
    
    fun editTweet(tweetId: Long, text: String, keptExistingUrls: List<String>, newFiles: List<File>): Flow<ResultWrapper<Tweet>>
    fun editComment(commentId: Long, text: String): Flow<ResultWrapper<Comment>>
}
