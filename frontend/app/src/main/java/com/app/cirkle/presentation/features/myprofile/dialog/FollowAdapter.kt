package com.app.cirkle.presentation.features.myprofile.dialog

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.paging.PagingDataAdapter
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.imageview.ShapeableImageView
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.FollowerFollowingItemBinding
import com.app.cirkle.domain.model.user.MyFollowFollowing
import android.view.View

// FollowAdapter.kt
class FollowAdapter(private val imageUtils: ImageUtils, private val showUnfollow: Boolean = false, private val onUnfollow: ((MyFollowFollowing) -> Unit)? = null) : PagingDataAdapter<MyFollowFollowing, FollowAdapter.ViewHolder>(DIFF) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = FollowerFollowingItemBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        getItem(position)?.let { holder.bind(it) }
    }

    inner class ViewHolder(private val binding: FollowerFollowingItemBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(user: MyFollowFollowing) {
            binding.postCreatorName.text = user.followerName
            binding.postCreatorId.text = user.followerId
            imageUtils.loadImageIntoImageView(user.followerProfileUrl,binding.profileImage, centerCrop = true)
            binding.removeFollower.visibility = if (showUnfollow) View.VISIBLE else View.GONE
            if (showUnfollow) {
                binding.removeFollower.setOnClickListener { onUnfollow?.invoke(user) }
            } else {
                binding.removeFollower.setOnClickListener(null)
            }
        }
    }

    companion object {
        val DIFF = object : DiffUtil.ItemCallback<MyFollowFollowing>() {
            override fun areItemsTheSame(oldItem: MyFollowFollowing, newItem: MyFollowFollowing): Boolean = oldItem.followerId == newItem.followerId
            override fun areContentsTheSame(oldItem: MyFollowFollowing, newItem: MyFollowFollowing): Boolean = oldItem == newItem
        }
    }
}