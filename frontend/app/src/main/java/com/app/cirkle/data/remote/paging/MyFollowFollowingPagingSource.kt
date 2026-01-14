package com.app.cirkle.data.remote.paging

import androidx.paging.PagingSource
import androidx.paging.PagingState
import com.app.cirkle.core.utils.extensions.safePagingApiCallWithTokenRefresh
import com.app.cirkle.data.model.user.response.FollowersResponse
import com.app.cirkle.data.model.user.response.FollowingResponse
import com.app.cirkle.data.model.user.response.MutualFollowersResponse
import com.app.cirkle.data.remote.api.UserApiService
import com.app.cirkle.data.remote.interceptor.TokenManager
import com.app.cirkle.data.remote.mappers.UserProfileMapper.toDomainModelList
import com.app.cirkle.domain.model.user.MyFollowFollowing

class MyFollowFollowingPagingSource(
    private val apiService: UserApiService,
    private val tokenManager: TokenManager,
    private val pageSize: Int = 20,
    private val type: RequestType
) : PagingSource<Int, MyFollowFollowing>() {

    override fun getRefreshKey(state: PagingState<Int, MyFollowFollowing>): Int? {
        return state.anchorPosition?.let { pos ->
            state.closestPageToPosition(pos)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(pos)?.nextKey?.minus(1)
        }
    }

    override suspend fun load(params: LoadParams<Int>): LoadResult<Int, MyFollowFollowing> {
        val page = params.key ?: 1

        return try {
            val result = safePagingApiCallWithTokenRefresh(tokenManager) {
                when (type) {
                    RequestType.MY_FOLLOWERS -> apiService.getFollowers(page, pageSize)
                    RequestType.MY_FOLLOWING -> apiService.getFollowing(page, pageSize)
                    RequestType.MUTUAL -> apiService.getMutualFollowers(page, pageSize)
                }
            }

            result?.fold(
                onSuccess = { apiResponse ->
                    val list = when (apiResponse) {
                        is FollowersResponse -> apiResponse.toDomainModelList()
                        is FollowingResponse -> apiResponse.toDomainModelList()
                        is MutualFollowersResponse -> apiResponse.toDomainModelList()
                        else -> emptyList()
                    }

                    val nextKey = if (list.isEmpty() || list.size < pageSize) null else page + 1
                    val prevKey = if (page == 1) null else page - 1

                    LoadResult.Page(
                        data = list,
                        prevKey = prevKey,
                        nextKey = nextKey
                    )
                },
                onFailure = { throwable ->
                    LoadResult.Error(throwable)
                }
            ) ?: LoadResult.Error(Throwable("Unknown error"))

        } catch (e: Exception) {
            LoadResult.Error(e)
        }
    }

    enum class RequestType {
        MY_FOLLOWERS, MY_FOLLOWING,MUTUAL
    }
}

