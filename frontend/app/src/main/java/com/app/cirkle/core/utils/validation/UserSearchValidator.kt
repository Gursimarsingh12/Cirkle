package com.app.cirkle.core.utils.validation

object UserSearchValidator {
    
    private const val MIN_USERNAME_LENGTH = 3
    private const val USER_ID_LENGTH = 3
    private val USER_ID_PATTERN = Regex("^[A-Z]{2}\\d{5}$")
    
    fun isValidUserId(input: String): Boolean {
        return input.length == USER_ID_LENGTH && USER_ID_PATTERN.matches(input)
    }
    
    fun isValidUsernameForSearch(input: String): Boolean {
        return input.length >= MIN_USERNAME_LENGTH && !isValidUserId(input)
    }
    
    fun shouldTriggerUsernameSearch(input: String): Boolean {
        return isValidUsernameForSearch(input)
    }
    
    fun shouldTriggerUserIdSearch(input: String): Boolean {
        return isValidUserId(input)
    }
} 