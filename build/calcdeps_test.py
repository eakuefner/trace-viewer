#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import unittest

import calcdeps
import os

srcdir = os.path.join(os.path.dirname(__file__), "../src")

class ParseTests(unittest.TestCase):
  def test_parse_declaration_1(self):
    text = """// blahblahblah
base.defineModule('myModule')
      .stylesheet('myStylesheet')
      .dependsOn('dependency1', 'dependency2')
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals(["myStylesheet"], module.style_sheet_names);
    self.assertEquals(["dependency1", "dependency2"],
                      module.dependent_module_names);

  def test_parse_declaration_with_deps_and_stylesheet_swapped(self):
    text = """// blahblahblah
base.defineModule('myModule')
      .dependsOn('dependency1', 'dependency2')
      .stylesheet('myStylesheet')
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals(["myStylesheet"], module.style_sheet_names);
    self.assertEquals(["dependency1", "dependency2"],
                      module.dependent_module_names);

  def test_parse_empty_declaration(self):
    text = """// blahblahblah
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text, decl_required = False)
    self.assertEquals([], module.style_sheet_names);
    self.assertEquals([], module.dependent_module_names);

  def test_parse_empty_depends_declaration(self):
    text = """// blahblahblah
base.defineModule('myModule')
      .dependsOn()
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals([], module.style_sheet_names);
    self.assertEquals([], module.dependent_module_names);

  def test_parse_empty_depends_declaration_2(self):
    text = """// blahblahblah
base.defineModule('myModule')
      .dependsOn()
      .exportsTo("x", function() {
      });
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals([], module.style_sheet_names);
    self.assertEquals([], module.dependent_module_names);

  def test_parse_declaration_2(self):
    text = """// blahblahblah
base.defineModule('myModule')
      .dependsOn("dependency1", 'dependency2')
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals([], module.style_sheet_names);
    self.assertEquals(["dependency1", "dependency2"], module.dependent_module_names);

  def test_parse_declaration_3(self):
    text = """// blahblahblah
base.defineModule("myModule").dependsOn('dependency1', 'dependency2')
"""
    module = calcdeps.Module("myModule")
    module.parse_declaration_(text)
    self.assertEquals([], module.style_sheet_names);
    self.assertEquals(["dependency1", "dependency2"], module.dependent_module_names);

  def test_parse_declaration_4(self):
    text = """// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

'use strict';

/**
 * @fileoverview TimelineView visualizes TRACE_EVENT events using the
 * tracing.Timeline component and adds in selection summary and control buttons.
 */
base.defineModule('timeline_view')
    .stylesheet('timeline_view')
    .dependsOn('timeline',
               'timeline_analysis',
               'overlay',
               'trace_event_importer',
               'linux_perf_importer')
    .exportsTo('tracing', function() {"""

    module = calcdeps.Module()
    module.parse_declaration_(text)
    self.assertEquals("timeline_view", module.name)
    self.assertEquals(["timeline_view"], module.style_sheet_names);
    self.assertEquals(["timeline",
                       "timeline_analysis",
                       "overlay",
                       "trace_event_importer",
                       "linux_perf_importer"], module.dependent_module_names);

class ResourceFinderStub(object):
  def __init__(self):
    self.modules = {}

  def add_module(self, name, filename, contents):
    module = {"filename": filename,
              "contents": contents}
    self.modules[name] = module

  def find_and_load_module(self, current_module, requested_module_name):
    if requested_module_name not in self.modules:
      return None
    return self.modules[requested_module_name]["filename"], self.modules[requested_module_name]["contents"]


x_contents = """
base.defineModule("x")
    .dependsOn("y", "z")
    .exportsTo("xyz", function() { });
"""

y_contents = """
base.defineModule("y")
    .dependsOn("z")
    .exportsTo("xyz", function() { });
"""

z_contents = """
base.defineModule("z")
    .exportsTo("xyz", function() { });
"""

class FlattenTests(unittest.TestCase):
  def test_module(self):
    resource_finder = ResourceFinderStub()
    resource_finder.add_module("y", "y.js", y_contents);
    resource_finder.add_module("z", "z.js", z_contents);

    x_module = calcdeps.Module("x")
    x_module.load_and_parse("x.js", x_contents)

    all_resources = {}
    x_module.resolve(all_resources, resource_finder)

    self.assertEquals([all_resources["scripts"]["y"], all_resources["scripts"]["z"]], x_module.dependent_modules)

    already_loaded_set = set()
    load_sequence = []
    x_module.compute_load_sequence_recursive(load_sequence, already_loaded_set)

    self.assertEquals([all_resources["scripts"]["z"], all_resources["scripts"]["y"], x_module], load_sequence)

class ResourceFinderTest(unittest.TestCase):
  def test_basic(self):

    resource_finder = calcdeps.ResourceFinder()
    module = calcdeps.Module("unittest")
    module.load_and_parse(os.path.join(srcdir, "unittest.js"))
    filename, contents = resource_finder.find_and_load_module(module, "base")

    assert filename

    same = os.path.samefile(os.path.join(srcdir, "base.js"), os.path.join(filename))
    self.assertTrue(same)

class CalcLoadSequenceTest(unittest.TestCase):
  def test_one_toplevel_nodeps(self):
    load_sequence = calcdeps.calc_load_sequence([os.path.join(srcdir, "unittest.js")])
    name_sequence = [x.name for x in load_sequence]
    self.assertEquals(["unittest"], name_sequence)

  def test_calc_load_sequence_two_toplevels(self): # tests that we resolve deps between toplevels
    pass

if __name__ == "__main__":
  unittest.main()