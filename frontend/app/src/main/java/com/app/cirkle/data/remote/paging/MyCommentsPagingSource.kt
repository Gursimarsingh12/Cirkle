package com.app.cirkle.data.remote.paging

import android.util.Log
import androidx.paging.PagingSource
import androidx.paging.PagingState
import com.app.cirkle.core.utils.extensions.safePagingApiCallWithTokenRefresh
import com.app.cirkle.data.model.tweets.response.CommentPagedResponse
import com.app.cirkle.data.model.tweets.response.CommentResponse
import com.app.cirkle.data.model.tweets.response.PaginatedTweetResponse
import com.app.cirkle.data.remote.api.TweetsApiService
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.TweetsMappers.toComment
import com.app.cirkle.data.remote.mappers.TweetsMappers.toDomain
import com.app.cirkle.domain.model.tweet.Comment

class MyCommentsPagingSource(
    val apiService: TweetsApiService,
    val tokenManager: TokenManager,
    val type: RequestType,
    val tweetId:Long?=null,
    val commentId:Long?=null,
): PagingSource<Int, Comment>() {

    override fun getRefreshKey(state: PagingState<Int, Comment>): Int? {
        return state.anchorPosition?.let { pos ->
            state.closestPageToPosition(pos)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(pos)?.nextKey?.minus(1)
        }
    }

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, Comment> {
        val page = params.key ?: 1
        return try {
            val result= safePagingApiCallWithTokenRefresh(tokenManager,"Load My Comments Paging Source") {
                when(type) {
                    RequestType.MY_COMMENTS -> apiService.getMyComments(page)
                    RequestType.TWEET_COMMENTS -> apiService.getTweetComments(tweetId!!,page)
                    RequestType.COMMENT_REPLIES -> apiService.getCommentReplies(commentId!!,page)
                }
            }
            return result?.fold(
                onSuccess = { apiResponse ->
                    val myComment=if(type== RequestType.TWEET_COMMENTS){
                        (apiResponse as CommentPagedResponse).comments.map { it.toComment() }
                    }else{
                        (apiResponse as List<CommentResponse>).map { it.toComment() }
                    }

                    Log.d("Comments","Inside My Comments Paging adapter Data to submit: $myComment")
                    LoadResult.Page(
                        data = myComment,
                        prevKey = if (page == 1) null else page - 1,
                        nextKey = if (myComment.isEmpty()) null else page + 1
                    )
                },
                onFailure = {
                        throwable ->
                    Log.d("Comments","Failed to parse data")
                    LoadResult.Error(throwable)
                }
            )?: LoadResult.Error(Throwable("Unknown error"))
        } catch (e: Exception) {
            LoadResult.Error(e)
        }
    }

    enum class RequestType{
        MY_COMMENTS,TWEET_COMMENTS,COMMENT_REPLIES
    }



}