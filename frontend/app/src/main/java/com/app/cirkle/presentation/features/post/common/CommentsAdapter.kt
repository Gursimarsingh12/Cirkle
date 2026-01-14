package com.app.cirkle.presentation.features.post.common

import android.util.Log
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.PopupMenu
import androidx.core.view.isVisible
import androidx.paging.PagingDataAdapter
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.PostCommentItemBinding
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.model.tweet.Tweet

class CommentsAdapter(
    private val myUserId: String,
    private val imageUtils: ImageUtils,
    private val clickListener: ClickListener,
    private val showReplies: Boolean=true,
) : PagingDataAdapter<Comment, CommentsAdapter.CommentsViewHolder>(COMMENT_COMPARATOR) {

    interface ClickListener{
        fun onLikeClick(id:Long,isLiked: Boolean)
        fun onRepliesClick(comment: Comment)
        fun onProfileClick(userId:String)
        fun onEditClick(comment: Comment)
        fun onDeleteClick(commentId:Long)
        fun onReportClick(commentId:Long)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CommentsViewHolder {
        return CommentsViewHolder(
            PostCommentItemBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        )
    }

    override fun onBindViewHolder(holder: CommentsViewHolder, position: Int) {
        Log.d("Comment","Binding data : before getting comment")
        val comment = getItem(position)?:return
        Log.d("Comment","Binding data : $comment")
        holder.bind(comment)
    }

    inner class CommentsViewHolder(private val binding: PostCommentItemBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(comment: Comment) {
            imageUtils.loadImageIntoImageView(
                comment.commentCreatorProfileUrl,
                binding.profileImage,
                cacheImage = true,
                centerCrop = true
            )
            binding.postCreatorName.text = comment.commentCreatorName
            binding.postCreatorId.text = "@${comment.commentCreatorId}"
            binding.accountVerification.setAccountType(comment.commentCreatorCheckMarkState)
            val timeUntil = com.app.cirkle.core.utils.converters.TimeUtils.calculateTimeUntil(comment.createdAt)
            binding.postCreatedBefore.text = if (comment.isEdited) {
                "$timeUntil\nedited"
            } else {
                timeUntil
            }
            binding.commentText.setText(comment.text)

            binding.likeButton.setOnStateChangeListener(null)
            binding.likeButton.isSelectedState = comment.isLikedByUser
            binding.likeButton.text = comment.commentLikesCount.toString()
            if(comment.commentCreatorId!=myUserId) {
                binding.linearLayout2.setOnClickListener {
                    clickListener.onProfileClick(comment.commentCreatorId)
                }
            }
            binding.likeButton.setOnStateChangeListener { _, state ->
                clickListener.onLikeClick(comment.commentId,state)
            }
            binding.replyButton.isVisible =showReplies
            if(showReplies) {
                binding.replyButton.setOnClickListener {
                    clickListener.onRepliesClick(comment)
                }
            }
            binding.moreOptionsButton.setOnClickListener {
                Log.d("CommentAdapter","More Options Clicked")
                val popup = PopupMenu(it.context, it)
                if(comment.commentCreatorId!=myUserId){
                    popup.inflate(R.menu.comments_recycle_view_other_comments)
                    Log.d("CommentAdapter","user id is same")
                    popup.setOnMenuItemClickListener { menuItem ->
                        onMenuItemClick(comment, menuItem.itemId)
                        true
                    }
                }else{
                    popup.inflate(R.menu.tweets_recycle_view_my_posts)
                    Log.d("CommentAdapter","user id is different")
                    popup.setOnMenuItemClickListener { menuItem ->
                        onMenuItemClick(comment, menuItem.itemId)
                        true
                    }
                }
                popup.show()
            }
        }
        fun onMenuItemClick(comment:Comment, id:Int){
            when(id){
                R.id.menu_item_other_comment_report->{
                    clickListener.onReportClick(comment.commentId)
                }
                R.id.menu_item_my_post_edit->{
                    clickListener.onEditClick(comment)
                }
                R.id.menu_item_my_post_delete->{
                    clickListener.onDeleteClick(comment.commentId)
                }
            }
        }
    }

    companion object {
        private val COMMENT_COMPARATOR = object : DiffUtil.ItemCallback<Comment>() {
            override fun areItemsTheSame(oldItem: Comment, newItem: Comment): Boolean {
                return oldItem.commentId == newItem.commentId
            }

            override fun areContentsTheSame(oldItem: Comment, newItem: Comment): Boolean {
                return oldItem == newItem
            }
        }
    }
}