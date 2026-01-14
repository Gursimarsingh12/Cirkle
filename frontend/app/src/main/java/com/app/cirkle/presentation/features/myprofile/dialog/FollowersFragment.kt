package com.app.cirkle.presentation.features.myprofile.dialog

import androidx.fragment.app.activityViewModels
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class FollowersFragment : BaseFollowFragment() {
    private val viewModel: FollowViewModel by activityViewModels()
    override val dataFlow get() = viewModel.getFollowers()
    override val showUnfollow: Boolean = false
}

