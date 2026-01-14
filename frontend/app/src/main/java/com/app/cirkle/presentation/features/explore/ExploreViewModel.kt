package com.app.cirkle.presentation.features.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.app.cirkle.core.utils.common.ResultWrapper
import com.app.cirkle.core.utils.validation.UserSearchValidator
import com.app.cirkle.data.local.SecuredSharedPreferences
import com.app.cirkle.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(FlowPreview::class)
@HiltViewModel
class ExploreViewModel @Inject constructor(
    private val userRepository: UserRepository,
    private val securedSharedPreferences: SecuredSharedPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(ExploreUiState())
    val uiState: StateFlow<ExploreUiState> = _uiState.asStateFlow()

    private val _searchQuery = MutableStateFlow("")

    init {
        setupSearchDebouncing()
    }

    private fun setupSearchDebouncing() {
        _searchQuery
            .debounce(300) // 300ms debounce
            .distinctUntilChanged()
            .filter { query ->
                UserSearchValidator.shouldTriggerUsernameSearch(query)
            }
            .onEach { query ->
                performUsernameSearch(query)
            }
            .launchIn(viewModelScope)
    }

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
        _uiState.value = _uiState.value.copy(
            searchQuery = query,
            showEmptyState = query.isEmpty(),
            isSearchActive = query.isNotEmpty()
        )

        if (query.isEmpty()) {
            clearSearchResults()
        }
    }

    fun performUserIdSearch(userId: String) {
        if (!UserSearchValidator.shouldTriggerUserIdSearch(userId)) {
            return
        }

        viewModelScope.launch {
            val loggedInUserId = securedSharedPreferences.getUserId()
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)

            userRepository.searchUsers(userId).collectLatest { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        val filteredResults = result.value.filter { it.id != loggedInUserId }
                        _uiState.update {
                            it.copy(
                                searchResults = filteredResults,
                                isLoading = false,
                                showEmptyState = filteredResults.isEmpty()
                            )
                        }
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            errorMessage = result.error ?: "Unknown error occurred",
                            searchResults = emptyList(),
                            showEmptyState = true
                        )
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            errorMessage = "Network error. Please check your connection.",
                            searchResults = emptyList(),
                            showEmptyState = true
                        )
                    }
                }
            }
        }
    }


    private fun performUsernameSearch(username: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)

            val loggedInUserId = securedSharedPreferences.getUserId()

            userRepository.searchUsers(username).collect { result ->
                when (result) {
                    is ResultWrapper.Success -> {
                        val filteredResults = result.value.filter { it.id != loggedInUserId }
                        _uiState.update {
                            it.copy(
                                searchResults = filteredResults,
                                isLoading = false,
                                showEmptyState = filteredResults.isEmpty()
                            )
                        }
                    }
                    is ResultWrapper.GenericError -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            errorMessage = result.error ?: "Unknown error occurred",
                            searchResults = emptyList(),
                            showEmptyState = true
                        )
                    }
                    ResultWrapper.NetworkError -> {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            errorMessage = "Network error. Please check your connection.",
                            searchResults = emptyList(),
                            showEmptyState = true
                        )
                    }
                }
            }
        }
    }


    private fun clearSearchResults() {
        _uiState.value = _uiState.value.copy(
            searchResults = emptyList(),
            isLoading = false,
            errorMessage = null,
            isSearchActive = false
        )
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }
} 