package com.app.cirkle.presentation.features.post

import android.graphics.BitmapFactory
import android.net.Uri
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.ImageView
import com.google.android.material.imageview.ShapeableImageView
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils

class EditTweetImageAdapter(
    private val images: MutableList<EditTweetImage>,
    private val onRemove: (Int) -> Unit,
    private val imageUtils: ImageUtils
) : RecyclerView.Adapter<EditTweetImageAdapter.ImageViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ImageViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_edit_tweet_image, parent, false)
        return ImageViewHolder(view)
    }

    override fun onBindViewHolder(holder: ImageViewHolder, position: Int) {
        val item = images[position]
        when (item) {
            is EditTweetImage.Existing -> {
                // Use ImageUtils for existing images
                imageUtils.loadImageIntoImageView(
                    item.url,
                    holder.shapeableImageView,
                    cacheImage = true,
                    centerCrop = true,
                    isMedia = true
                )
            }
            is EditTweetImage.New -> {
                // For new images, use setImageURI or setImageBitmap
                val file = item.file
                val uri = Uri.fromFile(file)
                holder.shapeableImageView.setImageURI(uri)
                // If setImageURI doesn't work, fallback to setImageBitmap
                if (holder.shapeableImageView.drawable == null) {
                    val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                    holder.shapeableImageView.setImageBitmap(bitmap)
                }
            }
        }
        holder.closeButton.setOnClickListener {
            onRemove(holder.adapterPosition)
        }
    }

    override fun getItemCount(): Int = images.size

    class ImageViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val shapeableImageView: ShapeableImageView = view.findViewById(R.id.imageView)
        val closeButton: ImageButton = view.findViewById(R.id.buttonClose)
    }
} 