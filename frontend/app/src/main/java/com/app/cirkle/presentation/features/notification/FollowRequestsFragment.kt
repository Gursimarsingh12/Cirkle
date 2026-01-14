package com.app.cirkle.presentation.features.notification

import android.os.Bundle
import android.util.Log
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
import com.app.cirkle.databinding.FragmentFollowRequestsBinding
import com.app.cirkle.presentation.common.BaseFragment
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets

@AndroidEntryPoint
class FollowRequestsFragment : BaseFragment<FragmentFollowRequestsBinding>() {

    private val viewModel: NotificationsViewModel by viewModels()
    private val followRequestsAdapter: FollowRequestsAdapter by lazy {
        FollowRequestsAdapter { followRequest, accept ->
            viewModel.respondToFollowRequest(followRequest.followerId, accept)
        }
    }

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentFollowRequestsBinding {
        return FragmentFollowRequestsBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.applyVerticalInsets()
        
        binding.backButton.setOnClickListener {
            findNavController().navigateUp()
        }
        setupRecyclerView()
        observeViewModel()
        
        // Load follow requests when fragment is created
        viewModel.loadFollowRequests()
    }

    private fun setupRecyclerView() {
        binding.followRequestsRecyclerView.apply {
            adapter = followRequestsAdapter
            layoutManager = LinearLayoutManager(requireContext())
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is NotificationsUiState.Loading -> {
                            Log.d("FollowRequestsFragment", "Loading follow requests...")
                            showLoading()
                            binding.emptyStateLayout.visibility = View.GONE
                        }
                        is NotificationsUiState.Success -> {
                            Log.d("FollowRequestsFragment", "Received ${state.followRequests.size} follow requests")
                            hideLoading()
                            
                            if (state.followRequests.isEmpty()) {
                                binding.followRequestsRecyclerView.visibility = View.GONE
                                binding.emptyStateLayout.visibility = View.VISIBLE
                            } else {
                                binding.followRequestsRecyclerView.visibility = View.VISIBLE
                                binding.emptyStateLayout.visibility = View.GONE
                                followRequestsAdapter.updateRequests(state.followRequests)
                            }
                        }
                        is NotificationsUiState.Error -> {
                            hideLoading()
                            binding.emptyStateLayout.visibility = View.VISIBLE
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                        }
                        is NotificationsUiState.RequestHandled -> {
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                            // Reload follow requests after handling one
                            viewModel.loadFollowRequests()
                        }
                    }
                }
            }
        }
    }
} 