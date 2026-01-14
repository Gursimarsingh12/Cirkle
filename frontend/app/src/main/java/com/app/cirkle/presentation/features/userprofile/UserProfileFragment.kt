package com.app.cirkle.presentation.features.userprofile

import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.core.os.bundleOf
import androidx.core.view.isVisible
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.LinearLayoutManager
import com.bumptech.glide.Glide
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.databinding.FragmentUserProfileBinding
import com.app.cirkle.domain.model.user.UserProfile
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.presentation.common.BaseTweetsFragment
import com.app.cirkle.presentation.features.tweets.TweetsAdapter
import com.app.cirkle.presentation.features.tweets.TweetsViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class UserProfileFragment : BaseTweetsFragment<FragmentUserProfileBinding>() {


    private val viewModel: UserProfileViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentUserProfileBinding {
        return FragmentUserProfileBinding.inflate(inflater)
    }

    val navArgs: UserProfileFragmentArgs by navArgs()


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel.loadUserProfileData(navArgs.userId)
        viewModel.loadUserTweets(navArgs.userId)
        observeUiState()
        setUpRecycleView()
        setupFollowButton()
    }

    fun setUpRecycleView(){
        binding.feedRecyclerView.layoutManager= LinearLayoutManager(requireContext())
        binding.feedRecyclerView.adapter=tweetsAdapter
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED){
                viewModel.pagedUserTweets.collectLatest {
                    tweetsAdapter.submitData(it)
                }
            }
        }
    }

    fun observeUiState(){
        lifecycleScope.launch {
            lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect {
                    when(it) {
                        is UserProfileUiState.Error -> {
                            Toast.makeText(requireContext(),it.message, Toast.LENGTH_LONG).show()
                        }
                        UserProfileUiState.Idle -> {
                            hideLoading()
                        }
                        UserProfileUiState.Loading -> {
                            showLoading()
                        }
                        is UserProfileUiState.ProfileDataLoaded -> {
                            hideLoading()
                            Log.d("UserProfileFragment", "Profile loaded for user: ${it.userProfile.name}, follow status: ${it.userProfile.followStatus}")
                            setupProfileUI(it.userProfile)
                            // Display the follower and following counts from the profile response
                            binding.txtFollowerCount.text = it.userProfile.followerCount
                            binding.txtFollowingCount.text = it.userProfile.followingCount
                        }
                        is UserProfileUiState.CountsUpdated -> {
                            // Update the counts with real data from API
                            binding.txtFollowerCount.text = it.counts.followersCount.toString()
                            binding.txtFollowingCount.text = it.counts.followingCount.toString()
                        }
                        UserProfileUiState.FollowLoading -> {
                            // Show loading state for follow button
                            binding.btnFollow.isEnabled = false
                            binding.btnFollow.text = "Loading..."
                            binding.btnFollow.setBackgroundResource(R.drawable.curved_grey_rectangle)
                            binding.btnFollow.setTextColor(ContextCompat.getColor(requireContext(), R.color.black))
                        }
                        is UserProfileUiState.FollowSuccess -> {
                            binding.btnFollow.isEnabled = true
                            Toast.makeText(requireContext(), it.message, Toast.LENGTH_SHORT).show()
                            // Update button state based on the current profile
                            viewModel.currentUserProfile?.let { profile ->
                                updateFollowButton(profile)
                            }
                            // Display updated counts if available
                            viewModel.currentUserCounts?.let { counts ->
                                binding.txtFollowerCount.text = counts.followersCount.toString()
                                binding.txtFollowingCount.text = counts.followingCount.toString()
                            }
                        }
                        is UserProfileUiState.FollowError -> {
                            binding.btnFollow.isEnabled = true
                            Toast.makeText(requireContext(), it.message, Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }


    private fun setupProfileUI(profile: UserProfile) {
        binding.apply {
            txtUserName.text = profile.name
            txtUserId.text = "@${profile.id}"
            if(profile.bio.isNotBlank())
                txtBio.text = profile.bio
            else
                txtBio.isVisible=false

            txtFollowerCount.text = profile.followerCount
            txtFollowingCount.text = profile.followingCount

            imageUtils.loadImageIntoImageView(profile.profileUrl,imgProfile, centerCrop = true)
            imageUtils.loadImageIntoImageView(profile.bannerUrl,imgBanner, isMedia = true)

            layoutInterests.removeAllViews()
            profile.interests.forEach { interest ->
                val interestView =
                    layoutInflater.inflate(R.layout.interest_item, layoutInterests, false)
                val textView = interestView.findViewById<TextView>(R.id.interestTextView)
                textView.text = interest
                layoutInterests.addView(interestView)
            }
            checkMark.setAccountType(profile.checkMarkState)
            
            // Handle content visibility based on follow status and privacy settings
            handleContentVisibility(profile)
        }

        // Update follow button based on follow status
        updateFollowButton(profile)
    }
    
    private fun handleContentVisibility(profile: UserProfile) {
        binding.apply {
            if (profile.isPrivate) {
                // For private accounts, only show content if user is following
                if (profile.followStatus == "following" || profile.isOrganizational) {
                    feedRecyclerView.visibility = View.VISIBLE
                } else {
                    feedRecyclerView.visibility = View.GONE
                    // You can show a message here like "This account is private"
                }
            } else {
                // For public accounts, always show content
                feedRecyclerView.visibility = View.VISIBLE
            }
        }
    }
    
    private fun setupFollowButton() {
        binding.btnFollow.setOnClickListener {
            viewModel.currentUserProfile?.let { profile ->
                when (profile.followStatus) {
                    "not_following" -> {
                        viewModel.followUser(profile.id)
                    }
                    "pending" -> {
                        // Cancel follow request
                        viewModel.unfollowUser(profile.id)
                    }
                    "following" -> {
                        // Show confirmation dialog for unfollowing
                        androidx.appcompat.app.AlertDialog.Builder(requireContext())
                            .setTitle("Unfollow ${profile.name}?")
                            .setMessage("You will no longer see their posts in your feed.")
                            .setPositiveButton("Unfollow") { _, _ ->
                                viewModel.unfollowUser(profile.id)
                            }
                            .setNegativeButton("Cancel", null)
                            .show()
                    }
                }
            }
        }
    }
    
    private fun updateFollowButton(profile: UserProfile) {
        Log.d("UserProfileFragment", "Updating follow button with status: ${profile.followStatus}")
        binding.btnFollow.apply {
            isEnabled = true
            when (profile.followStatus) {
                "not_following" -> {
                    text = "Follow"
                    setBackgroundResource(R.drawable.newuserwhitebtnthemebg)
                    setTextColor(ContextCompat.getColor(requireContext(), R.color.black))
                    Log.d("UserProfileFragment", "Set button to 'Follow' state - black text, newuserwhitebtnthemebg background")
                }
                "pending" -> {
                    text = "Requested"
                    setBackgroundResource(R.drawable.curved_grey_rectangle)
                    setTextColor(ContextCompat.getColor(requireContext(), R.color.black))
                    Log.d("UserProfileFragment", "Set button to 'Requested' state")
                }
                "following" -> {
                    text = "Following"
                    setBackgroundResource(R.drawable.bg_chip_selected)
                    setTextColor(ContextCompat.getColor(requireContext(), R.color.white))
                    Log.d("UserProfileFragment", "Set button to 'Following' state - white text, bg_chip_selected background")
                }
                else -> {
                    text = "Follow"
                    setBackgroundResource(R.drawable.newuserwhitebtnthemebg)
                    setTextColor(ContextCompat.getColor(requireContext(), R.color.black))
                    Log.d("UserProfileFragment", "Set button to default 'Follow' state for unknown status: ${profile.followStatus}")
                }
            }
        }
    }

}