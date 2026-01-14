package com.app.cirkle.data.local


import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import androidx.core.content.edit
import com.google.gson.stream.JsonToken
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject

class SecuredSharedPreferences @Inject constructor(
    @ApplicationContext context: Context) {

    companion object {
        private const val PREF_NAME = "secure_prefs"
        private const val KEY_JWT = "key_jwt_token"
        private const val KEY_LOGGED_IN = "key_logged_in"
        private const val REFRESH_TOKEN = "key_refresh_token"
        private const val USER_ID="user_id"
        private const val USER_REGISTERED="user_registered"
        private const val USER_INTEREST_UPDATED="user_interest_updated"
        private const val USER_PROFILE_UPDATED_AT="user_profile_updated_at"
    }

    private val sharedPreferences = EncryptedSharedPreferences.create(
        PREF_NAME,
        MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveRefreshToken(token: String){
        sharedPreferences.edit { putString(REFRESH_TOKEN,token) }
    }

    fun getRefreshToken():String?{
        return sharedPreferences.getString(REFRESH_TOKEN,null)
    }

    fun saveJwtToken(token: String) {
        sharedPreferences.edit { putString(KEY_JWT, token) }
    }

    fun getJwtToken(): String? {
        return sharedPreferences.getString(KEY_JWT, null)
    }

    fun setLoggedIn(userId:String,isLoggedIn: Boolean) {
        sharedPreferences.edit {
            putBoolean(KEY_LOGGED_IN, isLoggedIn)
            putString(USER_ID,userId)
        }
    }

    fun getUserId():String{
        return sharedPreferences.getString(USER_ID,"")?:""
    }

    fun isLoggedIn(): Boolean {
        return sharedPreferences.getBoolean(KEY_LOGGED_IN, false)
    }

    fun clear() {
        sharedPreferences.edit { clear() }
    }

    fun saveUserProfileUpdatedAt(updatedAt: String) {
        sharedPreferences.edit { putString(USER_PROFILE_UPDATED_AT, updatedAt) }
    }

    fun getUserProfileUpdatedAt(): String {
        return sharedPreferences.getString(USER_PROFILE_UPDATED_AT, "") ?: ""
    }
}
