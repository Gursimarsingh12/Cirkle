package com.app.cirkle.data.remote.paging

import android.util.Log
import androidx.paging.PagingSource
import androidx.paging.PagingState
import com.app.cirkle.core.utils.extensions.safePagingApiCallWithTokenRefresh
import com.app.cirkle.data.model.tweets.request.FeedQueryParams
import com.app.cirkle.data.remote.api.TweetsApiService
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.TweetsMappers.toDomain
import com.app.cirkle.data.remote.mappers.TweetsMappers.toQueryMap
import com.app.cirkle.domain.model.tweet.Tweet

class TweetPagingSource(
    private val api: TweetsApiService,
    private val type: TweetFeedType,
    private val tokenManager: TokenManager,
    private val userId: String? = null,
) : PagingSource<Int, Tweet>() {
    private var errorAtPage=-1

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, Tweet> {
        val page = params.key ?: 1
        val count = params.loadSize
        Log.d("BackEndPage","page size: $page")

        val result = safePagingApiCallWithTokenRefresh(tokenManager) {
            when (type) {
                TweetFeedType.RECOMMENDED -> {
                    val queryParams = if (errorAtPage < 0) FeedQueryParams(page, count,feedType = FeedQueryParams.FeedType.LATEST.value).toQueryMap() else FeedQueryParams(page - errorAtPage,count, feedType = FeedQueryParams.FeedType.OLDER.value).toQueryMap()
                    api.getFeed(queryParams)
                }
                TweetFeedType.MINE -> api.getMyTweets(page, count)
                TweetFeedType.USER -> api.getUserTweets(userId.orEmpty(), page, count)
                TweetFeedType.LIKED -> api.getLiked(page)
                TweetFeedType.BOOKMARKED -> api.getBookmarked(page)
            }
        }

        return result?.fold(
            onSuccess = { apiResponse ->
                val tweets = apiResponse.tweets.map { it.toDomain() }
                Log.d("BackEndTweets", "Size: ${tweets.size}")
                Log.d("BackEndTweets", "Inside on success. Tweets empty: ${tweets.isEmpty()} | Data: $tweets")

                if (tweets.isEmpty()&&type == TweetFeedType.RECOMMENDED) {
                    errorAtPage=page-1
                    val fallbackResult = safePagingApiCallWithTokenRefresh(tokenManager) {
                        val queryParams = FeedQueryParams(
                            page = 1,
                            pageSize = count,
                            includeRecommendations = false,
                            feedType = FeedQueryParams.FeedType.OLDER.value
                        ).toQueryMap()
                        api.getFeed(queryParams)
                    }

                    return fallbackResult?.fold(
                        onSuccess = { retryResponse ->
                            val fallbackTweets = retryResponse.tweets.map { it.toDomain() }
                            LoadResult.Page(
                                data = fallbackTweets,
                                prevKey = if (page == 1) null else page - 1,
                                nextKey = if (fallbackTweets.isEmpty()) null else page + 1
                            )
                        },
                        onFailure = { LoadResult.Error(it) }
                    ) ?: LoadResult.Error(Throwable("Unknown error on retry"))
                }
                LoadResult.Page(
                    data = tweets,
                    prevKey = if (page == 1) null else page - 1,
                    nextKey = if (tweets.isEmpty()) null else page + 1
                )
            },
            onFailure = { throwable ->
                Log.d("BackEndTweets", "Inside on failure")

                LoadResult.Error(throwable)
            }
        ) ?: LoadResult.Error(Throwable("Unknown error"))
    }



    override fun getRefreshKey(state: PagingState<Int, Tweet>): Int? {
        return state.anchorPosition?.let { pos ->
            state.closestPageToPosition(pos)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(pos)?.nextKey?.minus(1)
        }
    }
    enum class TweetFeedType {
        RECOMMENDED, MINE, USER, LIKED, BOOKMARKED
    }
}