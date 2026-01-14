package com.app.cirkle.presentation.features.post

import java.io.File
 
sealed class EditTweetImage {
    data class Existing(val url: String) : EditTweetImage()
    data class New(val file: File) : EditTweetImage()
} 