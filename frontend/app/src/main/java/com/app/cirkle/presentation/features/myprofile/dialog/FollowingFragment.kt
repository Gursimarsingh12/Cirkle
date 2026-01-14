package com.app.cirkle.presentation.features.myprofile.dialog

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import dagger.hilt.android.AndroidEntryPoint
import kotlin.getValue
import kotlinx.coroutines.flow.collectLatest

// FollowingFragment.kt
@AndroidEntryPoint
class FollowingFragment : BaseFollowFragment() {
    private val viewModel: FollowViewModel by activityViewModels()
    override val dataFlow get() = viewModel.getFollowing()
    override val showUnfollow: Boolean = true
    override val onUnfollow: ((com.app.cirkle.domain.model.user.MyFollowFollowing) -> Unit)? = { user ->
        // Show confirmation dialog before unfollowing
        AlertDialog.Builder(requireContext())
            .setTitle("Unfollow ${user.followerName}?")
            .setMessage("You will no longer see their posts in your feed.")
            .setPositiveButton("Unfollow") { _, _ ->
                viewModel.unfollowUser(user.followerId)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        // Observe unfollow state
        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            viewModel.unfollowState.collectLatest { state ->
                when (state) {
                    is UnfollowUiState.Success -> {
                        Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                        // Optionally refresh the list
                        adapter.refresh()
                    }
                    is UnfollowUiState.Error -> {
                        Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                    }
                    else -> {}
                }
            }
        }
    }
}