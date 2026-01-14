package com.app.cirkle.data.model.user.request

data class SearchUsersRequest(
    val search: String,
    val page: Int = 1
) 