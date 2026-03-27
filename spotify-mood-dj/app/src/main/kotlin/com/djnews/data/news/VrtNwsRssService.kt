package com.djnews.data.news

import okhttp3.ResponseBody
import retrofit2.http.GET
import retrofit2.http.Url

interface VrtNwsRssService {
    /**
     * Fetches the VRT NWS podcast RSS feed.
     * The full URL is passed so the base URL doesn't matter for this call.
     */
    @GET
    suspend fun fetchRssFeed(@Url url: String): ResponseBody
}
