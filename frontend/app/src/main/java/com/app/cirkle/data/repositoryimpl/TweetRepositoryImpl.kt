package com.app.cirkle.data.repositoryimpl

import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import com.app.cirkle.data.remote.mappers.TweetsMappers.toDomain
import com.app.cirkle.data.model.tweets.request.BookmarkTweetRequest
import com.app.cirkle.data.model.tweets.request.LikeTweetRequest
import com.app.cirkle.data.model.tweets.request.ShareTweetRequest
import com.app.cirkle.data.model.tweets.response.PostRequestStatus
import com.app.cirkle.data.model.tweets.response.TweetResponse
import com.app.cirkle.data.model.tweets.response.SharedTweetResponse
import com.app.cirkle.data.remote.api.TweetsApiService
import com.app.cirkle.domain.model.tweet.PaginatedTweets
import com.app.cirkle.domain.repository.TweetRepository
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.data.model.common.ActionResponse
import com.app.cirkle.data.model.common.MessageResponse
import com.app.cirkle.data.model.tweets.request.CommentReportRequest
import com.app.cirkle.data.model.tweets.request.LikeCommentRequest
import com.app.cirkle.data.model.tweets.request.PostCommentRequest
import com.app.cirkle.data.model.tweets.request.TweetReportRequest
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.TweetsMappers.toComment
import com.app.cirkle.data.remote.mappers.TweetsMappers.toTweetComplete
import com.app.cirkle.data.remote.mappers.TweetsMappers.toSharedTweetList
import com.app.cirkle.data.remote.paging.MyCommentsPagingSource
import com.app.cirkle.data.remote.paging.SharedTweetsPagingSource
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.tweet.TweetComplete
import com.app.cirkle.domain.model.tweet.SharedTweet
import com.app.cirkle.domain.repository.BaseRepository
import com.app.cirkle.data.remote.paging.TweetPagingSource
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.presentation.features.post.EditTweetImage
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.net.URLConnection
import javax.inject.Inject

class TweetRepositoryImpl @Inject constructor(
    private val api: TweetsApiService,
    private val tokenManager: TokenManager,
) : TweetRepository, BaseRepository(tokenManager)
{

    override fun postTweet(
        text: String,
        files: List<File>
    ): Flow<ResultWrapper<TweetResponse>> = flow {
        try {
            val textPart = text.toRequestBody("text/plain".toMediaType())

            val mediaParts = files.map { file ->
                val mediaType = guessMimeType(file) ?: "image/jpeg"
                val requestFile = file.asRequestBody(mediaType.toMediaTypeOrNull())
                MultipartBody.Part.createFormData("media_files", file.name, requestFile)
            }

            val mediaTypeParts = files.map { file ->
                val mediaType = guessMimeType(file) ?: "image/jpeg"
                val requestBody = mediaType.toRequestBody("text/plain".toMediaType())
                MultipartBody.Part.createFormData("media_types", null, requestBody)
            }

            val response = safeApiCallWithTokenRefresh {
                api.postTweet(
                    text = textPart,
                    mediaFiles = mediaParts,
                    mediaTypes = mediaTypeParts
                )
            }
            emit(response)
        } catch (e: Exception) {
            emit(ResultWrapper.GenericError(error=e.localizedMessage ?: "Unable to post tweet"))
        }
    }

    private fun guessMimeType(file: File): String? {
        return URLConnection.guessContentTypeFromName(file.name)
    }

//    override fun getRecommended(page: Int): Flow<ResultWrapper<PaginatedTweets>> =flow {
//        val result=safeApiCallWithTokenRefresh {
//            api.getFeed(page).toDomain()
//        }
//        emit(result)
//    }



    override fun getMyTweets(page: Int, pageSize: Int): Flow<ResultWrapper<PaginatedTweets>> = flow {
        val result = safeApiCallWithTokenRefresh {
            api.getMyTweets(page, pageSize).toDomain()
        }
        emit(result)
    }

    override fun getUserTweets(
        userId:String,
        page: Int,
        pageSize: Int
    ): Flow<ResultWrapper<PaginatedTweets>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.getUserTweets(userId,page,pageSize).toDomain()
        }
        emit(result)
    }

    override fun getLiked(page: Int): Flow<ResultWrapper<PaginatedTweets>> = flow{
        val result=safeApiCallWithTokenRefresh {
            api.getLiked(page).toDomain()
        }
        emit(result)
    }

    override fun getBookmarkedPaged(page: Int): Flow<ResultWrapper<PaginatedTweets>> =flow {
        val result=safeApiCallWithTokenRefresh {
            api.getBookmarked(page).toDomain()
        }
        emit(result)
    }

    override fun getShared(page: Int): Flow<ResultWrapper<List<SharedTweet>>> = flow {
        val result = safeApiCallWithTokenRefresh{
            api.getShared(page).toSharedTweetList()
        }
        emit(result)
    }

    override fun getTweetById(id: Long): Flow<ResultWrapper<TweetComplete>> = flow {
        val result=safeApiCallWithTokenRefresh {
            api.getTweetById(id).toTweetComplete()
        }
        emit(result)
    }

    override fun likeTweet(body: LikeTweetRequest): Flow<ResultWrapper<PostRequestStatus>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.likeTweet(body)
        }
        emit(result)
    }

    override fun bookmarkTweet(body: BookmarkTweetRequest): Flow<ResultWrapper<PostRequestStatus>> =flow {
        val result=safeApiCallWithTokenRefresh {
            api.bookmarkTweet(body)
        }
        emit(result)
    }

    override fun shareTweet(body: ShareTweetRequest): Flow<ResultWrapper<ActionResponse>> = flow {
        val result = safeApiCallWithTokenRefresh {
            api.shareTweet(body)
        }
        emit(result)
    }

    override fun postComment(body: PostCommentRequest): Flow<ResultWrapper<Comment>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.postComment(body).toComment()
        }
        emit(result)
    }


    override fun deleteComment(commentId: Long): Flow<ResultWrapper<MessageResponse>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.deleteComment(commentId)
        }
        emit(result)
    }

    override fun likeComment(body: LikeCommentRequest): Flow<ResultWrapper<MessageResponse>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.likeComment(body)
        }
        emit(result)
    }

    override fun getPostCommentPaged(tweetId:Long): Flow<PagingData<Comment>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { MyCommentsPagingSource(api,tokenManager, MyCommentsPagingSource.RequestType.TWEET_COMMENTS,tweetId)}
        ).flow
    }


    override fun getRecommendedPaged(): Flow<PagingData<Tweet>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { TweetPagingSource(api, TweetPagingSource.TweetFeedType.RECOMMENDED,tokenManager) }
        ).flow
    }

    override fun getMyTweetsPaged(): Flow<PagingData<Tweet>> {
        return Pager(
            config = PagingConfig(pageSize = 10),
            pagingSourceFactory = { TweetPagingSource(api, TweetPagingSource.TweetFeedType.MINE,tokenManager)}
        ).flow
    }

    override fun getUserTweetsPaged(userId: String): Flow<PagingData<Tweet>> {
        return Pager(
            config = PagingConfig(pageSize = 10),
            pagingSourceFactory = { TweetPagingSource(api, TweetPagingSource.TweetFeedType.USER,tokenManager,userId)}
        ).flow
    }

    override fun getLikedPaged(): Flow<PagingData<Tweet>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { TweetPagingSource(api, TweetPagingSource.TweetFeedType.LIKED,tokenManager)}
        ).flow
    }

    override fun getBookmarkedPaged(): Flow<PagingData<Tweet>>{
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { TweetPagingSource(api, TweetPagingSource.TweetFeedType.BOOKMARKED,tokenManager)}
        ).flow
    }

    override fun getMyCommentsPaged(): Flow<PagingData<Comment>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { MyCommentsPagingSource(api,tokenManager, MyCommentsPagingSource.RequestType.MY_COMMENTS)}
        ).flow
    }

    override fun getCommentRepliesPaged(commentId:Long): Flow<PagingData<Comment>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { MyCommentsPagingSource(api,tokenManager, MyCommentsPagingSource.RequestType.COMMENT_REPLIES, commentId = commentId)}
        ).flow
    }

    override fun refreshTweets(): Flow<Boolean> =flow{
       val result= safeApiCallWithTokenRefresh {
           api.refreshTweets()
       }
        when (result) {
            is ResultWrapper.GenericError -> emit(false)
            ResultWrapper.NetworkError -> emit(false)
            is ResultWrapper.Success -> emit(true)
        }
    }

    override fun reportTweet(
        tweetId: Long,
        message: String
    ): Flow<ResultWrapper<MessageResponse>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.reportTweet(TweetReportRequest(tweetId,message))
        }
        emit(result)
    }

    override fun reportComment(
        commentId: Long,
        message: String
    ): Flow<ResultWrapper<MessageResponse>> =flow{
        val result=safeApiCallWithTokenRefresh {
            api.reportComment(CommentReportRequest(commentId,message))
        }
        emit(result)
    }

    override fun deleteTweet(tweetId: Long): Flow<ResultWrapper<MessageResponse>> =flow{
       val result=safeApiCallWithTokenRefresh {
           api.deleteTweet(tweetId)
       }
        emit(result)
    }

    override fun editTweet(
        tweetId: Long,
        text: String,
        keptExistingUrls: List<String>,
        newFiles: List<File>
    ): Flow<ResultWrapper<Tweet>> = flow {
        try {
            val textPart = text.toRequestBody("text/plain".toMediaType())
            val existingMediaPathParts = keptExistingUrls.map { path ->
                MultipartBody.Part.createFormData("existing_media_paths", null, path.toRequestBody("text/plain".toMediaType()))
            }
            val mediaParts = newFiles.map { file ->
                val mediaType = guessMimeType(file) ?: "image/jpeg"
                val requestFile = file.asRequestBody(mediaType.toMediaTypeOrNull())
                MultipartBody.Part.createFormData("media_files", file.name, requestFile)
            }
            val mediaTypeParts = newFiles.map { file ->
                val mediaType = guessMimeType(file) ?: "image/jpeg"
                val requestBody = mediaType.toRequestBody("text/plain".toMediaType())
                MultipartBody.Part.createFormData("media_types", null, requestBody)
            }
            android.util.Log.d("EditTweet", "keptExistingUrls: $keptExistingUrls")
            val result = safeApiCallWithTokenRefresh<Tweet> {
                api.editTweet(
                    tweetId = tweetId,
                    text = textPart,
                    mediaFiles = if (mediaParts.isNotEmpty()) mediaParts else null,
                    mediaTypes = if (mediaTypeParts.isNotEmpty()) mediaTypeParts else null,
                    existingMediaPaths = if (existingMediaPathParts.isNotEmpty()) existingMediaPathParts else null
                ).toDomain()
            }
            emit(result)
        } catch (e: Exception) {
            emit(ResultWrapper.GenericError(error = e.localizedMessage ?: "Unable to edit tweet"))
        }
    }

    override fun editComment(commentId: Long, text: String): Flow<ResultWrapper<Comment>> = flow {
        val result = safeApiCallWithTokenRefresh<Comment> {
            api.editComment(commentId, text).toComment()
       }
        emit(result)
    }

    override fun getSentSharesPaged(): Flow<PagingData<SharedTweet>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { SharedTweetsPagingSource(api, tokenManager, SharedTweetsPagingSource.RequestType.SENT) }
        ).flow
    }

    override fun getReceivedSharesPaged(): Flow<PagingData<SharedTweet>> {
        return Pager(
            config = PagingConfig(pageSize = 20),
            pagingSourceFactory = { SharedTweetsPagingSource(api, tokenManager, SharedTweetsPagingSource.RequestType.RECEIVED) }
        ).flow
    }
}
