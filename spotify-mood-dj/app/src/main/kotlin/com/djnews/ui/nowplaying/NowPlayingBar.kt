package com.djnews.ui.nowplaying

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Radio
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.djnews.domain.model.PlaybackState
import com.djnews.domain.model.TrackInfo

@Composable
fun NowPlayingBar(
    playbackState: PlaybackState,
    currentTrack: TrackInfo?,
    modifier: Modifier = Modifier
) {
    val isNews = playbackState is PlaybackState.PlayingNews

    AnimatedContent(
        targetState = isNews,
        transitionSpec = { fadeIn() togetherWith fadeOut() },
        label = "nowplaying_bar"
    ) { showingNews ->
        Surface(
            modifier = modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)),
            color = if (showingNews) Color(0xFF1565C0) else MaterialTheme.colorScheme.surfaceVariant,
            tonalElevation = 8.dp
        ) {
            Row(
                modifier = Modifier
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = if (showingNews) Icons.Default.Radio else Icons.Default.MusicNote,
                    contentDescription = null,
                    tint = if (showingNews) Color.White else MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    if (showingNews) {
                        Text(
                            text = "VRT NWS",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color.White.copy(alpha = 0.7f)
                        )
                        Text(
                            text = "Nieuws op het uur",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = Color.White,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    } else {
                        Text(
                            text = currentTrack?.artist ?: "Spotify DJ",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            text = currentTrack?.title ?: when (playbackState) {
                                is PlaybackState.Idle -> "Kies een mood om te starten"
                                is PlaybackState.Connecting -> "Verbinden met Spotify..."
                                else -> "Nu aan het spelen"
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.SemiBold,
                            color = MaterialTheme.colorScheme.onSurface,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }

                // Pulsing dot indicator during playback
                if (playbackState is PlaybackState.PlayingMusic || showingNews) {
                    PlayingIndicator(
                        color = if (showingNews) Color.White else MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}

@Composable
private fun PlayingIndicator(color: Color) {
    var tick by remember { mutableIntStateOf(0) }
    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(600)
            tick = (tick + 1) % 3
        }
    }
    Row(
        horizontalArrangement = Arrangement.spacedBy(3.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        repeat(3) { index ->
            val height = when {
                index == tick -> 16.dp
                else -> 8.dp
            }
            Box(
                modifier = Modifier
                    .width(3.dp)
                    .height(height)
                    .clip(RoundedCornerShape(2.dp))
                    .background(color)
            )
        }
    }
}
