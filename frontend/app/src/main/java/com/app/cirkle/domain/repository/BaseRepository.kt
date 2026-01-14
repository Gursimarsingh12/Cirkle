package com.app.cirkle.domain.repository

import androidx.paging.PagingSource.LoadResult
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.core.utils.extensions.catchExceptions
import com.app.cirkle.data.remote.interceptor.TokenManager
import retrofit2.HttpException
import java.io.IOException

abstract class BaseRepository(
    private val tokenManager: TokenManager
) {
    protected suspend fun <T> safeApiCallWithTokenRefresh(apiCall: suspend () -> T): ResultWrapper<T> {
        return catchExceptions(
            apiCall = apiCall,
            refreshToken = { tokenManager.refreshToken() }
        )
    }


}