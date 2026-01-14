package com.app.cirkle.data.repositoryimpl

import android.util.Log
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.data.model.auth.request.ChangePasswordRequest
import com.app.cirkle.data.model.auth.request.ForgotPasswordRequest
import com.app.cirkle.data.model.auth.request.LoginRequest
import com.app.cirkle.data.model.auth.request.OnlineStatusRequest
import com.app.cirkle.data.model.auth.request.RefreshRequest
import com.app.cirkle.data.model.auth.request.RegisterRequest
import com.app.cirkle.data.model.auth.response.AuthResponse
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.data.model.auth.response.CommandResponse
import com.app.cirkle.data.model.auth.response.UserResponse
import com.app.cirkle.data.remote.api.AuthApiService
import com.app.cirkle.domain.repository.AuthRepository
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.core.utils.extensions.catchExceptions
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject

class AuthRepositoryImpl @Inject constructor(
    private val apiService: AuthApiService,
    private val prefs: SecuredSharedPreferences // if needed
) : AuthRepository {

    override fun login(userId: String, password: String): Flow<ResultWrapper<AuthResponse>> = flow {
        val result = catchExceptions {
            val response = apiService.login(LoginRequest(userId, password))
            prefs.saveJwtToken(response.accessToken)
            prefs.saveRefreshToken(response.refreshToken)
            prefs.setLoggedIn(userId,true)
            response
        }
        emit(result)
    }

    override fun register(request: RegisterRequest): Flow<ResultWrapper<AuthResponse>> = flow {
        Log.d("BackEnd","Function called inside AuthRepository Impl")
        val result = catchExceptions {
            val response = apiService.register(request)
            prefs.saveJwtToken(response.accessToken)
            prefs.saveRefreshToken(response.refreshToken)
            prefs.setLoggedIn(request.userId,true)
            response
        }
        emit(result)
    }

    override fun logout(): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = catchExceptions {
            val response = apiService.logout()
            prefs.clear()
            response
        }
        emit(result)
    }


    override fun forgotPassword(request: ForgotPasswordRequest): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = catchExceptions {
            apiService.forgotPassword(request)
        }
        emit(result)
    }

    override fun changePassword(request: ChangePasswordRequest): Flow<ResultWrapper<AuthResponse>> = flow {
        val result = catchExceptions {
            val response = apiService.changePassword(request)
            prefs.saveJwtToken(response.accessToken)
            response
        }
        emit(result)
    }

    override fun getCurrentUser(): Flow<ResultWrapper<UserResponse>> = flow {
        val result = catchExceptions {
            apiService.getCurrentUser()
        }
        emit(result)
    }

    override fun setOnlineStatus(isOnline: Boolean): Flow<ResultWrapper<BaseMessageResponse>> = flow {
        val result = catchExceptions {
            apiService.setOnlineStatus(OnlineStatusRequest(isOnline))
        }
        emit(result)
    }

    override fun getCommands(): Flow<ResultWrapper<List<CommandResponse>>> =flow {
        val result=catchExceptions {
            apiService.getCommands()
        }
        emit(result)
    }
}