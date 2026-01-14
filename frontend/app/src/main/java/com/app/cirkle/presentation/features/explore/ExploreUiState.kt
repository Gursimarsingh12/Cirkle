package com.app.cirkle.presentation.features.explore

import com.app.cirkle.domain.model.user.User

data class ExploreUiState(
    val searchQuery: String = "",
    val searchResults: List<User> = emptyList(),
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isSearchActive: Boolean = false,
    val showEmptyState: Boolean = true
) 