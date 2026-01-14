package com.app.cirkle.core.utils.converters

import java.time.Duration
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

object TimeUtils {
    fun calculateTimeUntil(createdAt: String): String {
        if(createdAt.contains("ago")) return createdAt
        if(!createdAt.contains("T")) return createdAt

        val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")
        val localDateTime = LocalDateTime.parse(createdAt, formatter)
        val createdTime = localDateTime.atOffset(ZoneOffset.UTC)

        val now = OffsetDateTime.now(ZoneOffset.UTC)

        val duration = Duration.between(createdTime, now)
        return when {
            duration.toMinutes()<0 ->"0m ago"
            duration.toMinutes() < 60 -> "${duration.toMinutes()}m ago"
            duration.toHours() < 24 -> "${duration.toHours()}h ago"
            else -> "${duration.toDays()}d ago"
        }
    }
}