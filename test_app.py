import os
import unittest
from app import app, UPLOAD_FOLDER, GIF_FOLDER

class VideoToGIFTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Video', response.data)

    def test_upload_video_no_file(self):
        response = self.app.post('/upload', data={})
        self.assertEqual(response.data, b'No file part')

    def test_upload_video_success(self):
        sample_video_path = 'sample_video.mp4'
        self.assertTrue(os.path.exists(sample_video_path), f"Sample video not found at {sample_video_path}")

        with open(sample_video_path, 'rb') as video:
            data = {'video': video}
            response = self.app.post('/upload', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'GIFs created successfully', response.data)
            self.assertGreater(len(os.listdir(GIF_FOLDER)), 0)

    def tearDown(self):
        # Clean up upload and gif folders
        for folder in [UPLOAD_FOLDER, GIF_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    try:
                        # Close the file first before deleting
                        with open(file_path, 'rb') as f:
                            pass
                    except PermissionError:
                        # If the file cannot be opened, it's likely already closed
                        pass
                    os.unlink(file_path)

if __name__ == '__main__':
    unittest.main()