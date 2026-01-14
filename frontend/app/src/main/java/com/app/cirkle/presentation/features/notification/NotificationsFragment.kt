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
import com.app.cirkle.R
import com.app.cirkle.databinding.FragmentNotificationsBinding
import com.app.cirkle.presentation.common.BaseFragment
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class NotificationsFragment : BaseFragment<FragmentNotificationsBinding>() {

    private val viewModel: NotificationsViewModel by viewModels()

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentNotificationsBinding {
        return FragmentNotificationsBinding.inflate(inflater, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.handleVerticalInsets()
        
        observeViewModel()
        
        // Load follow requests count when fragment is created
        viewModel.loadFollowRequests()

        binding.backButton.setOnClickListener {
            findNavController().navigateUp()
        }
        
        // Setup click listener for follow requests container
        binding.followRequestContainer.setOnClickListener {
            // Navigate to dedicated follow requests fragment
            findNavController().navigate(R.id.action_notifications_to_follow_requests)
        }
    }



    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is NotificationsUiState.Loading -> {
                            showLoading()
                        }
                        is NotificationsUiState.Success -> {
                            Log.d("NotificationsFragment", "Received ${state.followRequests.size} follow requests")
                            hideLoading()
                            
                            // Update the follow requests count display
                            val count = state.followRequests.size
                            binding.postCreatorId.text = if (count > 0) {
                                "$count pending request${if (count > 1) "s" else ""}"
                            } else {
                                "No pending requests"
                            }
                            Log.d("NotificationsFragment", "Updated UI with $count requests")
                        }
                        is NotificationsUiState.Error -> {
                            hideLoading()
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                        }
                        is NotificationsUiState.RequestHandled -> {
                            // This state is handled in the FollowRequestsFragment
                            // Just reload the count here
                            viewModel.loadFollowRequests()
                        }
                    }
                }
            }
        }
    }
} 