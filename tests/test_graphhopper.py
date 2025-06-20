# -*- coding: utf-8 -*-
# Copyright (C) 2021 GIS OPS UG
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
"""Tests for the Graphhopper module."""

import json
from copy import deepcopy

import responses

import tests as _test
from routingpy import Graphhopper
from routingpy.direction import Direction, Directions
from routingpy.isochrone import Isochrone, Isochrones
from routingpy.matrix import Matrix
from routingpy.utils import decode_polyline5
from tests.data.mock import *


class GraphhopperTest(_test.TestCase):
    name = "graphhopper"

    def setUp(self):
        self.key = "sample_key"
        self.client = Graphhopper(api_key=self.key)

    @responses.activate
    def test_full_directions(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["directions"])
        query["algorithm"] = None
        query["fake_option"] = 42
        expected = deepcopy(ENDPOINTS_EXPECTED[self.name]["directions"])

        responses.add(
            responses.POST,
            "https://graphhopper.com/api/1/route",
            status=200,
            json=ENDPOINTS_RESPONSES[self.name]["directions"],
            content_type="application/json",
        )

        routes = self.client.directions(**query)
        self.assertEqual(1, len(responses.calls))
        self.assertEqual(json.loads(responses.calls[0].request.body.decode("utf-8")), expected)
        self.assertIsInstance(routes, Direction)
        self.assertIsInstance(routes.geometry, list)
        self.assertIsInstance(routes.duration, int)
        self.assertIsInstance(routes.distance, int)
        self.assertIsInstance(routes.raw, dict)

    @responses.activate
    def test_full_directions_alternatives(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["directions"])

        responses.add(
            responses.POST,
            "https://graphhopper.com/api/1/route",
            status=200,
            json=ENDPOINTS_RESPONSES[self.name]["directions"],
            content_type="application/json",
        )

        routes = self.client.directions(**query)
        self.assertEqual(1, len(responses.calls))
        self.assertIsInstance(routes, Directions)
        self.assertEqual(3, len(routes))
        self.assertIsInstance(routes[0], Direction)
        self.assertIsInstance(routes[0].geometry, list)
        self.assertIsInstance(routes[0].duration, int)
        self.assertIsInstance(routes[0].distance, int)
        self.assertIsInstance(routes[0].raw, dict)

    @responses.activate
    def test_full_directions_not_encoded(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["directions"])
        query["points_encoded"] = False
        query["algorithm"] = None

        res = ENDPOINTS_RESPONSES[self.name]["directions"]
        res["paths"][0]["points"] = dict(coordinates=decode_polyline5(res["paths"][0]["points"]))

        responses.add(
            responses.POST,
            "https://graphhopper.com/api/1/route",
            status=200,
            json=ENDPOINTS_RESPONSES[self.name]["directions"],
            content_type="application/json",
        )

        route = self.client.directions(**query)
        self.assertEqual(1, len(responses.calls))

        self.assertIsInstance(route, Direction)
        self.assertIsInstance(route.geometry, list)
        self.assertIsInstance(route.duration, int)
        self.assertIsInstance(route.distance, int)
        self.assertIsInstance(route.raw, dict)

    @responses.activate
    def test_full_isochrones(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["isochrones"])
        query["buckets"] = 3
        query["fake_option"] = 42

        responses.add(
            responses.GET,
            "https://graphhopper.com/api/1/isochrone",
            status=200,
            json=ENDPOINTS_RESPONSES[self.name]["isochrones"],
            content_type="application/json",
        )

        isochrones = self.client.isochrones(**query)
        self.assertEqual(1, len(responses.calls))
        self.assertURLEqual(
            "https://graphhopper.com/api/1/isochrone?buckets=3&debug=false&key=sample_key&"
            "point=48.23424%2C8.34234&profile=car&reverse_flow=true&time_limit=1000&type=json&fake_option=42",
            responses.calls[0].request.url,
        )

        self.assertIsInstance(isochrones, Isochrones)
        self.assertEqual(3, len(isochrones))
        self.assertIsInstance(isochrones.raw, dict)
        for iso in isochrones:
            self.assertIsInstance(iso, Isochrone)
            self.assertIsInstance(iso.geometry, list)
            self.assertIsInstance(iso.interval, int)
            self.assertIsInstance(iso.center, list)
            self.assertEqual(iso.interval_type, "time")

    @responses.activate
    def test_full_matrix(self):
        query = ENDPOINTS_QUERIES[self.name]["matrix"]
        query["fake_option"] = 42

        responses.add(
            responses.GET,
            "https://graphhopper.com/api/1/matrix",
            status=200,
            json=ENDPOINTS_RESPONSES[self.name]["matrix"],
            content_type="application/json",
        )

        matrix = self.client.matrix(**query)
        self.assertEqual(1, len(responses.calls))
        self.assertURLEqual(
            "https://graphhopper.com/api/1/matrix?key=sample_key&out_array=distances&out_array=times&out_array=weights&"
            "point=49.415776%2C8.680916&point=49.420577%2C8.688641&point=49.445776%2C8.780916&profile=car&debug=true&fake_option=42",
            responses.calls[0].request.url,
        )

        self.assertIsInstance(matrix, Matrix)
        self.assertIsInstance(matrix.durations, list)
        self.assertIsInstance(matrix.distances, list)
        self.assertIsInstance(matrix.raw, dict)

    @responses.activate
    def test_few_sources_destinations_matrix(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["matrix"])
        query["sources"] = [0, 1, 2]
        query["destinations"] = [0, 1, 2]

        responses.add(
            responses.GET,
            "https://graphhopper.com/api/1/matrix",
            status=200,
            json={},
            content_type="application/json",
        )
        self.client.matrix(**query)

        query["sources"] = None
        query["destinations"] = None

        responses.add(
            responses.GET,
            "https://graphhopper.com/api/1/matrix",
            status=200,
            json={},
            content_type="application/json",
        )

        self.client.matrix(**query)

        self.assertEqual(2, len(responses.calls))
        self.assertURLEqual(
            "https://graphhopper.com/api/1/matrix?from_point=49.415776%2C8.680916&from_point=49.420577%2C8.688641&"
            "from_point=49.445776%2C8.780916&key=sample_key&out_array=distances"
            "&out_array=times&out_array=weights&profile=car&to_point=49.415776%2C8.680916&to_point=49.420577%2C8.688641&"
            "&to_point=49.445776%2C8.780916&debug=true",
            responses.calls[0].request.url,
        )
        self.assertURLEqual(
            "https://graphhopper.com/api/1/matrix?point=49.415776%2C8.680916&point=49.420577%2C8.688641&"
            "point=49.445776%2C8.780916&key=sample_key&out_array=distances"
            "&out_array=times&out_array=weights&profile=car"
            "&debug=true",
            responses.calls[1].request.url,
        )

    def test_index_sources_matrix(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["matrix"])
        query["sources"] = [100]

        self.assertRaises(IndexError, lambda: self.client.matrix(**query))

    def test_index_destinations_matrix(self):
        query = deepcopy(ENDPOINTS_QUERIES[self.name]["matrix"])
        query["destinations"] = [100]

        self.assertRaises(IndexError, lambda: self.client.matrix(**query))
