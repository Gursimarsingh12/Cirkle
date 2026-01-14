package com.app.cirkle.presentation.features.activity.comments

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.paging.PagingDataAdapter
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.app.cirkle.databinding.CommentsItemBinding
import com.app.cirkle.domain.model.tweet.Comment

class MyCommentsAdapter(private val onClick:(tweetId:Long)->Unit) : PagingDataAdapter<Comment,MyCommentsAdapter.CommentsViewHolder>(My_COMMENT_DIFF_CALLBACK) {

    companion object{
        private val My_COMMENT_DIFF_CALLBACK = object : DiffUtil.ItemCallback<Comment>() {
            override fun areItemsTheSame(oldItem: Comment, newItem: Comment): Boolean =
                oldItem.commentId == newItem.commentId

            override fun areContentsTheSame(oldItem: Comment, newItem: Comment): Boolean =
                oldItem == newItem
        }
    }

    override fun onCreateViewHolder(
        parent: ViewGroup,
        viewType: Int
    ): CommentsViewHolder {
        val binding=CommentsItemBinding.inflate(LayoutInflater.from(parent.context),parent,false)
        return CommentsViewHolder(binding)
    }

    override fun onBindViewHolder(
        holder: CommentsViewHolder,
        position: Int
    ) {
        val comment=getItem(position)?:return
        holder.bind(comment)
    }


    inner class CommentsViewHolder(val binding: CommentsItemBinding): RecyclerView.ViewHolder(binding.root){
        fun bind(myComment:Comment){
            binding.commentText.text=myComment.text
            binding.postCreatorName.text=myComment.author!!.name
            binding.likesCount.text=myComment.commentLikesCount.toString()
            binding.updatedBefore.text=myComment.createdAt
            binding.postCreatorId.text="@${myComment.author!!.userId}"
            binding.root.setOnClickListener {
                onClick(myComment.tweetId)
            }
        }

    }
}

