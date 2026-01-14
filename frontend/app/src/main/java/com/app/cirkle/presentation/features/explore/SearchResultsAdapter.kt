package com.app.cirkle.presentation.features.explore

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.google.android.material.imageview.ShapeableImageView
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.domain.model.user.User

class SearchResultsAdapter(
    private val imageUtils: ImageUtils,
    private val onUserClick: (User) -> Unit
) : ListAdapter<User, SearchResultsAdapter.UserViewHolder>(UserDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): UserViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_search_user, parent, false)
        return UserViewHolder(view)
    }

    override fun onBindViewHolder(holder: UserViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class UserViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val profileImage: ShapeableImageView = itemView.findViewById(R.id.ivProfileImage)
        private val userName: TextView = itemView.findViewById(R.id.tvUserName)
        private val userId: TextView = itemView.findViewById(R.id.tvUserId)

        fun bind(user: User) {
            userName.text = user.name
            userId.text = user.id
            imageUtils.loadImageIntoImageView(
                url = user.profileUrl,
                centerCrop = true,
                circleCrop = true,
                imageView = profileImage
            )
            itemView.setOnClickListener {
                onUserClick(user)
            }
        }
    }

    private class UserDiffCallback : DiffUtil.ItemCallback<User>() {
        override fun areItemsTheSame(oldItem: User, newItem: User): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: User, newItem: User): Boolean {
            return oldItem == newItem
        }
    }
}