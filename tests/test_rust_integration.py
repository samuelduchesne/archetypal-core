import unittest
from archetypal_core.rust.idf_parser import IDF as RustIDF

class TestRustIntegration(unittest.TestCase):
    def test_idf_parsing(self):
        file_path = "/Applications/EnergyPlus-23-1-0/ExampleFiles/RefBldgMediumOfficeNew2004_Chicago_epJSON.epJSON"
        rust_idf = RustIDF(file_path)
        data = rust_idf.get_data()
        self.assertIsInstance(data, str)
        self.assertIn("Building", data)

if __name__ == "__main__":
    unittest.main()
