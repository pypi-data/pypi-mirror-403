#                                         بسم الله الرحمن الرحیم
"""
اللَّهُمَّ صَلِّ عَلَى عَلِيِّ بْنِ مُوسَى الرِّضَا الْمُرْتَضَى

الْإِمَامِ التَّقِيِّ النَّقِي وَ حُجَّتِكَ عَلَى مَنْ فَوْقَ الْأَرْضِ

وَ مَنْ تَحْتَ الثَّرَى الصِّدِّيقِ الشَّهِيدِ

صَلاَةً كَثِيرَةً تَامَّةً زَاكِيَةً مُتَوَاصِلَةً مُتَوَاتِرَةً مُتَرَادِفَةً

كَأَفْضَلِ مَا صَلَّيْتَ عَلَى أَحَدٍ مِنْ أَوْلِيَائِكَ
"""
import datetime
import platform
import subprocess
import time
from typing import Self


class TP:
    """کلاس اصلی زمان - دقیقاً همون چیزی که خواستی"""

    def __init__(self, year: int, month: int, day: int,
                 hour: int = 0, minute: int = 0, second: int = 0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    @classmethod
    def now(cls) -> Self:
        """زمان فعلی سیستم به صورت TP"""
        return TPySys.local_time()

    @classmethod
    def utc_now(cls) -> Self:
        """زمان فعلی UTC به صورت TP"""
        return TPySys.utc_time()

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d} {self.hour:02d}:{self.minute:02d}:{self.second:02d}"

    def __repr__(self) -> str:
        return f"TP({self.year},{self.month},{self.day},{self.hour},{self.minute},{self.second})"

    def to_datetime(self) -> datetime.datetime:
        return datetime.datetime(self.year, self.month, self.day,
                                 self.hour, self.minute, self.second)

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> Self:
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    def add_seconds(self, seconds: int) -> Self:
        dt = self.to_datetime() + datetime.timedelta(seconds=seconds)
        return self.from_datetime(dt)

    def add_minutes(self, minutes: int) -> Self:
        return self.add_seconds(minutes * 60)

    def add_hours(self, hours: int) -> Self:
        return self.add_minutes(hours * 60)

    def add_days(self, days: int) -> Self:
        dt = self.to_datetime() + datetime.timedelta(days=days)
        return self.from_datetime(dt)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TP):
            return False
        return (self.year, self.month, self.day, self.hour, self.minute, self.second) == \
            (other.year, other.month, other.day, other.hour, other.minute, other.second)

    def __lt__(self, other: 'TP') -> bool:
        return self.to_datetime() < other.to_datetime()


class TPySys:
    """کلاس اصلی مدیریت زمان سیستم و جهانی"""

    @staticmethod
    def local_time() -> TP:
        """زمان فعلی سیستم (محلی)"""
        now = datetime.datetime.now()
        return TP.from_datetime(now)

    @staticmethod
    def utc_time() -> TP:
        """زمان فعلی جهانی UTC"""
        now = datetime.datetime.utcnow()
        return TP.from_datetime(now)

    @staticmethod
    def set_system_time(tp: TP, admin: bool = True) -> bool:
        """
        تغییر زمان سیستم - نیاز به اجرا با ادمین/سودو داره
        ویندوز و لینوکس رو ساپورت می‌کنه
        """
        time_str = f"{tp.year:04d}-{tp.month:02d}-{tp.day:02d} {tp.hour:02d}:{tp.minute:02d}:{tp.second:02d}"

        if platform.system() == "Windows":
            cmd = f'time {tp.hour:02d}:{tp.minute:02d}:{tp.second:02d}'
            cmd_date = f'date {tp.year:04d}-{tp.month:02d}-{tp.day:02d}'
            try:
                subprocess.run(cmd, shell=True, check=True)
                subprocess.run(cmd_date, shell=True, check=True)
                return True
            except:
                return False
        else:  # Linux / macOS
            cmd = f"sudo date -s '{time_str}'" if admin else f"date -s '{time_str}'"
            try:
                subprocess.run(cmd, shell=True, check=True)
                return True
            except:
                return False

    @staticmethod
    def sleep_until(tp: TP):
        """برنامه رو می‌خوابونه تا برسه به اون زمان"""
        target = tp.to_datetime()
        now = datetime.datetime.now()
        if target > now:
            seconds = (target - now).total_seconds()
            time.sleep(seconds)

    @staticmethod
    def timestamp() -> float:
        """تایم‌استمپ یونیکس فعلی"""
        return time.time()

    @staticmethod
    def system_timezone() -> str:
        """اسم تایم‌زون سیستم"""
        return time.tzname[0]

    @staticmethod
    def is_dst() -> bool:
        """آیا الان daylight saving فعاله؟"""
        return bool(time.daylight)

    @staticmethod
    def format(tp: TP, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """فرمت دلخواه - مثل strftime"""
        return tp.to_datetime().strftime(fmt)

