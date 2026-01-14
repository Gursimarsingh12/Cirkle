package com.app.cirkle.core.utils.validation

object AuthInputValidator {

    /**
     * Validates the User ID.
     * User ID must be exactly 7 characters long,
     * start with 2 capital letters followed by 5 digits.
     */
    fun isValidUserId(userId: String): Boolean {
        val regex = Regex("^[A-Z]{2}\\d{5}$")
        return regex.matches(userId)
    }

    /**
     * Validates the Password.
     * Password must be at least 8 characters long.
     * Includes uppercase, lowercase, a number, and a special character.
     */
    fun isValidPassword(password: String): Boolean {
        val regex = Regex("^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d)(?=.*[@#\$%^&+=]).{8,}$")
        return regex.matches(password)
    }
}