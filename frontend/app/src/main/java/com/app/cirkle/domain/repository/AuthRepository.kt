package com.app.cirkle.domain.repository

import com.app.cirkle.data.model.auth.request.ChangePasswordRequest
import com.app.cirkle.data.model.auth.request.ForgotPasswordRequest
import com.app.cirkle.data.model.auth.request.RegisterRequest
import com.app.cirkle.data.model.auth.response.AuthResponse
import com.app.cirkle.data.model.auth.response.BaseMessageResponse
import com.app.cirkle.data.model.auth.response.CommandResponse
import com.app.cirkle.data.model.auth.response.UserResponse
import com.app.cirkle.core.utils.common.ResultWrapper
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
     fun login(userId: String, password: String): Flow<ResultWrapper<AuthResponse>>
     fun register(request: RegisterRequest): Flow<ResultWrapper<AuthResponse>>
     fun logout(): Flow<ResultWrapper<BaseMessageResponse>>
     fun forgotPassword(request: ForgotPasswordRequest): Flow<ResultWrapper<BaseMessageResponse>>
     fun changePassword(request: ChangePasswordRequest): Flow<ResultWrapper<AuthResponse>>
     fun getCurrentUser(): Flow<ResultWrapper<UserResponse>>
     fun setOnlineStatus(isOnline: Boolean): Flow<ResultWrapper<BaseMessageResponse>>
     fun getCommands():Flow<ResultWrapper<List<CommandResponse>>>
}
