package com.djnews.domain.model

enum class Mood(
    val label: String,
    val emoji: String,
    val spotifyPlaylistUri: String,
    val description: String
) {
    CHILL(
        label = "Chill",
        emoji = "🌙",
        spotifyPlaylistUri = "spotify:playlist:37i9dQZF1DX4WYpdgoIcn6",
        description = "Relaxed & mellow vibes"
    ),
    ENERGY(
        label = "Energy",
        emoji = "⚡",
        spotifyPlaylistUri = "spotify:playlist:37i9dQZF1DXdxcBWuJkbcy",
        description = "High-octane power tracks"
    ),
    FOCUS(
        label = "Focus",
        emoji = "🎯",
        spotifyPlaylistUri = "spotify:playlist:37i9dQZF1DWZeKCadgRdKQ",
        description = "Deep concentration music"
    ),
    PARTY(
        label = "Party",
        emoji = "🎉",
        spotifyPlaylistUri = "spotify:playlist:37i9dQZF1DXa2PvUpywmrr",
        description = "Let's go dance!"
    )
}
