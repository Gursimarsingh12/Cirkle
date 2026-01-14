package com.app.cirkle.presentation.features.post.fragments

import android.util.Log
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.PopupMenu
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.setFragmentResultListener
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentPostBinding
import com.app.cirkle.domain.model.tweet.TweetComplete
import com.app.cirkle.presentation.features.post.PostFragmentUiState
import com.app.cirkle.presentation.features.post.base.BaseCommentFragment
import com.app.cirkle.presentation.features.post.viewmodels.PostViewModel
import com.app.cirkle.presentation.features.tweets.TweetsViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.presentation.features.post.dialogs.EditTweetDialog
import kotlinx.coroutines.Job

@AndroidEntryPoint
class PostFragment : BaseCommentFragment<FragmentPostBinding>() {

    private val viewModel: PostViewModel by viewModels()
    private val navArgs: PostFragmentArgs by navArgs()
    private val tweetsViewModel: TweetsViewModel by viewModels()


    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentPostBinding {
        return FragmentPostBinding.inflate(layoutInflater)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        showLoading()
        viewModel.setTweetId(navArgs.postId)
        viewModel.getTweet(navArgs.postId)
        setUpStateListeners()
        setUpClickListeners()
        setUpUi()
        setFragmentResultListener("edit_tweet_camera_request") { _, _ ->
            val args = Bundle().apply {
                putBoolean("is_Circle", false)
                putBoolean("isFromProfile", false)
                putBoolean("isFromEditTweet", true)
            }
            NavUtils.navigateWithSlideAnimAndPopUpTo(
                findNavController(),
                R.id.fragment_camera,
                R.id.fragment_camera,
                true,
                args
            )
        }
        setFragmentResultListener("camera_result") { _, bundle ->
            val filePath = bundle.getString("image_file_path")
            val file = filePath?.let { java.io.File(it) }
            val sharedImageViewModel = androidx.lifecycle.ViewModelProvider(requireActivity()).get(com.app.cirkle.presentation.common.SharedImageViewModel::class.java)
            if (file != null) {
                sharedImageViewModel.addImage(file)
            }
            val pendingTweet = sharedImageViewModel.pendingEditTweet.value
            val pendingCallback = sharedImageViewModel.getPendingEditCallback()
            if (pendingTweet != null && pendingCallback != null) {
                val editDialog = com.app.cirkle.presentation.features.post.dialogs.EditTweetDialog.newInstance(pendingTweet) { updatedTweet ->
                    viewModel.getTweet(updatedTweet.id)
                    Toast.makeText(requireContext(), "Post updated!", Toast.LENGTH_SHORT).show()
                    sharedImageViewModel.clearPendingEditTweet()
                }
                editDialog.show(parentFragmentManager, "EditTweetDialog")
            }
        }
    }


    private fun setUpStateListeners(){

        viewLifecycleOwner.lifecycleScope.launch{
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    var commentsJob: Job? = null
                    viewModel.postUiState.collect { comment ->
                        when(comment){
                            is PostFragmentUiState.Error -> {
                                hideLoading()
                                Toast.makeText(requireContext(),comment.message, Toast.LENGTH_LONG).show()
                                findNavController().navigateUp()
                            }
                            PostFragmentUiState.Idle -> {
                                hideLoading()
                            }
                            PostFragmentUiState.Loading -> {
                                showLoading()
                            }
                            is PostFragmentUiState.Success -> {
                                hideLoading()
                                updateUi(comment.data)
                                commentsJob?.cancel()
                                commentsJob = viewLifecycleOwner.lifecycleScope.launch {
                                    delay(250) // Small delay for smoothness
                                    viewModel.pagedComments.onEach {
                                        Log.d("Comments","Data received inside on each: $it")
                                    }.collect{
                                        Log.d("Comments","Data received: $it")
                                        try {
                                            commentsAdapter.submitData(it)
                                            Log.d("Comments", "Data submitted")
                                        } catch (e: Exception) {
                                            Log.e("Comments", "submitData() failed", e)
                                        }
                                        Log.d("Comments","Data submitted")
                                        delay(300) // Give adapter a chance to load
                                        val snapshot = commentsAdapter.snapshot()
                                        Log.d("Comments", "Snapshot size: ${snapshot.size}")
                                    }
                                }
                            }
                            is PostFragmentUiState.CommentPosted -> {
                                hideLoading()
                                binding.commentEditText.clearFocus()
                                binding.commentEditText.text?.clear()
                                commentsAdapter.refresh()
                                Log.d("BackEndPostComment",comment.comment.toString())
                                Toast.makeText(requireContext(),"Comment added!", Toast.LENGTH_SHORT).show()
                            }
                            is PostFragmentUiState.PostCommentError -> {
                                hideLoading()
                                Toast.makeText(requireContext(),comment.message, Toast.LENGTH_SHORT).show()
                                viewModel.setStateIdle()
                            }
                        }
                    }
                }
                // Remove the always-on comments collection
                // launch {
                //     viewModel.pagedComments.onEach {
                //         Log.d("Comments","Data received inside on each: $it")
                //     }.collect{
                //         Log.d("Comments","Data received: $it")
                //         try {
                //             commentsAdapter.submitData(it)
                //             Log.d("Comments", "Data submitted")
                //         } catch (e: Exception) {
                //             Log.e("Comments", "submitData() failed", e)
                //         }
                //         Log.d("Comments","Data submitted")
                //         delay(300) // Give adapter a chance to load
                //         val snapshot = commentsAdapter.snapshot()
                //         Log.d("Comments", "Snapshot size: ${snapshot.size}")
                //     }
                // }
                launch {
                    commentsAdapter.loadStateFlow.collectLatest {

                    }
                }

            }
        }
    }

    private fun setUpClickListeners(){
        binding.sendComment.setOnClickListener {
            if(binding.commentEditText.text.toString().isNotBlank()){
                viewModel.postComment(text = binding.commentEditText.text.toString(), tweetId = navArgs.postId)
            }else{
                Toast.makeText(requireContext(),"Comment can not be empty", Toast.LENGTH_SHORT).show()
            }
        }
    }

    fun setUpUi(){
        val profileUrl = viewModel.getProfileUrl()
        if (profileUrl.isBlank()) {
            binding.myProfileImage.setImageResource(R.drawable.default_user_img)
        } else {
            imageUtils.loadImageIntoImageView(profileUrl, binding.myProfileImage, cacheImage = true, circleCrop = true, isMedia = true)
        }
        binding.commentsRecyclerView.layoutManager= LinearLayoutManager(requireContext())
        binding.commentsRecyclerView.adapter=commentsAdapter
    }

    private fun updateUi(tweet: TweetComplete) {
        binding.postCreatorName.text=tweet.userName
        binding.postCreatorId.text="@${tweet.userId}"
        binding.postCreatedBefore.text=tweet.timeUntilPost
        binding.postText.text=tweet.text
        binding.likeButton.setOnStateChangeListener(null)
        binding.likeButton.isSelectedState=tweet.isLiked
        binding.likeButton.text=tweet.likesCount.toString()
        val accountType =
            if (tweet.isUserPrime && tweet.isUserOrganization) 3
            else if (tweet.isUserOrganization) 1
            else if (tweet.isUserPrime) 0
            else 2
        binding.accountVerification.setAccountType(accountType)
        binding.saved.setOnStateChangeListener(null)
        binding.saved.isSavedState = tweet.isBookMarked
        binding.commentsButton.text=tweet.commentCount.toString()
        imageUtils.loadImageIntoImageView(tweet.userProfileUrl,binding.profileImage, cacheImage = true, circleCrop = true)
        binding.moreOptionsButton.setOnClickListener {
            val popup = PopupMenu(it.context, it)
            if(viewModel.isUserCreator(tweet.userId)) {
                popup.inflate(R.menu.tweets_recycle_view_my_posts)
                popup.setOnMenuItemClickListener { menuItem ->
                    when(menuItem.itemId) {
                        R.id.menu_item_my_post_edit -> {
                            val editDialog = EditTweetDialog.newInstance(tweetCompleteToTweet(tweet)) { updatedTweet ->
                                viewModel.getTweet(updatedTweet.id)
                                Toast.makeText(requireContext(), "Post updated!", Toast.LENGTH_SHORT).show()
                            }
                            editDialog.show(parentFragmentManager, "EditTweetDialog")
                        }
                        R.id.menu_item_my_post_delete -> {
                            // Instantly navigate to MyProfile
                            val action = AppNavigationDirections.actionToFragmentMyProfile()
                            NavUtils.navigateWithSlideAnimAndPopUpTo(
                                findNavController(),
                                action.actionId,
                                R.id.fragment_my_profile,
                                true,
                                action.arguments
                            )
                            tweetsViewModel.deleteTweet(tweet.id) { deleted ->
                                if (!deleted) {
                                    Toast.makeText(requireContext(), "Unable to delete post", Toast.LENGTH_LONG).show()
                                }
                            }
                        }
                    }
                    true
                }
            } else {
                popup.inflate(R.menu.tweets_recycle_view_other_posts)
                popup.setOnMenuItemClickListener { menuItem ->
                    when(menuItem.itemId) {
                        R.id.menu_item_other_post_report -> {
                            val action = AppNavigationDirections.actionToDialogSubmitAReport(isPost = true, targetId = tweet.id)
                            findNavController().navigate(action)
                        }
                    }
                    true
                }
            }
            popup.show()
        }
        binding.profileImage.setOnClickListener {
            if(!viewModel.isUserCreator(tweet.userId)){
                val action =
                    AppNavigationDirections.actionToFragmentUserProfile(tweet.userId)
                findNavController().navigate(action)
            }
        }
        binding.profileInfoContainer.setOnClickListener {
            if(!viewModel.isUserCreator(tweet.userId)){
                val action =
                    AppNavigationDirections.actionToFragmentUserProfile(tweet.userId)
                findNavController().navigate(action)
            }
        }
        binding.likeButton.setOnStateChangeListener { _, isSelected->
            tweetsViewModel.likeTweet(tweet.id, isSelected)
            if(isSelected) {
                tweet.likesCount++
            }else {
                tweet.likesCount--
            }
        }
        binding.saved.setOnStateChangeListener { _,isSelected->
            tweetsViewModel.bookMarkTweet(tweet.id,isSelected)
        }
        binding.shareButton.setOnClickListener {
            val action= AppNavigationDirections.actionToShareBottomSheetFragment(tweet.id)
            findNavController().navigate(action)
        }
        binding.imageOneOne.visibility = View.GONE
        binding.twoImageContainer.visibility = View.GONE
        binding.threeImageContainer.visibility = View.GONE
        binding.fourImageContainer.visibility = View.GONE
        when(tweet.mediaCount){
            1 -> {
                binding.imageOneOne.visibility = View.VISIBLE
                imageUtils.loadImageIntoImageView(tweet.media[0].url,binding.imageOneOne, cacheImage = true, centerInside = true, isMedia = true)
            }
            2 -> {
                binding.twoImageContainer.visibility = View.VISIBLE
                imageUtils.loadImageIntoImageView(tweet.media[0].url,binding.imageTwoOne, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[1].url,binding.imageTwoTwo, cacheImage = true, centerInside = true, isMedia = true)
            }
            3 -> {
                binding.threeImageContainer.visibility = View.VISIBLE
                imageUtils.loadImageIntoImageView(tweet.media[0].url,binding.imageThreeOne, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[1].url,binding.imageThreeTwo, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[2].url,binding.imageThreeThree, cacheImage = true, centerInside = true, isMedia = true)
            }
            4 -> {
                binding.fourImageContainer.visibility = View.VISIBLE
                imageUtils.loadImageIntoImageView(tweet.media[0].url,binding.imageFourOne, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[1].url,binding.imageFourTwo, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[2].url,binding.imageFourThree, cacheImage = true, centerInside = true, isMedia = true)
                imageUtils.loadImageIntoImageView(tweet.media[2].url,binding.imageFourFour, cacheImage = true, centerInside = true, isMedia = true)
            }
            else->{
                binding.twoImageContainer.visibility= View.GONE
                binding.threeImageContainer.visibility= View.GONE
                binding.fourImageContainer.visibility= View.GONE
                binding.imageOneOne.visibility= View.GONE
            }
        }

        binding.imageClickListeners.setOnClickListener {
            val urls=tweet.media.map { it.url }
            val bundle = bundleOf(
                "image_urls" to urls,
                "start_position" to 0,
                "user_name" to tweet.userName,
                "user_id" to tweet.userId,
                "user_icon_url" to tweet.userProfileUrl,
                "like_count" to tweet.likesCount
            )
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_to_dialog_image_preview, bundle)
        }

    }

    private fun tweetCompleteToTweet(tweet: TweetComplete): com.app.cirkle.domain.model.tweet.Tweet {
        return com.app.cirkle.domain.model.tweet.Tweet(
            id = tweet.id,
            userId = tweet.userId,
            userName = tweet.userName,
            userProfileUrl = tweet.userProfileUrl,
            isUserOrganization = tweet.isUserOrganization,
            isUserPrime = tweet.isUserPrime,
            text = tweet.text,
            mediaCount = tweet.mediaCount,
            media = tweet.media,
            timeUntilPost = tweet.timeUntilPost,
            likesCount = tweet.likesCount,
            commentCount = tweet.commentCount,
            isLiked = tweet.isLiked,
            isBookMarked = tweet.isBookMarked,
            editedAt = null,
            isEdited = false
        )
    }


}