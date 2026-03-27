package com.djnews.data.news

import java.util.Date

data class NewsEpisode(
    val title: String,
    val audioUrl: String,
    val publishedAt: Date,
    val durationSeconds: Int? = null
)
