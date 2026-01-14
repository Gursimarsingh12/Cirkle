package com.app.cirkle.presentation.features.shares.adapters

import android.text.Spannable
import android.text.SpannableString
import android.text.style.ForegroundColorSpan
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.paging.PagingDataAdapter
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.databinding.ItemSharePostBinding
import com.app.cirkle.domain.model.tweet.SharedTweet
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.domain.model.tweet.Tweet
import android.view.View
import android.widget.PopupMenu
import androidx.core.content.ContextCompat
import com.app.cirkle.R

class PagingSharedTweetsAdapter(
    private val imageUtils: ImageUtils,
    private val myId: String,
    private val onClick: TweetItemClickListener
) : PagingDataAdapter<SharedTweet, PagingSharedTweetsAdapter.SharedTweetViewHolder>(DIFF_CALLBACK) {

    interface TweetItemClickListener {
        fun onProfileClick(userId: String)
        fun onPostClick(tweetId: Long)
        fun onLikeClick(tweetId: Long, isLiked: Boolean)
        fun onCommentClick(tweetId: Long)
        fun onSaveClick(tweetId: Long, isSaved: Boolean)
        fun onShareClick(tweetId: Long)
        fun onReportClick(tweetId: Long)
        fun onEditClick(tweet: Tweet)
        fun onDeleteClick(tweetId: Long)
        fun onImageClick(urls: List<String>, startPosition: Int, profileUrl: String, userName: String, userId: String, likeCount: Int)
    }

    companion object {
        private val DIFF_CALLBACK = object : DiffUtil.ItemCallback<SharedTweet>() {
            override fun areItemsTheSame(oldItem: SharedTweet, newItem: SharedTweet): Boolean {
                return oldItem.tweetId == newItem.tweetId && oldItem.sharedAt == newItem.sharedAt
            }

            override fun areContentsTheSame(oldItem: SharedTweet, newItem: SharedTweet): Boolean {
                return oldItem == newItem
            }
        }
    }

    inner class SharedTweetViewHolder(private val binding: ItemSharePostBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(sharedTweet: SharedTweet) {
            val tweet = sharedTweet.tweet
      
            val isCurrentUserSender = sharedTweet.senderId == myId
            val headerText: CharSequence = if (isCurrentUserSender) {
                val prefix = "Sent to "
                val receiverName = sharedTweet.recipientName
                val full = prefix + receiverName
                val spannable = SpannableString(full)
                val color = ContextCompat.getColor(binding.root.context, R.color.selected_color)
                spannable.setSpan(ForegroundColorSpan(color), prefix.length, full.length, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                spannable
            } else {
                val senderName = sharedTweet.senderName
                val suffix = " shared a post with you"
                val full = senderName + suffix
                val spannable = SpannableString(full)
                val color = ContextCompat.getColor(binding.root.context, R.color.selected_color)
                spannable.setSpan(ForegroundColorSpan(color), 0, senderName.length, Spannable.SPAN_EXCLUSIVE_EXCLUSIVE)
                spannable
            }

            binding.headerText.text = headerText
            binding.time.text = sharedTweet.formattedTime

            val counterpartId = if (isCurrentUserSender) sharedTweet.recipientId else sharedTweet.senderId

            binding.headerText.setOnClickListener {
                onClick.onProfileClick(counterpartId)
            }

            binding.profilePic.setOnClickListener {
                onClick.onProfileClick(counterpartId)
            }

            imageUtils.loadImageIntoImageView(
                if (isCurrentUserSender) sharedTweet.recipientProfileUrl ?: "" else sharedTweet.senderProfileUrl ?: "",
                binding.profilePic,
                cacheImage = true,
                centerCrop = true
            )

            // --- Common tweet details (reuse code from TweetsAdapter) ---
            bindTweetCommonFields(tweet)

            // Image count instead of thumbnails
            val hasImages = tweet.mediaCount > 0
            binding.imageClickListeners.visibility = if (hasImages) View.VISIBLE else View.GONE
            if (hasImages) {
                binding.imageCountText.text = "${tweet.mediaCount} Image${if (tweet.mediaCount > 1) "s" else ""}"
                val imageUrls = tweet.media.map { it.url }
                binding.imageClickListeners.setOnClickListener {
                    onClick.onImageClick(imageUrls, 0, tweet.userProfileUrl, tweet.userName, tweet.userId, tweet.likesCount)
                }
            }

            // Root click opens post
            binding.root.setOnClickListener { onClick.onPostClick(tweet.id) }

            // Expandable text click acts same as in main tweets list
            binding.postText.setOnClickListener { onClick.onPostClick(tweet.id) }
        }

        private fun bindTweetCommonFields(tweet: Tweet) {
            binding.postText.setText(tweet.text)
            binding.postCreatorName.text = tweet.userName
            binding.postCreatorId.text = "@${tweet.userId}"
            binding.postCreatedBefore.text = if (tweet.isEdited) "${tweet.timeUntilPost}\nedited" else tweet.timeUntilPost

            val accountType = when {
                tweet.isUserPrime && tweet.isUserOrganization -> 3
                tweet.isUserOrganization -> 1
                tweet.isUserPrime -> 0
                else -> 2
            }
            binding.accountVerification.setAccountType(accountType)

            // Profile picture
            imageUtils.loadImageIntoImageView(tweet.userProfileUrl, binding.profileImage, cacheImage = true, centerCrop = true)

            // Profile clicks
            val openProfile: () -> Unit = {
                if (tweet.userId != myId) onClick.onProfileClick(tweet.userId)
            }
            binding.profileInfoContainer.setOnClickListener { openProfile() }
            binding.profileImage.setOnClickListener { openProfile() }

            // Like button
            binding.likeButton.text = tweet.likesCount.toString()
            binding.likeButton.setOnStateChangeListener(null)
            binding.likeButton.isSelectedState = tweet.isLiked
            binding.likeButton.setOnStateChangeListener { _, isSelected ->
                val currentPos = bindingAdapterPosition
                if (currentPos != RecyclerView.NO_POSITION) {
                    onClick.onLikeClick(tweet.id, isSelected)
                    tweet.isLiked = isSelected
                    tweet.likesCount = if (isSelected) tweet.likesCount + 1 else tweet.likesCount - 1
                    binding.likeButton.text = tweet.likesCount.toString()
                }
            }

            // Comments click
            binding.commentsButton.text = tweet.commentCount.toString()
            binding.commentsButton.setOnClickListener {
                onClick.onCommentClick(tweet.id)
            }

            // Save button
            binding.saved.setOnStateChangeListener(null)
            binding.saved.isSavedState = tweet.isBookMarked
            binding.saved.setOnStateChangeListener { _, isSaved ->
                onClick.onSaveClick(tweet.id, isSaved)
                tweet.isBookMarked = isSaved
            }

            // Share button
            binding.shareButton.setOnClickListener { onClick.onShareClick(tweet.id) }

            // More options
            binding.moreOptionsButton.setOnClickListener {
                val popup = PopupMenu(it.context, it)
                if (tweet.userId == myId) {
                    popup.inflate(R.menu.tweets_recycle_view_my_posts)
                } else {
                    popup.inflate(R.menu.tweets_recycle_view_other_posts)
                }
                popup.setOnMenuItemClickListener { menuItem ->
                    when (menuItem.itemId) {
                        R.id.menu_item_other_post_report -> onClick.onReportClick(tweet.id)
                        R.id.menu_item_my_post_edit -> onClick.onEditClick(tweet)
                        R.id.menu_item_my_post_delete -> onClick.onDeleteClick(tweet.id)
                    }
                    true
                }
                popup.show()
            }

            // Filler click (opens post)
            binding.clickAbleFillerView.setOnClickListener { onClick.onPostClick(tweet.id) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SharedTweetViewHolder {
        val binding = ItemSharePostBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return SharedTweetViewHolder(binding)
    }

    override fun onBindViewHolder(holder: SharedTweetViewHolder, position: Int) {
        getItem(position)?.let { holder.bind(it) }
    }
}
