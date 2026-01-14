package com.app.cirkle.data.remote.mappers

import com.app.cirkle.data.model.user.response.SearchedUser
import com.app.cirkle.domain.model.user.User

fun SearchedUser.toDomainModel(): User {
    return User(
        id = this.user_id,
        name = this.name,
        followerCount = "0", // Default value since not provided by API
        profileUrl = this.photo ?: "",
        checkMarkState = 0 // Default value since not provided by API
    )
}

fun List<SearchedUser>.toDomainModelList(): List<User> {
    return this.map { it.toDomainModel() }
} 