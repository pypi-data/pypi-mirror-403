import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "current: As current ones")
    config.addinivalue_line("markers", "learning: As learning exercises")
    config.addinivalue_line("markers", "api: As using the Notion API")
    config.addinivalue_line("markers", "slow: As slow ones")
    config.addinivalue_line("markers", "minimum: 最低限やっておきたいテスト")
    config.addinivalue_line("markers", "all: 全てのテスト. -m allで実行すると自動的に付与される")


def pytest_collection_modifyitems(config, items):
    """apiマークがついているテストを自動的に除外する。ただし、-mオプションで指定された場合は除外しない。"""
    selected_marker = config.getoption("-m")  # -mで指定されたマークを取得

    for item in items:
        # "api" がマークされているかどうかを確認
        if "api" in item.keywords and (selected_marker is None or len(selected_marker) == 0):
            item.add_marker(pytest.mark.skip(reason="api マークがついているのでスキップ"))

        if "all" in selected_marker:
            item.add_marker(pytest.mark.all())
