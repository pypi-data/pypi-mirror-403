import unittest
from sharer.server import ScreenSharer

class TestSharer(unittest.TestCase):
    def test_get_local_ip(self):
        sharer = ScreenSharer()
        ip = sharer.get_local_ip()
        self.assertIsNotNone(ip)
        self.assertNotEqual(ip, "")
    
    def test_initialization(self):
        sharer = ScreenSharer()
        self.assertEqual(sharer.port, 5000)
        self.assertIsNotNone(sharer.app)
        self.assertIsNotNone(sharer.socketio)

if __name__ == '__main__':
    unittest.main()