package com.djnews.domain.model

data class TrackInfo(
    val title: String,
    val artist: String,
    val albumArtUrl: String? = null
)

sealed class PlaybackState {
    object Idle : PlaybackState()
    object Connecting : PlaybackState()
    data class PlayingMusic(val mood: Mood, val track: TrackInfo?) : PlaybackState()
    data class PlayingNews(val episodeTitle: String = "VRT NWS") : PlaybackState()
    data class Error(val message: String) : PlaybackState()
}
