package com.app.cirkle.presentation.features.notification

import android.annotation.SuppressLint
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.app.cirkle.R
import com.app.cirkle.databinding.ItemFollowRequestBinding
import com.app.cirkle.domain.model.notification.FollowRequest

class FollowRequestsAdapter(
    private val onRequestAction: (FollowRequest, Boolean) -> Unit
) : RecyclerView.Adapter<FollowRequestsAdapter.FollowRequestViewHolder>() {

    private val followRequests: MutableList<FollowRequest> = mutableListOf()

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): FollowRequestViewHolder {
        val binding = ItemFollowRequestBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return FollowRequestViewHolder(binding)
    }

    override fun onBindViewHolder(holder: FollowRequestViewHolder, position: Int) {
        holder.bind(followRequests[position])
    }

    override fun getItemCount(): Int = followRequests.size

    @SuppressLint("NotifyDataSetChanged")
    fun updateRequests(newRequests: List<FollowRequest>) {
        followRequests.clear()
        followRequests.addAll(newRequests)
        notifyDataSetChanged()
    }

    inner class FollowRequestViewHolder(
        private val binding: ItemFollowRequestBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(followRequest: FollowRequest) {
            binding.apply {
                followerName.text = followRequest.followerName
                followerId.text = "@${followRequest.followerId}"
                timestamp.text = followRequest.timestamp

                // Load profile image
                Glide.with(itemView.context)
                    .load(followRequest.followerProfileUrl)
                    .placeholder(R.drawable.default_user_img)
                    .error(R.drawable.default_user_img)
                    .circleCrop()
                    .into(profileImage)

                // Set up action buttons
                btnAccept.setOnClickListener {
                    onRequestAction(followRequest, true)
                }

                btnDecline.setOnClickListener {
                    onRequestAction(followRequest, false)
                }
            }
        }
    }
} 