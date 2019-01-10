import unittest
from filtering import generate_exchange_ranges, run_area_opf, \
    run_area_opf_with_exchange, find_initial_exchange

class TestExchangeRangeGenerator(unittest.TestCase):

    def test_find_first_limit(self):
        ATC_list = {('NO1', 'NO2'): 20, ('NO2', 'NO1'): 10}
        home_area = 'NO1'
        expected = -10
        actual = generate_exchange_ranges(ATC_list)[home_area,'NO2'][0]
        self.assertEqual(expected, actual)

    def test_find_range(self):
        ATC_list = {('NO1', 'NO2'): 20, ('NO2', 'NO1'): 10, ('SE3', 'NO1'): 30,
                    ('NO1', 'SE3'): 50}
        home_area = 'NO1'
        expected = [-30, 50]
        actual = generate_exchange_ranges(ATC_list)[home_area,'SE3']
        self.assertEqual(expected, actual)

class TestRunAreaOPF(unittest.TestCase):

    def test_cost_outome(self):
        expected = 125948
        actual = round(run_area_opf('all')['f'])
        self.assertEqual(expected, actual)

    def test_cost_zone1(self):
        expected = 32040
        actual = round(run_area_opf('zone1')['f'])
        self.assertEqual(expected, actual)

class TestRunAreaOPFwithExchange(unittest.TestCase):
    def test_cost_outcome(self):
        expected = 30959
        actual = round(run_area_opf_with_exchange('zone1', find_initial_exchange())['f'])
        self.assertEqual(expected, actual)

class TestFindInitialExchange(unittest.TestCase):

    def test_exchange_volume(self):
        expected = 48
        actual = round(find_initial_exchange()['zone1','zone2'])
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
