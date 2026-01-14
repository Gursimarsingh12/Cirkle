package com.app.cirkle.data.remote.paging

import androidx.paging.PagingSource
import androidx.paging.PagingState
import com.app.cirkle.core.utils.extensions.safePagingApiCallWithTokenRefresh
import com.app.cirkle.data.remote.api.TweetsApiService
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.TweetsMappers.toSharedTweetList
import com.app.cirkle.domain.model.tweet.SharedTweet

class SharedTweetsPagingSource(
    private val apiService: TweetsApiService,
    private val tokenManager: TokenManager,
    private val requestType: RequestType
) : PagingSource<Int, SharedTweet>() {

    override fun getRefreshKey(state: PagingState<Int, SharedTweet>): Int? {
        return state.anchorPosition?.let { pos ->
            state.closestPageToPosition(pos)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(pos)?.nextKey?.minus(1)
        }
    }

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, SharedTweet> {
        val page = params.key ?: 1
        val pageSize = params.loadSize.coerceAtMost(50)

        val result = safePagingApiCallWithTokenRefresh(tokenManager) {
            when (requestType) {
                RequestType.SENT -> apiService.getSentShares(page, pageSize)
                RequestType.RECEIVED -> apiService.getReceivedShares(page, pageSize)
            }
        }

        return result?.fold(
            onSuccess = { response ->
                val shares = response.toSharedTweetList()
                LoadResult.Page(
                    data = shares,
                    prevKey = if (page == 1) null else page - 1,
                    nextKey = if (shares.isEmpty()) null else page + 1
                )
            },
            onFailure = { throwable ->
                LoadResult.Error(throwable)
            }
        ) ?: LoadResult.Error(Throwable("Unknown error"))
    }

    enum class RequestType { SENT, RECEIVED }
} 