package com.app.cirkle.core.utils.common

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.drawable.Drawable
import android.util.Log
import androidx.core.content.ContextCompat
import com.bumptech.glide.Glide
import com.bumptech.glide.load.engine.DiskCacheStrategy
import com.bumptech.glide.signature.ObjectKey
import com.google.android.material.imageview.ShapeableImageView
import com.app.cirkle.R
import com.app.cirkle.core.utils.constants.CirkleUrlConstants.BASE_URL
import com.app.cirkle.data.local.SecuredSharedPreferences
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject


class ImageUtils@Inject constructor(
    @ApplicationContext context: Context,
    private val securedSharedPreferences: SecuredSharedPreferences) {

    private val placeHolderDrawable: Drawable=ContextCompat.getDrawable(context, R.drawable.default_user_img)!!
    private val mediaPlaceHolderDrawable: Drawable=ContextCompat.getDrawable(context, R.drawable.loadingthmb)!!
    private val errorDrawable = ContextCompat.getDrawable(context, R.drawable.default_user_img)!!
    private val profileEmptyDrawable= ContextCompat.getDrawable(context,R.drawable.default_user_img)!!


    @SuppressLint("CheckResult")
    fun loadImageIntoImageView(
        url: String?,
        imageView: ShapeableImageView,
        cacheImage: Boolean = false,
        centerInside: Boolean = false,
        centerCrop: Boolean = false,
        dontTransform:Boolean=false,
        circleCrop: Boolean=false,
        isMedia: Boolean = false // <-- add this param
    ) {
        if (url.isNullOrBlank()) {
            imageView.setImageDrawable(if (isMedia) mediaPlaceHolderDrawable else placeHolderDrawable)
            return
        }

        val modifiedUrl = "$BASE_URL/" + url.replaceFirst("user", "image")
        Log.d("ImageUrl",modifiedUrl)

        val request = Glide.with(imageView.context)
            .load(modifiedUrl)
            .placeholder(if (isMedia) mediaPlaceHolderDrawable else placeHolderDrawable)
            .thumbnail(0.1f)
            .dontAnimate()

        val signature = getImageSignature(url)
        if(signature.isNotBlank()) request.signature(ObjectKey(signature))
        
        if (cacheImage) request.diskCacheStrategy(DiskCacheStrategy.DATA)
        if (centerInside) request.centerInside()
        if (centerCrop) {
            request.centerCrop().error(profileEmptyDrawable)
        }else{
            request.error(errorDrawable)
        }
        if(dontTransform) request.dontTransform()
        if(circleCrop) request.circleCrop()

        request.into(imageView)
    }

    private fun getImageSignature(url: String?): String {
        if (url.isNullOrBlank()) return ""
        val currentUserId = securedSharedPreferences.getUserId()
        if (currentUserId.isNotEmpty() && url.contains("user/$currentUserId/photo")) {
            return securedSharedPreferences.getUserProfileUpdatedAt()
        }
        return ""
    }

    fun clearEntireCache(context: Context){
        Glide.get(context).clearMemory()
        Thread(Runnable { Glide.get(context).clearDiskCache() }).start()
    }
}