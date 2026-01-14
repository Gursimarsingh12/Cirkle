package com.app.cirkle.presentation.adapters

import android.graphics.Color
import android.view.Gravity
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.imageview.ShapeableImageView
import com.app.cirkle.core.utils.common.ImageUtils

class ImagePagerAdapter(
    private val imageUrls: List<String>,
    private val imageUtils: ImageUtils
) : RecyclerView.Adapter<ImagePagerAdapter.ImageViewHolder>() {

    inner class ImageViewHolder(frameLayout: LinearLayout, val imageView: ShapeableImageView) : RecyclerView.ViewHolder(frameLayout)


    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ImageViewHolder {
        val context = parent.context
        val imageView =  ShapeableImageView(context).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = Gravity.CENTER_HORIZONTAL
            }
            scaleType = ImageView.ScaleType.FIT_CENTER
        }

        val linearLayout = LinearLayout(context).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
            addView(imageView)
        }

        return ImageViewHolder(linearLayout, imageView)
    }




    override fun getItemCount(): Int = imageUrls.size

    override fun onBindViewHolder(holder: ImageViewHolder, position: Int) {
        imageUtils.loadImageIntoImageView(imageUrls[position],holder.imageView,isMedia = true, dontTransform = true)
    }


}
