package com.djnews.data.news

import android.util.Log
import android.util.Xml
import org.xmlpull.v1.XmlPullParser
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "VrtNwsRepository"

// Max age of podcast episode before falling back to live stream (65 min)
private const val MAX_EPISODE_AGE_MS = 65 * 60 * 1000L

// VRT NWS podcast RSS feed (hourly news, max 3 min per episode)
private const val RSS_URL =
    "https://podcasts.vrt.be/v1/program-6848a863-f561-429b-8f9b-19aaa4f7ef4c"

// VRT Radio 1 live stream as fallback (carries het nieuws op het uur)
const val LIVE_STREAM_FALLBACK_URL =
    "http://progressive-audio.vrtcdn.be/content/fixed/11_11niws-snip_hi.mp3"

@Singleton
class VrtNwsRepository @Inject constructor(
    private val rssService: VrtNwsRssService
) {
    /**
     * Returns the audio URL to play for the news segment.
     * Prefers the latest podcast episode; falls back to live stream if the
     * episode is stale (older than 65 min) or the fetch fails.
     */
    suspend fun getNewsAudioUrl(): String {
        return try {
            val episode = fetchLatestEpisode()
            val ageMs = System.currentTimeMillis() - episode.publishedAt.time
            if (ageMs <= MAX_EPISODE_AGE_MS) {
                Log.d(TAG, "Using podcast episode: ${episode.title} (${ageMs / 60000} min old)")
                episode.audioUrl
            } else {
                Log.d(TAG, "Episode too old (${ageMs / 60000} min), using live stream")
                LIVE_STREAM_FALLBACK_URL
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch RSS, using live stream: ${e.message}")
            LIVE_STREAM_FALLBACK_URL
        }
    }

    private suspend fun fetchLatestEpisode(): NewsEpisode {
        val body = rssService.fetchRssFeed(RSS_URL)
        val xml = body.string()
        return parseLatestEpisode(xml)
    }

    private fun parseLatestEpisode(xml: String): NewsEpisode {
        val parser = Xml.newPullParser().apply {
            setFeature(XmlPullParser.FEATURE_PROCESS_NAMESPACES, false)
            setInput(xml.reader())
        }

        var inItem = false
        var title = ""
        var audioUrl = ""
        var pubDateStr = ""

        val dateFormat = SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss Z", Locale.ENGLISH)

        var eventType = parser.eventType
        while (eventType != XmlPullParser.END_DOCUMENT) {
            when (eventType) {
                XmlPullParser.START_TAG -> when (parser.name) {
                    "item" -> {
                        // Only parse the first (latest) item
                        if (inItem) return buildEpisode(title, audioUrl, pubDateStr, dateFormat)
                        inItem = true
                    }
                    "title" -> if (inItem) title = parser.nextText()
                    "pubDate" -> if (inItem) pubDateStr = parser.nextText()
                    "enclosure" -> if (inItem) audioUrl = parser.getAttributeValue(null, "url") ?: ""
                }
            }
            eventType = parser.next()
        }

        return buildEpisode(title, audioUrl, pubDateStr, dateFormat)
    }

    private fun buildEpisode(
        title: String,
        audioUrl: String,
        pubDateStr: String,
        dateFormat: SimpleDateFormat
    ): NewsEpisode {
        val pubDate = try {
            dateFormat.parse(pubDateStr) ?: Date()
        } catch (e: Exception) {
            Date()
        }
        require(audioUrl.isNotBlank()) { "No audio URL found in RSS feed" }
        return NewsEpisode(title = title, audioUrl = audioUrl, publishedAt = pubDate)
    }
}
