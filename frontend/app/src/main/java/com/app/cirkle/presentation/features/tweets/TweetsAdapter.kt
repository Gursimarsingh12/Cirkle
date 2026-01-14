package com.app.cirkle.presentation.features.tweets

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import androidx.recyclerview.widget.RecyclerView.ViewHolder
import com.google.android.material.imageview.ShapeableImageView
import com.app.cirkle.R
import com.app.cirkle.core.components.CheckMark
import com.app.cirkle.core.components.FavoriteTextView
import com.app.cirkle.core.components.SavedImageButton
import com.app.cirkle.databinding.TweetItemDoubleImageBinding
import com.app.cirkle.databinding.TweetItemOnlyTextBinding
import com.app.cirkle.databinding.TweetItemQuadrupleImageBinding
import com.app.cirkle.databinding.TweetItemSingleImageBinding
import com.app.cirkle.databinding.TweetItemTripleImageBinding
import com.app.cirkle.domain.model.tweet.Tweet
import android.util.Log
import android.view.MenuItem
import android.widget.PopupMenu
import androidx.paging.PagingDataAdapter
import com.app.cirkle.core.components.ExpandableTextView
import com.app.cirkle.core.utils.common.ImageUtils
import android.view.animation.AlphaAnimation
import android.view.animation.Animation
import android.view.animation.DecelerateInterpolator
import android.view.animation.TranslateAnimation


class TweetsAdapter(
    private val myId: String,
    private val imageUtils: ImageUtils,
    private val onClick: OnTweetItemClickListener
) : PagingDataAdapter<Tweet, ViewHolder>(TWEET_DIFF_CALLBACK) {


    // Interface for adapter interactions - moved to ViewModel pattern
    interface OnTweetItemClickListener {
        fun onProfileClick(userId: String)
        fun onPostClick(tweetId: Long)
        fun onImageClick(urls: List<String>, currentImage: Int, profileUrl: String, userName: String, userId: String, likeCount: Int)
        fun onLikeClick(tweetId: Long, isLiked: Boolean)
        fun onCommentClick(tweetId: Long)
        fun onSaveClick(tweetId: Long, isSaved: Boolean)
        fun onShareClick(tweetId:Long)
        fun onReportClick(tweetId:Long)
        fun onEditClick(tweet: Tweet)
        fun onDeleteClick(tweetId:Long)
    }


    companion object {
        private const val TYPE_ONLY_TEXT = 0
        private const val TYPE_ONE_IMAGE = 1
        private const val TYPE_TWO_IMAGE = 2
        private const val TYPE_THREE_IMAGE = 3
        private const val TYPE_FOUR_IMAGE = 4
        private val TWEET_DIFF_CALLBACK = object : DiffUtil.ItemCallback<Tweet>() {
            override fun areItemsTheSame(oldItem: Tweet, newItem: Tweet): Boolean =
                oldItem.id == newItem.id

            override fun areContentsTheSame(oldItem: Tweet, newItem: Tweet): Boolean =
                oldItem == newItem
        }
    }

    private var lastPosition = -1


    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return when (viewType) {
            TYPE_ONLY_TEXT -> OnlyTextViewHolder(TweetItemOnlyTextBinding.inflate(inflater, parent, false))
            TYPE_ONE_IMAGE -> OneImageViewHolder(TweetItemSingleImageBinding.inflate(inflater, parent, false))
            TYPE_TWO_IMAGE -> TwoImageViewHolder(TweetItemDoubleImageBinding.inflate(inflater, parent, false))
            TYPE_THREE_IMAGE -> ThreeImageViewHolder(TweetItemTripleImageBinding.inflate(inflater, parent, false))
            TYPE_FOUR_IMAGE -> FourImageViewHolder(TweetItemQuadrupleImageBinding.inflate(inflater, parent, false))
            else -> throw IllegalArgumentException("Unknown viewType $viewType")
        }
    }


    override fun getItemViewType(position: Int): Int {
        val tweet = getItem(position) ?: return TYPE_ONLY_TEXT
        return when (tweet.mediaCount) {
            0 -> TYPE_ONLY_TEXT
            1 -> TYPE_ONE_IMAGE
            2 -> TYPE_TWO_IMAGE
            3 -> TYPE_THREE_IMAGE
            4 -> TYPE_FOUR_IMAGE
            else -> TYPE_ONE_IMAGE
        }
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val tweet = getItem(position) ?: return
        when (holder) {
            is OnlyTextViewHolder -> holder.bind(tweet,position)
            is OneImageViewHolder -> holder.bind(tweet,position)
            is TwoImageViewHolder -> holder.bind(tweet,position)
            is ThreeImageViewHolder -> holder.bind(tweet,position)
            is FourImageViewHolder -> holder.bind(tweet,position)
        }
        setAnimation(holder.itemView, position)
    }

    private fun setAnimation(viewToAnimate: View, position: Int) {
        if (position > lastPosition) {
            val anim = TranslateAnimation(0f, 0f, 60f, 0f)
            anim.duration = 220
            anim.interpolator = DecelerateInterpolator()
            val fade = AlphaAnimation(0f, 1f)
            fade.duration = 220
            viewToAnimate.startAnimation(anim)
            viewToAnimate.startAnimation(fade)
            lastPosition = position
        }
    }

    override fun onViewDetachedFromWindow(holder: ViewHolder) {
        holder.itemView.clearAnimation()
        super.onViewDetachedFromWindow(holder)
    }

    inner class OnlyTextViewHolder(private val binding: TweetItemOnlyTextBinding) :
        BaseTweetViewHolder(binding.root) {
        fun bind(tweet: Tweet,position: Int) {
            bindCommonFields(
                tweet,
                position,
                binding.postText,
                binding.postCreatorName,
                binding.postCreatorId,
                binding.postCreatedBefore,
                binding.accountVerification,
                binding.profileImage,
                binding.likeButton,
                binding.commentsButton,
                binding.saved,
                binding.profileInfoContainer,
                binding.shareButton,
                binding.moreOptionsButton,
                binding.clickAbleFillerView,
            )

        }
    }

    inner class OneImageViewHolder(private val binding: TweetItemSingleImageBinding) :
        BaseTweetViewHolder(binding.root) {
        fun bind(tweet: Tweet,position: Int) {
            bindCommonFields(
                tweet,
                position,
                binding.postText,
                binding.postCreatorName,
                binding.postCreatorId,
                binding.postCreatedBefore,
                binding.accountVerification,
                binding.profileImage,
                binding.likeButton,
                binding.commentsButton,
                binding.saved,
                binding.profileInfoContainer,
                binding.shareButton,
                binding.moreOptionsButton,
                binding.clickAbleFillerView,
            )

            val imageUrls = tweet.media.map { it.url }
            loadImageIntoImageView(binding.imageOne, tweet.media[0].url, isMedia = true)
            binding.imageOne.setOnClickListener {
                onClick.onImageClick(imageUrls, 0, tweet.userProfileUrl, tweet.userName, tweet.userId, tweet.likesCount)
            }
        }
    }

    inner class TwoImageViewHolder(val binding: TweetItemDoubleImageBinding) :
        BaseTweetViewHolder(binding.root) {
        fun bind(tweet: Tweet,position: Int) {
            bindCommonFields(
                tweet,
                position,
                binding.postText,
                binding.postCreatorName,
                binding.postCreatorId,
                binding.postCreatedBefore,
                binding.accountVerification,
                binding.profileImage,
                binding.likeButton,
                binding.commentsButton,
                binding.saved,
                binding.profileInfoContainer,
                binding.shareButton,
                binding.moreOptionsButton,
                binding.clickAbleFillerView,
            )
            val imageUrls = tweet.media.map { it.url }
            binding.imageOne.setOnClickListener{
                onClick.onImageClick(imageUrls,0,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageTwo.setOnClickListener{
                onClick.onImageClick(imageUrls,1,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            loadImageIntoImageView(binding.imageOne, tweet.media[0].url, isMedia = true)
            loadImageIntoImageView(binding.imageTwo, tweet.media[1].url, isMedia = true)
        }
    }

    inner class ThreeImageViewHolder(val binding: TweetItemTripleImageBinding) :
        BaseTweetViewHolder(binding.root) {
        fun bind(tweet: Tweet,position: Int) {
            bindCommonFields(
                tweet,
                position,
                binding.postText,
                binding.postCreatorName,
                binding.postCreatorId,
                binding.postCreatedBefore,
                binding.accountVerification,
                binding.profileImage,
                binding.likeButton,
                binding.commentsButton,
                binding.saved,
                profileContainer = binding.profileInfoContainer,
                binding.shareButton,
                binding.moreOptionsButton,
                binding.clickAbleFillerView,
            )

            val imageUrls = tweet.media.map { it.url }
            binding.imageOne.setOnClickListener{
                onClick.onImageClick(imageUrls,0,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageTwo.setOnClickListener{
                onClick.onImageClick(imageUrls,1,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageThree.setOnClickListener{
                onClick.onImageClick(imageUrls,2,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }

            loadImageIntoImageView(binding.imageOne, tweet.media[0].url, isMedia = true)
            loadImageIntoImageView(binding.imageTwo, tweet.media[1].url, isMedia = true)
            loadImageIntoImageView(binding.imageThree, tweet.media[2].url, isMedia = true)
        }
    }

    inner class FourImageViewHolder(val binding: TweetItemQuadrupleImageBinding) :
        BaseTweetViewHolder(binding.root) {
        fun bind(tweet: Tweet,position: Int) {
            bindCommonFields(
                tweet,
                position,
                binding.postText,
                binding.postCreatorName,
                binding.postCreatorId,
                binding.postCreatedBefore,
                binding.accountVerification,
                binding.profileImage,
                binding.likeButton,
                binding.commentsButton,
                binding.saved,
                binding.profileInfoContainer,
                binding.shareButton,
                binding.moreOptionsButton,
                binding.clickAbleFillerView,
            )

            val imageUrls = tweet.media.map { it.url }
            binding.imageOne.setOnClickListener{
                onClick.onImageClick(imageUrls,0,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageTwo.setOnClickListener{
                onClick.onImageClick(imageUrls,1,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageThree.setOnClickListener{
                onClick.onImageClick(imageUrls,2,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }
            binding.imageFour.setOnClickListener{
                onClick.onImageClick(imageUrls,3,tweet.userProfileUrl,tweet.userName,tweet.userId,tweet.likesCount)
            }

            loadImageIntoImageView(binding.imageOne, tweet.media[0].url, isMedia = true)
            loadImageIntoImageView(binding.imageTwo, tweet.media[1].url, isMedia = true)
            loadImageIntoImageView(binding.imageThree, tweet.media[2].url, isMedia = true)
            loadImageIntoImageView(binding.imageFour, tweet.media[3].url, isMedia = true)
        }

    }

    private fun loadImageIntoImageView(
        imageView: ShapeableImageView,
        url: String,
        centerInside: Boolean = true,
        isMedia: Boolean = false
    ) {
       imageUtils.loadImageIntoImageView(url,imageView, cacheImage = true,centerInside = true, isMedia = isMedia)
    }

    abstract inner class BaseTweetViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {

        protected fun bindCommonFields(
            tweet: Tweet,
            position: Int,
            postText: ExpandableTextView,
            creatorName: TextView,
            creatorId: TextView,
            createdBefore: TextView,
            accountVerificationView: CheckMark,
            profileImage: ShapeableImageView,
            likeButton: FavoriteTextView,
            commentButton: TextView,
            saveButton: SavedImageButton,
            profileContainer: LinearLayout,
            shareButton: ImageButton,
            optionButton:ImageButton,
            fillerView:View,
        ) {
            postText.setText(tweet.text)
            creatorName.text = tweet.userName
            creatorId.text = "@${tweet.userId}"
            createdBefore.text = if (tweet.isEdited) {
                "${tweet.timeUntilPost}\nedited"
            } else {
                tweet.timeUntilPost
            }

            val accountType =
                if (tweet.isUserPrime && tweet.isUserOrganization) 3
                else if (tweet.isUserOrganization) 1
                else if (tweet.isUserPrime) 0
                else 2

            accountVerificationView.setAccountType(accountType)

            likeButton.text = tweet.likesCount.toString()
            likeButton.setOnStateChangeListener(null)
            likeButton.isSelectedState = tweet.isLiked
            commentButton.text = tweet.commentCount.toString()
            saveButton.setOnStateChangeListener(null)
            saveButton.isSavedState = tweet.isBookMarked

            imageUtils.loadImageIntoImageView(tweet.userProfileUrl,profileImage, cacheImage = true, centerCrop = true)

            profileContainer.setOnClickListener {
                if(tweet.userId != myId) {
                    Log.d("BackEnd","${tweet.userId != myId} where tweet.userId:${tweet.userId} and myId:$myId")
                    onClick.onProfileClick(tweet.userId)
                }
            }
            profileImage.setOnClickListener {
                if(tweet.userId != myId) {
                    Log.d("BackEnd","${tweet.userId != myId} where tweet.userId:${tweet.userId} and myId:$myId")
                    onClick.onProfileClick(tweet.userId)
                }
            }
            postText.setOnClickListener {
                onClick.onPostClick(tweet.id)
            }

            fillerView.setOnClickListener {
                onClick.onPostClick(tweet.id)
            }

            likeButton.setOnStateChangeListener { _, isSelected ->
                val position = bindingAdapterPosition
                if (position != RecyclerView.NO_POSITION) {
                    val tweet = getItem(position)?.copy() ?: return@setOnStateChangeListener

                    tweet.isLiked = isSelected
                    tweet.likesCount = if (isSelected) tweet.likesCount + 1 else tweet.likesCount - 1

                    likeButton.text = tweet.likesCount.toString()



                    // Notify your ViewModel or usecase to actually update backend
                    onClick.onLikeClick(tweet.id, isSelected)
                }
            }

            commentButton.setOnClickListener {
                onClick.onCommentClick(tweet.id)
            }
            saveButton.setOnStateChangeListener { _, isSaved ->
                if (adapterPosition != RecyclerView.NO_POSITION) {
                    tweet.isBookMarked = isSaved
                    onClick.onSaveClick(tweet.id,isSaved)
                }
            }

            shareButton.setOnClickListener {
                onClick.onShareClick(tweet.id)
            }

            optionButton.setOnClickListener {
                val popup = PopupMenu(it.context, it)
                if(tweet.userId != myId) {
                    popup.inflate(R.menu.tweets_recycle_view_other_posts)
                    popup.setOnMenuItemClickListener { menuItem ->
                    onMenuItemClick(tweet, menuItem.itemId)
                        true
                    }
                }else{
                    popup.inflate(R.menu.tweets_recycle_view_my_posts)
                    popup.setOnMenuItemClickListener { menuItem ->
                    onMenuItemClick(tweet, menuItem.itemId)
                        true
                    }
                }

                popup.show()

            }
        }
        fun onMenuItemClick(tweet: Tweet, id:Int){
            when(id){
                R.id.menu_item_other_post_report->{
                    onClick.onReportClick(tweet.id)
                }
                R.id.menu_item_my_post_edit->{
                    onClick.onEditClick(tweet)
                }
                R.id.menu_item_my_post_delete->{
                    onClick.onDeleteClick(tweet.id)
                }
            }
        }
    }

}