from datetime import datetime, time, timedelta


class TimeService:
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    # We take 9-4 as market open window to ensure any trades executed around 3:29 and post market are handled well.
    MARKET_START_TIME = time(9, 00, 00)  # 1s less to account for isAfter()
    MARKET_END_TIME = time(16, 00, 00)  # 1s more to account for isBefore()

    def is_amo(self):
        return not self.is_market_open_now()

    def is_market_open_now(self):
        return self.is_market_open(datetime.now())

    def is_after_market_window_open(self):
        now = datetime.now().time()
        return (time(16, 4, 59) < now < time(0, 0, 1)) or (time(4, 59, 59) < now < time(8, 58, 1))

    def is_market_open(self, dt: datetime):
        current_time = dt.time()
        return dt.weekday() not in [5, 6] and self.MARKET_START_TIME < current_time < self.MARKET_END_TIME

    def get_date_from_string_with_today_as_default(self, date_as_string: str):
        try:
            return datetime.strptime(date_as_string, TimeService.TIME_FORMAT)
        except ValueError:
            return datetime.now()

    def get_todays_date(self) -> str:
        # # Get current date
        # current_date = datetime.now().date()
        #
        # # Format the date as a string in 'YYYY-MM-DD' format
        # formatted_date = current_date.strftime('%Y-%m-%d')

        return self.get_past_date(0)

    def get_past_date(self, days_ago: int) -> str:
        # Calculate the date 'n' days ago
        target_date = datetime.now() - timedelta(days=days_ago)

        # Format the date as a string in 'YYYY-MM-DD' format
        formatted_date = target_date.strftime('%Y-%m-%d')
        return formatted_date

if __name__ == "__main__":
    # Example usage
    time_service = TimeService()
    print(time_service.is_market_open_now())
    print(time_service.is_after_market_window_open())
    print(time_service.is_market_open(datetime(2023, 1, 2, 9, 14, 59)))  # Monday
    print(time_service.is_market_open(datetime(2023, 1, 2, 9, 15, 1)))   # Monday
    print(time_service.is_market_open(datetime(2023, 1, 2, 15, 29, 59)))  # Monday
    print(time_service.is_market_open(datetime(2023, 1, 2, 15, 30, 0)))   # Monday
    print(time_service.is_market_open(datetime(2023, 1, 2, 15, 30, 1)))   # Monday
    print(time_service.is_market_open(datetime(2023, 1, 1, 10, 00, 0)))  # Sunday
    print(time_service.is_market_open(datetime(2022, 12, 31, 10, 00, 0)))  # Saturday
    print(time_service.get_date_from_string_with_today_as_default('2023-01-01 12:30:00'))
    print(f'today: {time_service.get_todays_date()}')
    print(f'yesterday :{time_service.get_past_date(1)}')
    print(f'a week ago :{time_service.get_past_date(7)}')

