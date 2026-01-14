package com.app.cirkle.presentation.features.myprofile.base

import android.annotation.SuppressLint
import android.util.Log
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.activity.addCallback
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.setFragmentResultListener
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.paging.LoadState
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.databinding.FragmentMyProfileBinding
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.domain.model.user.MyProfile
import com.app.cirkle.presentation.common.BaseTweetsFragment
import com.app.cirkle.presentation.common.SharedImageViewModel
import com.app.cirkle.presentation.features.myprofile.dialog.FollowFollowingDialog
import com.app.cirkle.presentation.features.post.dialogs.EditTweetDialog
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MyProfileFragment : BaseTweetsFragment<FragmentMyProfileBinding>() {

    private val viewModel: MyProfileViewModel by viewModels()
    private val sharedImageViewModel: SharedImageViewModel by activityViewModels()


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requireActivity().onBackPressedDispatcher.addCallback(this) {
            findNavController().navigate(R.id.action_return_to_home)
        }
    }


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupRecyclerView()
        setClickListeners()
        observeUserProfile()
        setupCameraResultListener()
    }

    private fun setupRecyclerView() {
        binding.feedRecyclerView.apply {
            adapter = tweetsAdapter
            layoutManager = LinearLayoutManager(requireContext())
        }
    }

    private fun observeUserProfile() {
        viewLifecycleOwner.lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.getMyProfile()
                }
                launch {
                    viewModel.myTweets.collectLatest {
                        tweetsAdapter.submitData(it)
                    }
                }
                launch {
                    viewModel.userProfileState.collect { state ->
                        handleProfileState(state.profileState)
//                    handleTweetsState(state.tweetsState)
                        binding.swipeRefreshLayout.isRefreshing = state.isRefreshing
                    }
                }
                launch {
                    tweetsAdapter.loadStateFlow.collect { loadStates->
                        when (val refreshState = loadStates.refresh) {
                            is LoadState.Loading -> {
                                binding.tweetsProgressBar.isVisible=true
                                binding.feedRecyclerView.isVisible=false
                            }

                            is LoadState.NotLoading -> {
                                binding.swipeRefreshLayout.isRefreshing=false
                                binding.tweetsProgressBar.isVisible=false
                                // Check if the list is empty
                                val isEmpty = tweetsAdapter.itemCount == 0
                                binding.feedRecyclerView.visibility = if (isEmpty) View.GONE else View.VISIBLE
                                binding.emptyTweetsView.visibility = if (isEmpty) View.VISIBLE else View.GONE
                            }

                            is LoadState.Error -> {
                                binding.tweetsProgressBar.isVisible=false
                                Toast.makeText(requireContext(),refreshState.error.message, Toast.LENGTH_LONG).show()
                            }
                        }

                    }
                }
 
            }
        }
    }

    private fun handleProfileState(profileState: ProfileState) {
        when (profileState) {
            is ProfileState.Loading -> {
                showLoading()
                binding.mainContent.isVisible = false
            }
            is ProfileState.Success -> {
                hideLoading()
                binding.mainContent.isVisible = true
                setupProfileUI(profileState.myProfile)
            }
            is ProfileState.Error -> {
                hideLoading()
                binding.mainContent.isVisible = false
                Toast.makeText(requireContext(), profileState.message, Toast.LENGTH_LONG).show()
            }
        }
    }


    private fun setClickListeners() {
        binding.btnEditProfile.setOnClickListener {
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_profile_to_fragment_edit_profile)
        }

        binding.btnSettings.setOnClickListener {
            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_profile_to_fragment_settings)
        }

        binding.swipeRefreshLayout.setOnRefreshListener {
            tweetsAdapter.refresh()
            viewModel.getMyProfile()
        }

        binding.followersCountLayout.setOnClickListener {
            FollowFollowingDialog.newInstance(1).show(parentFragmentManager, "FollowFollowingDialog")
        }
        binding.followingCountLayout.setOnClickListener {
            FollowFollowingDialog.newInstance(0).show(parentFragmentManager, "FollowFollowingDialog")
        }
    }

    @SuppressLint("NotifyDataSetChanged")
    private fun setupCameraResultListener() {
        setFragmentResultListener("camera_result") { _, bundle ->
            val filePath = bundle.getString("image_file_path")
            val file = filePath?.let { java.io.File(it) }
            
            if (file != null) {
                sharedImageViewModel.addImage(file)
            }
            
            val pendingTweet = sharedImageViewModel.pendingEditTweet.value
            val pendingCallback = sharedImageViewModel.getPendingEditCallback()
            
            if (pendingTweet != null && pendingCallback != null) {
                val editDialog = EditTweetDialog.newInstance(pendingTweet) { updatedTweet ->
                    updateTweetInAdapter(updatedTweet.id) { tweetInAdapter ->
                        tweetInAdapter.text = updatedTweet.text
                        tweetInAdapter.mediaCount = updatedTweet.mediaCount
                        tweetInAdapter.media = updatedTweet.media
                        tweetInAdapter.editedAt = updatedTweet.editedAt
                        tweetInAdapter.isEdited = updatedTweet.isEdited
                    }
                    tweetsAdapter.notifyDataSetChanged()
                    sharedImageViewModel.clearPendingEditTweet()
                }
                editDialog.show(parentFragmentManager, "EditTweetDialog")
            }
        }
        
        setFragmentResultListener("edit_tweet_camera_request") { _, _ ->
            val action = MyProfileFragmentDirections.actionFragmentMyProfileToFragmentCamera(false, false, true)
            findNavController().navigate(action)
        }
    }

    private fun updateTweetInAdapter(tweetId: Long, update: (Tweet) -> Unit) {
        val index = tweetsAdapter.snapshot().items.indexOfFirst { it.id == tweetId }
        val tweet = tweetsAdapter.peek(index)
        if (tweet != null) {
            update(tweet)
        }
    }

    private fun setupProfileUI(profile: MyProfile) {
        Log.d("BackEndProfile","$profile")
        binding.apply {
            txtUserName.text = profile.name
            txtUserId.text = "@${profile.id}"
            if(profile.bio.isNotBlank())
                txtBio.text = profile.bio
            else
                txtBio.isVisible=false
            txtFollowerCount.text = profile.followerCount
            txtFollowingCount.text = profile.followingCount

            if(profile.profileUrl.isEmpty()){
                imgProfile.setImageDrawable(ContextCompat.getDrawable(requireContext(),R.drawable.default_user_img))
            }else {
                imageUtils.loadImageIntoImageView(profile.profileUrl, imgProfile, centerCrop = true)
            }
            imageUtils.loadImageIntoImageView(profile.bannerUrl,imgBanner, centerInside = true, isMedia = true)

            layoutInterests.removeAllViews()
            profile.interests.forEach { interest ->
                val interestView =
                    layoutInflater.inflate(R.layout.interest_item, layoutInterests, false)
                val textView = interestView.findViewById<TextView>(R.id.interestTextView)
                textView.text = interest
                layoutInterests.addView(interestView)
            }
            checkMark.setAccountType(profile.checkMarkState)
        }
    }

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentMyProfileBinding {
        return FragmentMyProfileBinding.inflate(inflater)
    }

    fun scrollToTopOrRefresh() {
        binding.feedRecyclerView.scrollToPosition(0)
        viewModel.getMyProfile()
        tweetsAdapter.refresh()
    }
}