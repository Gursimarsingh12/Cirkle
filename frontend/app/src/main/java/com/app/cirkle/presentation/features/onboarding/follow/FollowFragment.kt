package com.app.cirkle.presentation.features.onboarding.follow

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentFollowBinding
import com.app.cirkle.presentation.common.BaseFragment
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class FollowFragment : BaseFragment<FragmentFollowBinding>() {

    @Inject
    lateinit var imageUtils: ImageUtils

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentFollowBinding {
        return FragmentFollowBinding.inflate(inflater, container, false)
    }

    private val adapter: FollowUserProfileAdapter by lazy {
        FollowUserProfileAdapter(
            followUser = { userId, follow -> viewModel.sendFollowRequest(userId, follow) },
            imageUtils = imageUtils
        )
    }
    private val viewModel: FollowFragmentViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.applyVerticalInsets()
        viewModel.getTopAccounts()
         binding.btnConfirm.setOnClickListener {
             if(viewModel.accountsFollowed.size < 3) {
                 Toast.makeText(requireContext(), "Please follow at least 3 accounts", Toast.LENGTH_LONG).show()
             } else {
                 findNavController().navigate(R.id.action_fragment_follow_top_voices_to_fragment_home)
             }
         }

        setUpRecycleView()
        setUpUi()
    }

    private fun setUpRecycleView() {
        binding.recycleView.layoutManager = LinearLayoutManager(requireContext())
        binding.recycleView.adapter = adapter
    }

    private fun setUpUi() {
        lifecycleScope.launch {
            viewLifecycleOwner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when(state) {
                        is FollowFragmentUiState.DataReceived -> {
                            hideLoading()
                            adapter.updateAdapter(state.data)
                            binding.recycleView.post { adapter.notifyDataSetChanged() }
                        }
                        is FollowFragmentUiState.Error -> {
                            hideLoading()
                            Toast.makeText(requireContext(), state.messages, Toast.LENGTH_LONG).show()
                        }
                        FollowFragmentUiState.Loading -> {
                            showLoading()
                        }
                        FollowFragmentUiState.UpdateSuccess -> {
                            NavUtils.navigateWithSlideAnim(findNavController(), R.id.action_fragment_follow_top_voices_to_fragment_home)
                        }
                    }
                }
            }
        }
    }
}