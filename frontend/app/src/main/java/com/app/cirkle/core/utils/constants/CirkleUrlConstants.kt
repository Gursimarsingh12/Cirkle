package com.app.cirkle.core.utils.constants

object CirkleUrlConstants {

    const val BASE_URL = "http://192.168.1.44"

    // Auth
    const val LOGIN = "/auth/login"
    const val REGISTER = "/auth/register"
    const val LOG_OUT = "/auth/logout"
    const val REFRESH_TOKEN = "/auth/refresh"
    const val FORGOT_PASSWORD = "/auth/forgot-password"
    const val CHANGE_PASSWORD = "/auth/change-password"
    const val SET_ONLINE_STATUS = "/auth/set-online-status"
    const val GET_CURRENT_USER = "/auth/me"
    const val GET_COMMANDS = "/auth/commands"

    // Tweets
    const val POST_TWEET = "/tweets/post"
    const val GET_TWEET_FEED = "/tweets/feed"
    const val GET_MY_TWEETS = "/tweets/my-tweets"
    const val GET_RECOMMENDED = "/tweets/recommend"
    const val GET_LIKED = "/tweets/liked"
    const val GET_BOOKMARKED = "/tweets/bookmarked"
    const val GET_SHARED = "/tweets/shared"
    const val GET_SENT_SHARES = "/tweets/sent-shares"
    const val GET_RECEIVED_SHARES = "/tweets/received-shares"
    const val GET_TWEET_BY_ID = "/tweets/{tweet_id}"
    const val SHARE_TWEET = "/tweets/share"
    const val LIKE_TWEET = "/tweets/like"
    const val BOOKMARK_TWEET = "/tweets/bookmark"
    const val GET_USER_TWEETS = "/tweets/user/{user_id}/tweets"
    const val REPORT_COMMENT="/tweets/comment/report"
    const val REPORT_TWEET="/tweets/report"
    const val DELETE_TWEET="/tweets/{tweet_id}"
    const val EDIT_TWEET="/tweets/{tweet_id}"
    const val EDIT_COMMENT="/tweets/comment/{comment_id}"

    // User
    const val GET_MY_PROFILE = "/user/profile"
    const val GET_USER_PROFILE = "/user/profile/{user_id}"
    const val UPDATE_PROFILE = "/user/profile"
    const val GET_FOLLOWERS = "/user/followers"
    const val GET_FOLLOWING = "/user/following"
    const val GET_FOLLOW_REQUESTS = "/user/follow-requests"
    const val FOLLOW_USER = "/user/follow/{followee_id}"
    const val RESPOND_FOLLOW_REQUEST = "/user/follow-request/{follower_id}"
    const val UNFOLLOW_USER = "/user/unfollow/{followee_id}"
    const val GET_ALL_INTERESTS = "/user/interests/all"
    const val GET_INTERESTS = "/user/interests"
    const val ADD_INTEREST = "/user/interests"
    const val REMOVE_INTEREST = "/user/interests/{interest_id}"
    const val ADD_MULTIPLE_INTERESTS = "/user/interests/set"
    const val GET_TOP_ACCOUNTS = "/user/top-accounts"
    const val SEARCH_USERS = "/user/users/search"
    const val GET_OTHER_USERS_FOLLOWERS="/user/followers/{target_user_id}"
    const val GET_OTHER_USERS_FOLLOWING="/user/following/{target_user_id}"
    const val GET_MUTUAL_FOLLOWERS = "/user/mutual-followers"
}