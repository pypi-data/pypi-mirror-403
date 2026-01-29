#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Omnix System
# Copyright (c) 2008-2025 Hive Solutions Lda.
#
# This file is part of Hive Omnix System.
#
# Hive Omnix System is free software: you can redistribute it and/or modify
# it under the terms of the Apache License as published by the Apache
# Foundation, either version 2.0 of the License, or (at your option) any
# later version.
#
# Hive Omnix System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License for more details.
#
# You should have received a copy of the Apache License along with
# Hive Omnix System. If not, see <http://www.apache.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__copyright__ = "Copyright (c) 2008-2025 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "Apache License, Version 2.0"
""" The license for the module """

import calendar
import datetime
import unittest

import omnix


class BusinessTest(unittest.TestCase):

    def test_get_comparison_day(self):
        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=2, day=28, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=2, day=28, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="day", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 28)
        self.assertEqual(current_v["unit"], "day")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 28)
        self.assertEqual(previous_v["unit"], "day")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=3, day=1, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="day", offset=0, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 1)
        self.assertEqual(current_v["unit"], "day")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 1)
        self.assertEqual(previous_v["unit"], "day")
        self.assertEqual(previous_v["has_global"], True)

    def test_get_comparison_day_leap(self):
        timestamp = calendar.timegm(
            datetime.datetime(year=2020, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2020, month=2, day=29, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2019, month=2, day=28, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="day", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 29)
        self.assertEqual(current_v["unit"], "day")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 28)
        self.assertEqual(previous_v["unit"], "day")
        self.assertEqual(previous_v["has_global"], True)

    def test_get_comparison_month(self):
        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=2, day=28, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=2, day=28, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 2)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 2)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=3, day=1, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=0, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 3)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 3)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=2, day=25, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=2, day=25, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-4, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 2)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 2)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=4, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=3, day=31, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=3, day=31, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 3)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 3)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=1, day=2, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=1, day=1, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=1, day=1, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 1)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 1)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=2, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=1, day=31, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=1, day=31, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 1)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 1)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=2, day=2, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2018, month=1, day=31, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2017, month=1, day=31, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-2, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 1)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 1)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

        timestamp = calendar.timegm(
            datetime.datetime(year=2018, month=1, day=2, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2017, month=12, day=31, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2016, month=12, day=31, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-2, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 12)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 12)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

    def test_get_comparison_month_leap(self):
        timestamp = calendar.timegm(
            datetime.datetime(year=2020, month=3, day=1, hour=4).utctimetuple()
        )
        current = calendar.timegm(
            datetime.datetime(year=2020, month=2, day=29, hour=4).utctimetuple()
        )
        previous = calendar.timegm(
            datetime.datetime(year=2019, month=2, day=28, hour=4).utctimetuple()
        )
        current_v, previous_v = omnix.calc_comparison(
            unit="month", offset=-1, timestamp=timestamp
        )

        self.assertEqual(current_v["date"], current)
        self.assertEqual(current_v["span"], 2)
        self.assertEqual(current_v["unit"], "month")
        self.assertEqual(current_v["has_global"], True)

        self.assertEqual(previous_v["date"], previous)
        self.assertEqual(previous_v["span"], 2)
        self.assertEqual(previous_v["unit"], "month")
        self.assertEqual(previous_v["has_global"], True)

    def test_sum_results_basic(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
            )
        )
        second = dict(
            store_1=dict(
                number_entries=dict(current=20, previous=10),
                net_price_vat=dict(current=200.0, previous=100.0),
            )
        )

        result = omnix.sum_results(first, second, calc=False)

        self.assertEqual(result["store_1"]["number_entries"]["current"], 30)
        self.assertEqual(result["store_1"]["number_entries"]["previous"], 15)
        self.assertEqual(result["store_1"]["net_price_vat"]["current"], 300.0)
        self.assertEqual(result["store_1"]["net_price_vat"]["previous"], 150.0)

    def test_sum_results_type_preservation(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
            )
        )
        second = dict(
            store_1=dict(
                number_entries=dict(current=20, previous=10),
                net_price_vat=dict(current=200.0, previous=100.0),
            )
        )

        result = omnix.sum_results(first, second, calc=False)

        self.assertIsInstance(result["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["current"], float)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["previous"], float)

    def test_sum_results_missing_second(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
            )
        )
        second = dict()

        result = omnix.sum_results(first, second, calc=False)

        self.assertEqual(result["store_1"]["number_entries"]["current"], 10)
        self.assertEqual(result["store_1"]["number_entries"]["previous"], 5)
        self.assertEqual(result["store_1"]["net_price_vat"]["current"], 100.0)
        self.assertEqual(result["store_1"]["net_price_vat"]["previous"], 50.0)

        self.assertIsInstance(result["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["current"], float)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["previous"], float)

    def test_sum_results_multiple_stores(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
            ),
            store_2=dict(
                number_entries=dict(current=30, previous=15),
            ),
        )
        second = dict(
            store_1=dict(
                number_entries=dict(current=20, previous=10),
            ),
            store_2=dict(
                number_entries=dict(current=40, previous=20),
            ),
        )

        result = omnix.sum_results(first, second, calc=False)

        self.assertEqual(result["store_1"]["number_entries"]["current"], 30)
        self.assertEqual(result["store_1"]["number_entries"]["previous"], 15)
        self.assertEqual(result["store_2"]["number_entries"]["current"], 70)
        self.assertEqual(result["store_2"]["number_entries"]["previous"], 35)

    def test_sum_results_with_calc(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
                net_number_sales=dict(current=5, previous=3),
            ),
        )
        second = dict(
            store_1=dict(
                number_entries=dict(current=20, previous=10),
                net_price_vat=dict(current=200.0, previous=100.0),
                net_number_sales=dict(current=10, previous=5),
            ),
        )

        result = omnix.sum_results(first, second, calc=True)

        self.assertEqual(result["store_1"]["number_entries"]["current"], 30)
        self.assertEqual(result["store_1"]["number_entries"]["previous"], 15)
        self.assertEqual(result["store_1"]["number_entries"]["diff"], 15)

        self.assertIsInstance(result["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["diff"], int)

    def test_calc_results_type_preservation(self):
        results = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
                net_number_sales=dict(current=5, previous=3),
            ),
        )

        omnix.calc_extra(results)
        omnix.calc_results(results)

        self.assertIsInstance(results["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(results["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(results["store_1"]["number_entries"]["diff"], int)

        self.assertIsInstance(results["store_1"]["net_number_sales"]["current"], int)
        self.assertIsInstance(results["store_1"]["net_number_sales"]["previous"], int)
        self.assertIsInstance(results["store_1"]["net_number_sales"]["diff"], int)

        self.assertIsInstance(results["store_1"]["net_price_vat"]["current"], float)
        self.assertIsInstance(results["store_1"]["net_price_vat"]["previous"], float)
        self.assertIsInstance(results["store_1"]["net_price_vat"]["diff"], float)

    def test_calc_results_with_float_counts(self):
        # simulates the case where API returns floats for count fields
        # which can happen with JSON deserialization or database returns
        results = dict(
            store_1=dict(
                number_entries=dict(current=10.0, previous=5.0),
                net_price_vat=dict(current=100.0, previous=50.0),
                net_number_sales=dict(current=5.0, previous=3.0),
            ),
        )

        omnix.calc_extra(results)
        omnix.calc_results(results)

        # the diff should be usable with {:,d} format code
        # this will fail if diff is a float
        number_entries = results["store_1"]["number_entries"]
        net_number_sales = results["store_1"]["net_number_sales"]

        # this is what slack_sales does - it will raise ValueError
        # if current or diff are floats
        "{:,d} x / {:+,d} x ({:+,.2f} %)".format(
            int(number_entries["current"]),
            int(number_entries["diff"]),
            number_entries["percentage"],
        )
        "{:,d} x / {:+,d} x ({:+,.2f} %)".format(
            int(net_number_sales["current"]),
            int(net_number_sales["diff"]),
            net_number_sales["percentage"],
        )

    def test_empty_results_type_preservation(self):
        input_data = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
                net_number_sales=dict(current=5, previous=3),
            ),
        )

        from omnix.util.business import empty_results

        result = empty_results(input_data, calc=False)

        self.assertEqual(result["store_1"]["number_entries"]["current"], 0)
        self.assertEqual(result["store_1"]["number_entries"]["previous"], 0)
        self.assertEqual(result["store_1"]["net_price_vat"]["current"], 0.0)
        self.assertEqual(result["store_1"]["net_price_vat"]["previous"], 0.0)
        self.assertEqual(result["store_1"]["net_number_sales"]["current"], 0)
        self.assertEqual(result["store_1"]["net_number_sales"]["previous"], 0)

        self.assertIsInstance(result["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["current"], float)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["previous"], float)
        self.assertIsInstance(result["store_1"]["net_number_sales"]["current"], int)
        self.assertIsInstance(result["store_1"]["net_number_sales"]["previous"], int)

    def test_empty_results_then_sum_type_preservation(self):
        first = dict(
            store_1=dict(
                number_entries=dict(current=10, previous=5),
                net_price_vat=dict(current=100.0, previous=50.0),
                net_number_sales=dict(current=5, previous=3),
            ),
        )

        from omnix.util.business import empty_results

        empty = empty_results(first, calc=False)
        result = omnix.sum_results(empty, first, calc=True)

        self.assertIsInstance(result["store_1"]["number_entries"]["current"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["previous"], int)
        self.assertIsInstance(result["store_1"]["number_entries"]["diff"], int)

        self.assertIsInstance(result["store_1"]["net_number_sales"]["current"], int)
        self.assertIsInstance(result["store_1"]["net_number_sales"]["previous"], int)
        self.assertIsInstance(result["store_1"]["net_number_sales"]["diff"], int)

        self.assertIsInstance(result["store_1"]["net_price_vat"]["current"], float)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["previous"], float)
        self.assertIsInstance(result["store_1"]["net_price_vat"]["diff"], float)
