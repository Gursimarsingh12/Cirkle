package com.app.cirkle.data.remote.api

import com.app.cirkle.core.utils.constants.CirkleUrlConstants
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
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface AuthApiService {

    @POST(CirkleUrlConstants.LOGIN)
    suspend fun login(@Body body: LoginRequest): AuthResponse

    @POST(CirkleUrlConstants.REGISTER)
    suspend fun register(@Body body: RegisterRequest): AuthResponse

    @POST(CirkleUrlConstants.LOG_OUT)
    suspend fun logout(): BaseMessageResponse

    @POST(CirkleUrlConstants.REFRESH_TOKEN)
    suspend fun refreshToken(@Body request: RefreshRequest): AuthResponse

    @POST(CirkleUrlConstants.FORGOT_PASSWORD)
    suspend fun forgotPassword(@Body request: ForgotPasswordRequest): BaseMessageResponse

    @POST(CirkleUrlConstants.CHANGE_PASSWORD)
    suspend fun changePassword(@Body request: ChangePasswordRequest): AuthResponse

    @POST(CirkleUrlConstants.SET_ONLINE_STATUS)
    suspend fun setOnlineStatus(@Body request: OnlineStatusRequest): BaseMessageResponse

    @GET(CirkleUrlConstants.GET_CURRENT_USER)
    suspend fun getCurrentUser(): UserResponse

    @GET(CirkleUrlConstants.GET_COMMANDS)
    suspend fun getCommands(): List<CommandResponse>

}