package com.app.cirkle.data.remote.mappers

import com.app.cirkle.data.model.common.MediaResponse
import com.app.cirkle.data.model.tweets.response.PaginatedTweetResponse
import com.app.cirkle.data.model.tweets.response.TweetResponse

import com.app.cirkle.domain.model.tweet.Media
import com.app.cirkle.domain.model.tweet.PaginatedTweets
import com.app.cirkle.domain.model.tweet.Tweet
import com.app.cirkle.core.utils.converters.TimeUtils
import com.app.cirkle.core.utils.converters.TimeUtils.calculateTimeUntil
import com.app.cirkle.data.model.tweets.request.FeedQueryParams
import com.app.cirkle.data.model.tweets.response.CommentResponse
import com.app.cirkle.domain.model.tweet.Comment
import com.app.cirkle.domain.model.tweet.MyComment
import com.app.cirkle.domain.model.tweet.TweetComplete
import com.app.cirkle.data.model.tweets.response.SharedTweetResponse
import com.app.cirkle.domain.model.tweet.SharedTweet

object TweetsMappers {

    fun FeedQueryParams.toQueryMap(): Map<String, Any?> {
        return mapOf(
            "page" to page,
            "page_size" to pageSize,
            "include_recommendations" to includeRecommendations,
            "feed_type" to feedType,
            "last_tweet_id" to lastTweetId,
            "refresh" to refresh
        ).filterValues { it != null } // optionally remove nulls
    }


    fun TweetResponse.toDomain(): Tweet {
        return Tweet(
            id = id,
            userId = userId,
            userName = userName,
            userProfileUrl = photoUrl ?: "",
            isUserOrganization = isOrganizational,
            isUserPrime = isPrime,
            text = text,
            mediaCount = media.size,
            media = media.map { it.toDomain() }, // Corrected mapping to Media
            timeUntilPost = calculateTimeUntil(createdAt),
            likesCount = likeCount,
            commentCount = commentCount,
            isLiked = isLiked,
            isBookMarked = isBookmarked,
            editedAt = editedAt,
            isEdited = editedAt != null
        )
    }

    fun TweetResponse.toTweetComplete(): TweetComplete{
        return TweetComplete(
            id = id,
            userId = userId,
            userName = userName,
            userProfileUrl = photoUrl ?: "",
            isUserOrganization = isOrganizational,
            isUserPrime = isPrime,
            text = text,
            mediaCount = media.size,
            media = media.map { it.toDomain() },
            timeUntilPost = calculateTimeUntil(createdAt),
            likesCount = likeCount,
            commentCount = commentCount,
            isLiked = isLiked,
            isBookMarked = isBookmarked,
            comments= comments.map { it.toComment() }.toMutableList()
        )
    }


    fun CommentResponse.toComment(): Comment{
        fun getCheckMarkState(isPrime: Boolean,isOrganizational: Boolean,):Int{
            return when {
                isPrime && isOrganizational -> 3
                isOrganizational -> 1
                isPrime -> 0
                else -> 2
            }
        }
        val data=if(author!=null){
            Comment.Author(author.userId,author.name,author.photo,getCheckMarkState(author.isOrganizational,author.isOrganizational))
        }else null
        return Comment(
            id,tweetId,userId,text,parentCommentId,likeCount,isLiked,calculateTimeUntil(createdAt),userName,photoUrl?:"",
            getCheckMarkState(isPrime,isOrganizational),
            data,
            editedAt,
            editedAt != null
        )

    }


    fun MediaResponse.toDomain(): Media {
        return Media(
            url = mediaUrl // Use the domain model's properties
        )
    }

    fun PaginatedTweetResponse.toDomain(): PaginatedTweets {
        return PaginatedTweets(
            tweets = tweets.map { it.toDomain() }.toMutableList(),
            page = page,
            total = total,
            pageSize = pageSize
        )
    }

    fun SharedTweetResponse.toSharedTweet(): SharedTweet {
        return SharedTweet(
            id = id,
            tweetId = tweetId,
            senderId = senderId,
            recipientId = recipientId,
            message = message,
            createdAt = createdAt ?: "",
            sharedAt = sharedAt,
            senderName = senderName,
            recipientName = recipientName,
            senderProfileUrl = senderPhotoPath,
            recipientProfileUrl = recipientPhotoPath,
            tweet = tweet.toDomain(),
            imageCount = imageCount,
            formattedTime = calculateTimeUntil(sharedAt)
        )
    }

    fun List<SharedTweetResponse>.toSharedTweetList(): List<SharedTweet> {
        return map { it.toSharedTweet() }
    }
}
