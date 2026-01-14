package com.app.cirkle.core.utils.validation

object TweetInputValidator {

    private const val MAX_TWEET_LENGTH = 500
    private const val MAX_COMMENT_LENGTH = 280

    fun isValidTweetText(text: String): Boolean {
        val trimmedText = text.trim()
        return trimmedText.isNotEmpty() && trimmedText.length <= MAX_TWEET_LENGTH
    }

    fun isValidCommentText(text: String): Boolean {
        val trimmedText = text.trim()
        return trimmedText.isNotEmpty() && trimmedText.length <= MAX_COMMENT_LENGTH
    }

    
    fun getTweetRemainingChars(text: String): Int {
        return MAX_TWEET_LENGTH - text.trim().length
    }

   
    fun getCommentRemainingChars(text: String): Int {
        return MAX_COMMENT_LENGTH - text.trim().length
    }

    
    fun getTweetValidationError(text: String): String? {
        val trimmedText = text.trim()
        return when {
            trimmedText.isEmpty() -> "Tweet text cannot be empty"
            trimmedText.length > MAX_TWEET_LENGTH -> "Tweet text cannot exceed $MAX_TWEET_LENGTH characters"
            else -> null
        }
    }

    fun getCommentValidationError(text: String): String? {
        val trimmedText = text.trim()
        return when {
            trimmedText.isEmpty() -> "Comment text cannot be empty"
            trimmedText.length > MAX_COMMENT_LENGTH -> "Comment text cannot exceed $MAX_COMMENT_LENGTH characters"
            else -> null
        }
    }
} 