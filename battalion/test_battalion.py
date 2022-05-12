import pytest
from battalion.main import battalion_main
from datetime import datetime

def test_battalion():
    battalion_main(datetime.now().strftime("battalion_%Y%m%d_%H%M%S_log.txt"), True)