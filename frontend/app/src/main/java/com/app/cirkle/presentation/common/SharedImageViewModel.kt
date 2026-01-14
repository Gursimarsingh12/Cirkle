package com.app.cirkle.presentation.common

import android.graphics.Bitmap
import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.app.cirkle.domain.model.tweet.Tweet
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File
import javax.inject.Inject

@HiltViewModel
class SharedImageViewModel @Inject constructor(): ViewModel() {
    private val _capturedImage = MutableLiveData<Bitmap>()
    val capturedImage: LiveData<Bitmap> = _capturedImage

    var text=""

    private val _pendingEditTweet = MutableStateFlow<Tweet?>(null)
    val pendingEditTweet: StateFlow<Tweet?> = _pendingEditTweet.asStateFlow()

    private val _pendingEditCallback = MutableStateFlow<((Tweet) -> Unit)?>(null)

    fun setImage(bitmap: Bitmap) {
        _capturedImage.value = bitmap
    }

    fun setPendingEditTweet(tweet: Tweet, callback: (Tweet) -> Unit) {
        _pendingEditTweet.value = tweet
        _pendingEditCallback.value = callback
    }

    fun getPendingEditCallback(): ((Tweet) -> Unit)? {
        return _pendingEditCallback.value
    }

    fun clearPendingEditTweet() {
        _pendingEditTweet.value = null
        _pendingEditCallback.value = null
    }

    private val _createFragmentImageFiles = MutableStateFlow<MutableList<File>>(mutableListOf<File>())  // Correct initialization
    val createFragmentImageFiles: StateFlow<MutableList<File>> = _createFragmentImageFiles.asStateFlow()


    fun addImage(file: File) {
        Log.d("Files", "Adding file: ${file.absolutePath}")
        Log.d("Files", "Current List before addition: ${_createFragmentImageFiles.value}")

        val updatedList = _createFragmentImageFiles.value.toMutableList()  // Create a mutable copy of the current list
        updatedList.add(file)  // Add the new file to the list

        Log.d("Files", "Updated List after addition: $updatedList")

        // Update _imageFiles with the new list
        _createFragmentImageFiles.value = updatedList

        // Log the final value after update
        Log.d("Files", "StateFlow List after update: ${_createFragmentImageFiles.value}")
    }

    fun setCreateFragmentImages(files: List<File>) {
        _createFragmentImageFiles.value = files.toMutableList()
    }

    fun clear() {
        text=""
        _createFragmentImageFiles.value = mutableListOf()
        clearPendingEditTweet()
    }

    fun removeImage(index: Int) {
        val updatedList = _createFragmentImageFiles.value.toMutableList()
        if (index in updatedList.indices) {
            updatedList.removeAt(index)
            _createFragmentImageFiles.value = updatedList
        }
    }
}