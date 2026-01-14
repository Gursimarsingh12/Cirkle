package com.app.cirkle.data.model.user.response

data class SearchUsersResponse(
    val users: List<SearchedUser>,
    val total: Int,
    val page: Int,
    val page_size: Int
)

data class SearchedUser(
    val user_id: String,
    val name: String,
    val photo: String?
) 