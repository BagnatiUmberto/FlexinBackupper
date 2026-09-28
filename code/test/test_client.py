import configparser
import os
from threading import Event
from pathlib import Path
import unittest


from client.img_copier import ImgCopierManager
from client.paths import FLEXIN_DIR, CONFIG_DIR, LOG_DIR, ZIP_DIR, DATA_DIR

class TestClient(unittest.TestCase):
    def test_regman(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(CONFIG_DIR, "config.ini"))
        stop_event = Event()
        registry_manager = ImgCopierManager(config, stop_event)

        '''
        FUNC: SHOULD_SKIP_FOLDER
        '''
        registry_manager.last_completed = "202604081507"  
        result = registry_manager._should_skip_folder("202301010000", 30)
        self.assertTrue(result, "Folder should be skipped because it's older than 30 days")

        result = registry_manager._should_skip_folder("202604091507", 30)
        self.assertFalse(result, "Folder should not be skipped because it's not older than 30 days")

        '''
        FUNC: SCAN_AND_PARSE
        '''
        mock_folders = Path("C:\\Users\\bagnati.umberto\\Documents\\Projects\\Scambio Dati DB Flexin\\new code\\code\\test\\mock_folders\\202605031221")
        result = registry_manager._scan_and_parse(mock_folders)
        self.assertEqual(result[0]['img_name'], "202504241014-0", "Name should be equal")
        self.assertEqual(result[0]['year'], "2025", "Year should be equal")
        self.assertEqual(result[0]['month'], "04", "Month should be equal")
        self.assertEqual(result[0]['day'], "24", "Day should be equal")
        self.assertEqual(result[0]['hour'], "10", "Hour should be equal")
        self.assertEqual(result[0]['minute'], "14", "Minute should be equal")
        self.assertEqual(result[0]['img_id'], "0", "Id should be equal")


        


if __name__ == "__main__":
    unittest.main()