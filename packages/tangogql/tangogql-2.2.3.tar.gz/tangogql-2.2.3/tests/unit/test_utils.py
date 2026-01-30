from tangogql.utils import DbDeviceInfo


def test_dbdeviceinfo_broken_date_format():
    info = DbDeviceInfo(
        [
            "sys/tg_test/1",
            "some_alias",
            "1",
            "21908219821928",
            "some-host.maxiv.lu.se",
            "TangoTest/1",
            "123",
            "TangoTest",
            "7",
            "0000-00-00 00:00:00",
            "2024-01-01 17:16:15",
        ]
    )
    assert info.started is None
    assert info.stopped.year == 2024
