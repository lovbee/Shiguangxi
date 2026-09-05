package com.quanxiaoha.framework.common.util;

import com.quanxiaoha.framework.common.constant.DateConstants;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.Objects;

/**
 * @author: 犬小哈
 * @url: www.quanxiaoha.com
 * @date: 2023-08-14 16:27
 * @description: 日期工具类
 **/
public class DateUtils {

    /**
     * LocalDateTime 转时间戳
     *
     * @param localDateTime
     * @return
     */
    public static long localDateTime2Timestamp(LocalDateTime localDateTime) {
        return localDateTime.toInstant(ZoneOffset.UTC).toEpochMilli();
    }

    /**
     * LocalDateTime 转 String 字符串
     * @param time
     * @return
     */
    public static String localDateTime2String(LocalDateTime time) {
        return time.format(DateConstants.DATE_FORMAT_Y_M_D_H_M_S);
    }

    /**
     * LocalDateTime 转 Date 字符串
     * @param time
     * @return
     */
    public static String parse2DateStr(LocalDateTime time) {
        if (Objects.isNull(time))
            return null;

        return time.format(DateConstants.DATE_FORMAT_Y_M_D);
    }

    /**
     * LocalDateTime 转友好的相对时间字符串
     * @param dateTime
     * @return
     */
    public static String formatRelativeTime(LocalDateTime dateTime) {
        // 当前时间
        LocalDateTime now = LocalDateTime.now();

        // 计算与当前时间的差距
        long daysDiff = ChronoUnit.DAYS.between(dateTime, now);
        long hoursDiff = ChronoUnit.HOURS.between(dateTime, now);
        long minutesDiff = ChronoUnit.MINUTES.between(dateTime, now);

        if (daysDiff < 1) {  // 如果是今天
            if (hoursDiff < 1) {  // 如果是几分钟前
                if (minutesDiff < 10) {
                    return "刚刚";
                } else {
                    return minutesDiff + " 分钟前";
                }
            } else {  // 如果是几小时前
                return hoursDiff + " 小时前";
            }
        } else if (daysDiff == 1) {  // 如果是昨天
            return "昨天 " + dateTime.format(DateConstants.DATE_FORMAT_H_M);
        } else if (daysDiff < 7) {  // 如果是最近一周
            return daysDiff + " 天前";
        } else if (dateTime.getYear() == now.getYear()) {  // 如果是今年
            return dateTime.format(DateConstants.DATE_FORMAT_M_D);
        } else {  // 如果是去年或更早
            return dateTime.format(DateConstants.DATE_FORMAT_Y_M_D);
        }
    }

    /**
     * 计算年龄
     *
     * @param birthDate 出生日期（LocalDate）
     * @return 计算得到的年龄（以年为单位）
     */
    public static int calculateAge(LocalDate birthDate) {
        // 获取当前日期
        LocalDate currentDate = LocalDate.now();

        // 计算出生日期到当前日期的 Period 对象
        Period period = Period.between(birthDate, currentDate);

        // 返回完整的年份（即年龄）
        return period.getYears();
    }

    public static void main(String[] args) {
        // // 测试示例
        // LocalDateTime dateTime1 = LocalDateTime.now().minusMinutes(10); // 10分钟前
        // LocalDateTime dateTime2 = LocalDateTime.now().minusHours(3); // 3小时前
        // LocalDateTime dateTime3 = LocalDateTime.now().minusDays(1).minusHours(5); // 昨天 20:12
        // LocalDateTime dateTime4 = LocalDateTime.now().minusDays(2); // 2天前
        // LocalDateTime dateTime5 = LocalDateTime.now().minusDays(10); // 11-06
        // LocalDateTime dateTime6 = LocalDateTime.of(2023, 12, 1, 12, 30, 0); // 2023-12-01
        //
        // System.out.println(formatRelativeTime(dateTime1)); // 输出 "10分钟前"
        // System.out.println(formatRelativeTime(dateTime2)); // 输出 "3小时前"
        // System.out.println(formatRelativeTime(dateTime3)); // 输出 "昨天 20:12"
        // System.out.println(formatRelativeTime(dateTime4)); // 输出 "2天前"
        // System.out.println(formatRelativeTime(dateTime5)); // 输出 "11-06"
        // System.out.println(formatRelativeTime(dateTime6)); // 输出 "2023-12-01"

    }
}
