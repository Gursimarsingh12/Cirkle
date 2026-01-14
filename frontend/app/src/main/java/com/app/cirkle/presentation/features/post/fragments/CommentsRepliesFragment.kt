package com.app.cirkle.presentation.features.post.fragments

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentCommentsRepliesBinding
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.presentation.common.Resource
import com.app.cirkle.presentation.features.post.base.BaseCommentFragment
import com.app.cirkle.presentation.features.post.viewmodels.CommentRepliesFragmentViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class CommentsRepliesFragment : BaseCommentFragment<FragmentCommentsRepliesBinding>() {

    private val navArgs: CommentsRepliesFragmentArgs by navArgs()
    private val viewModel: CommentRepliesFragmentViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentCommentsRepliesBinding {
        return FragmentCommentsRepliesBinding.inflate(inflater)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        val comment=navArgs.comment
        setUpViews(comment)
        setUpStateListeners()
        setUpOnClickListeners(comment)
    }

    private fun setUpViews(comment: Comment){
        viewModel.setCommentId(comment.commentId)
        binding.repliesRecycleView.adapter=commentsAdapter
        binding.repliesRecycleView.layoutManager= LinearLayoutManager(requireContext())
        if(comment.commentCreatorProfileUrl.isNotEmpty()){
            imageUtils.loadImageIntoImageView(comment.commentCreatorProfileUrl,binding.profileImage, centerCrop = true)
        }else{
            binding.profileImage.setImageDrawable(ContextCompat.getDrawable(requireContext(),R.drawable.default_user_img))
        }
        binding.postCreatorName.text=comment.commentCreatorName
        binding.accountVerification.setAccountType(comment.commentCreatorCheckMarkState)
        binding.postCreatedBefore.text=comment.createdAt
        binding.likeButton.setOnStateChangeListener(null)
        binding.likeButton.isSelectedState=comment.isLikedByUser
        binding.likeButton.setOnStateChangeListener {_,like->
            viewModel.likeComment(comment.commentId,like)
            if(like) navArgs.comment.commentLikesCount+=1 else navArgs.comment.commentLikesCount-=1
            binding.likeButton.text=navArgs.comment.commentLikesCount.toString()
        }
        binding.likeButton.text=comment.commentLikesCount.toString()
        binding.commentText.text=comment.text
        imageUtils.loadImageIntoImageView(viewModel.getProfileUrl(),binding.myProfileImage, centerCrop = true)

    }

    private fun setUpOnClickListeners(comment: Comment){
        binding.sendComment.setOnClickListener {
            if(binding.commentEditText.text.toString().isBlank()){
                Toast.makeText(requireContext(),"Reply cannot be empty", Toast.LENGTH_SHORT).show()
            }else{
                viewModel.postReply(binding.commentEditText.text.toString(),comment.tweetId, comment.commentId)
            }
        }
    }

    private fun setUpStateListeners(){
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.replyUiState.collect {
                        when(it){
                            is Resource.Error -> {
                                hideLoading()
                                Toast.makeText(requireContext(),it.message, Toast.LENGTH_LONG).show()
                            }
                            Resource.Idle -> {
                                hideLoading()
                            }
                            Resource.Loading -> {
                                showLoading()
                            }
                            is Resource.Success -> {
                                hideLoading()
                                Toast.makeText(requireContext(),"Reply added successfully", Toast.LENGTH_LONG).show()
                                viewModel.setStateIdle()
                                binding.commentEditText.setText("")
                                commentsAdapter.refresh()
                            }
                        }
                    }
                }
                launch {
                    viewModel.pagedComments.collect {
                        commentsAdapter.submitData(it)
                    }
                }
            }
        }
    }

}