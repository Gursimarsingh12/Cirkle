package com.app.cirkle.presentation.features.shares.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.MessageItemBinding
import com.app.cirkle.domain.model.tweet.SharedTweet

class SharedTweetsAdapter(
    private val imageUtils: ImageUtils,
    private val currentUserId: String = "",
    private val onTweetClick: (Long) -> Unit = {}
) : ListAdapter<SharedTweet, SharedTweetsAdapter.SharedTweetViewHolder>(DIFF_CALLBACK) {

    companion object {
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<SharedTweet>() {
            override fun areItemsTheSame(oldItem: SharedTweet, newItem: SharedTweet): Boolean {
                return oldItem.id == newItem.id
            }

            override fun areContentsTheSame(oldItem: SharedTweet, newItem: SharedTweet): Boolean {
                return oldItem == newItem
            }
        }
    }

    inner class SharedTweetViewHolder(private val binding: MessageItemBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(sharedTweet: SharedTweet) {
            val isCurrentUserSender = sharedTweet.senderId == currentUserId
            val actorName = if (isCurrentUserSender) "You" else sharedTweet.senderName
            val messageText = actorName + if (sharedTweet.message.isNullOrBlank()) {
                " shared a post"
            } else {
                " shared a post"
            }
            binding.participantName.text = messageText
            binding.messageInfo.visibility = View.GONE
            binding.time.text = sharedTweet.formattedTime

            imageUtils.loadImageIntoImageView(
                sharedTweet.senderProfileUrl ?: "",
                binding.profileImage,
                cacheImage = true,
                centerCrop = true
            )

            binding.root.setOnClickListener {
                onTweetClick(sharedTweet.tweetId)
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SharedTweetViewHolder {
        val binding = MessageItemBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return SharedTweetViewHolder(binding)
    }

    override fun onBindViewHolder(holder: SharedTweetViewHolder, position: Int) {
        getItem(position)?.let { holder.bind(it) }
    }
} 