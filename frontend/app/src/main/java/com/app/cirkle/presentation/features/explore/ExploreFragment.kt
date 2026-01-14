package com.app.cirkle.presentation.features.explore

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import androidx.activity.addCallback
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.app.cirkle.AppNavigationDirections
import com.app.cirkle.R
import com.app.cirkle.core.utils.common.ImageUtils
import com.app.cirkle.core.utils.common.NavUtils
import com.app.cirkle.core.utils.common.WindowInsetsHelper.applyVerticalInsets
import com.app.cirkle.core.utils.validation.UserSearchValidator
import com.app.cirkle.databinding.FragmentExploreBinding
import com.app.cirkle.domain.model.user.User
import com.app.cirkle.presentation.common.BaseFragment
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class ExploreFragment : BaseFragment<FragmentExploreBinding>() {

    private val viewModel: ExploreViewModel by viewModels()
    
    @Inject
    lateinit var imageUtils: ImageUtils
    private lateinit var searchResultsAdapter: SearchResultsAdapter

    override fun getViewBinding(
        inflater: LayoutInflater,
        container: ViewGroup?
    ): FragmentExploreBinding {
        return FragmentExploreBinding.inflate(inflater, container, false)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        requireActivity().onBackPressedDispatcher.addCallback(this) {
            findNavController().navigate(R.id.action_return_to_home)
        }
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.root.applyVerticalInsets()
        setupRecyclerView()
        setupSearchFunctionality()
        observeViewModel()
    }

    private fun setupRecyclerView() {
        searchResultsAdapter = SearchResultsAdapter(
            imageUtils = imageUtils
        ){ user ->
            navigateToUserProfile(user)
        }
        
        binding.rvSearchResults.apply {
            adapter = searchResultsAdapter
            layoutManager = LinearLayoutManager(requireContext())
        }
    }

    private fun setupSearchFunctionality() {
        // Text change listener for real-time username search
        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            
            override fun afterTextChanged(s: Editable?) {
                val query = s?.toString()?.trim() ?: ""
                viewModel.updateSearchQuery(query)
            }
        })

        // Search icon click and IME action for User ID search
        val performUserIdSearch = {
            val query = binding.etSearch.text.toString().trim()
            if (UserSearchValidator.shouldTriggerUserIdSearch(query)) {
                viewModel.performUserIdSearch(query)
            }
        }

        binding.ivSearchIcon.setOnClickListener { performUserIdSearch() }
        
        binding.etSearch.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                performUserIdSearch()
                true
            } else {
                false
            }
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collect { uiState ->
                updateUiState(uiState)
            }
        }
    }

    private fun updateUiState(uiState: ExploreUiState) {
        // Update search results
        searchResultsAdapter.submitList(uiState.searchResults)
        
        // Show/hide loading
        binding.progressBar.visibility = if (uiState.isLoading) View.VISIBLE else View.GONE
        
        // Show/hide search results
        binding.rvSearchResults.visibility = if (uiState.searchResults.isNotEmpty() && !uiState.isLoading) {
            View.VISIBLE
        } else {
            View.GONE
        }
        
        // Show/hide empty state
        binding.llEmptyState.visibility = if (uiState.showEmptyState && !uiState.isLoading && uiState.errorMessage == null) {
            View.VISIBLE
        } else {
            View.GONE
        }
        
        // Show/hide error state
        if (uiState.errorMessage != null) {
            binding.llErrorState.visibility = View.VISIBLE
            binding.tvErrorMessage.text = uiState.errorMessage
        } else {
            binding.llErrorState.visibility = View.GONE
        }
    }

    private fun navigateToUserProfile(user: User) {
        val action = AppNavigationDirections.actionToFragmentUserProfile(user.id)
        NavUtils.navigateWithSlideAnim(findNavController(), action.actionId, action.arguments)
    }
}