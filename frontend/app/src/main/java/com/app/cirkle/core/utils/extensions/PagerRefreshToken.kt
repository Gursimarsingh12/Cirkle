package com.app.cirkle.core.utils.extensions

import android.util.Log
import com.app.cirkle.data.remote.interceptor.TokenManager
import retrofit2.HttpException
import java.io.IOException


suspend fun <T : Any> safePagingApiCallWithTokenRefresh(tokenManager: TokenManager,
                                                        callName:String="Unknown",
                                                        apiCall: suspend () -> T,

): Result<T>? {
    return try {
        Result.success(apiCall())
    } catch (e: HttpException) {
        when (e.code()) {
            401, 403 -> {
                // Try refreshing token
                try {
                    tokenManager.refreshToken()
                    Result.success(apiCall())
                }catch(e: HttpException){
                    SessionManager.notifyLogout()
                    Result.failure(e)
                } catch (ex: Exception) {
                    Result.failure(ex)
                }
            }

            404 -> Result.failure(Throwable("Not Found"))
            else -> Result.failure(e)
        }
    } catch (e: IOException) {
        Log.d("Comment","IOException: ${e.message}")
        Result.failure(Throwable("Network error", e))
    } catch (e: Exception) {
        Log.d("Comment","Exception: at call $callName ${e.message} and class is ${e.javaClass.name} also ${e.localizedMessage}")
        Result.failure(e)
    }
}