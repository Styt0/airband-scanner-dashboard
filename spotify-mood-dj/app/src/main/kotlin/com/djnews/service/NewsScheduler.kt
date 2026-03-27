package com.djnews.service

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import com.djnews.receiver.NewsAlarmReceiver
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Calendar
import javax.inject.Inject
import javax.inject.Singleton

private const val TAG = "NewsScheduler"

@Singleton
class NewsScheduler @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val alarmManager = context.getSystemService(AlarmManager::class.java)

    private val pendingIntent: PendingIntent
        get() = PendingIntent.getBroadcast(
            context,
            REQUEST_CODE,
            Intent(context, NewsAlarmReceiver::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

    fun scheduleNextHourAlarm() {
        val triggerAt = nextHourMillis()
        Log.d(TAG, "Scheduling news alarm for ${java.util.Date(triggerAt)}")

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (alarmManager.canScheduleExactAlarms()) {
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent
                )
            } else {
                // Fallback: inexact alarm (±22 min window)
                Log.w(TAG, "Exact alarm permission not granted — using inexact alarm")
                alarmManager.setAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent
                )
            }
        } else {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent
            )
        }
    }

    fun cancel() {
        alarmManager.cancel(pendingIntent)
        Log.d(TAG, "News alarm cancelled")
    }

    private fun nextHourMillis(): Long {
        return Calendar.getInstance().apply {
            add(Calendar.HOUR_OF_DAY, 1)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }.timeInMillis
    }

    companion object {
        private const val REQUEST_CODE = 42
    }
}
