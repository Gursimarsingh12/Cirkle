package com.app.cirkle.presentation.features.shares.adapters

import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.paging.PagingDataAdapter
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.ItemFollowingUserToShareBinding
import com.app.cirkle.domain.model.user.MyFollowFollowing

class MyFollowingAdapter(
    private val imageUtils: ImageUtils,
    private val onSelectionChange: (selectedUsers: Set<String>) -> Unit = {}
) : PagingDataAdapter<MyFollowFollowing, MyFollowingAdapter.FollowingViewHolder>(DIFF_CALLBACK) {

    private val selectedUsers = mutableSetOf<String>()

    companion object {
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<MyFollowFollowing>() {
            override fun areItemsTheSame(oldItem: MyFollowFollowing, newItem: MyFollowFollowing): Boolean {
                return oldItem.followerId == newItem.followerId
            }

            override fun areContentsTheSame(oldItem: MyFollowFollowing, newItem: MyFollowFollowing): Boolean {
                return oldItem == newItem
            }
        }
    }

    inner class FollowingViewHolder(private val binding: ItemFollowingUserToShareBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(user: MyFollowFollowing) {
            Log.d("MyFollowingAdapter", "Binding user: ${user.followerName}")

            binding.tvName.text = user.followerName
            binding.tvId.text = "@${user.followerId}"

            val photoUrl = user.followerProfileUrl
            if (photoUrl.isNullOrBlank()) {
                binding.ivProfile.setImageResource(R.drawable.default_user_img)
            } else {
                imageUtils.loadImageIntoImageView(
                    imageView = binding.ivProfile,
                    cacheImage = true,
                    centerCrop = true,
                    url = photoUrl
                )
            }

            if (user.isPrime && user.isOrganizational) {
                binding.tvPrimeOrg.visibility = View.VISIBLE
                binding.tvPrimeOrg.setImageResource(R.drawable.prime_public_drawable)
            } else if (user.isPrime) {
                binding.tvPrimeOrg.visibility = View.VISIBLE
                binding.tvPrimeOrg.setImageResource(R.drawable.prime_drawable)
            } else {
                binding.tvPrimeOrg.visibility = View.GONE
            }

            binding.checkbox.isChecked = selectedUsers.contains(user.followerId)

            binding.checkbox.setOnCheckedChangeListener { _, isChecked ->
                if (isChecked) {
                    if (selectedUsers.size < 5) {
                        selectedUsers.add(user.followerId)
                    } else {
                        binding.checkbox.isChecked = false
                        return@setOnCheckedChangeListener
                    }
                } else {
                    selectedUsers.remove(user.followerId)
                }
                onSelectionChange(selectedUsers.toSet())
            }

            binding.userProfile.setOnClickListener {
                binding.checkbox.isChecked = !binding.checkbox.isChecked
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FollowingViewHolder {
        val binding = ItemFollowingUserToShareBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return FollowingViewHolder(binding)
    }

    override fun onBindViewHolder(holder: FollowingViewHolder, position: Int) {
        getItem(position)?.let { holder.bind(it) }
    }

    fun getSelectedUsers(): Set<String> = selectedUsers.toSet()

    fun clearSelections() {
        selectedUsers.clear()
        notifyDataSetChanged()
    }
}

