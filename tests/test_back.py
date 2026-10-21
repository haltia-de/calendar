#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Back action checks; widget checks also run when a GTK display is available."""
import datetime
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch
import uuid

calendar = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "haltia-calendar"),
    run_name="haltia_calendar",
)
Calendar = calendar["Calendar"]
Gtk = calendar["Gtk"]


class BackActionTests(unittest.TestCase):
    def setUp(self):
        self.app = Calendar()
        self.action = self.app.lookup_action("back")
        self.app.back_btn = Mock()

    def test_root_action_is_disabled_at_construction(self):
        self.assertIsNotNone(self.action)
        self.assertFalse(self.action.get_enabled())

    def test_back_state_for_each_screen(self):
        for mode, picked, enabled in (
            ("month", None, False),
            ("month", datetime.date(2026, 10, 21), True),
            ("year", None, True),
            ("year", datetime.date(2026, 10, 21), True),
        ):
            with self.subTest(mode=mode, picked=picked):
                self.app.mode, self.app.picked = mode, picked
                self.app.update_back()
                self.assertEqual(self.action.get_enabled(), enabled)
                self.app.back_btn.set_visible.assert_called_with(enabled)

    def test_disabled_action_does_not_navigate(self):
        with patch.object(self.app, "show_month") as show_month:
            self.action.activate(None)
            show_month.assert_not_called()

    def test_action_clears_selected_day(self):
        self.app.picked = datetime.date(2026, 10, 21)
        self.app.update_back()
        with patch.object(self.app, "show_month") as show_month:
            self.action.activate(None)
            self.assertIsNone(self.app.picked)
            show_month.assert_called_once_with()

    def test_action_returns_from_year_preserving_selected_day(self):
        self.app.mode = "year"
        self.app.picked = datetime.date(2026, 10, 21)
        self.app.update_back()
        with patch.object(self.app, "show_month") as show_month:
            self.action.activate(None)
            self.assertEqual(self.app.picked, datetime.date(2026, 10, 21))
            show_month.assert_called_once_with()


@unittest.skipUnless(Gtk.init_check()[0], "GTK display required")
class BackWidgetTests(unittest.TestCase):
    def setUp(self):
        self.app = Calendar()
        # NON_UNIQUE still exports actions on the shared session bus. Each
        # instance needs its own object path, including across test methods.
        self.app.set_application_id("io.github.haltia_de.Calendar.Test" + uuid.uuid4().hex)
        self.app.set_flags(calendar["Gio"].ApplicationFlags.NON_UNIQUE)
        self.assertTrue(self.app.register(None))
        with patch.object(calendar["GLib"], "timeout_add_seconds"):
            self.app.activate()
        self.action = self.app.lookup_action("back")
        self.addCleanup(self.app.win.destroy)

    def assert_back(self, enabled):
        self.assertEqual(self.action.get_enabled(), enabled)
        self.assertEqual(self.app.back_btn.get_visible(), enabled)
        self.assertEqual(self.app.back_btn.get_sensitive(), enabled)

    def test_root_survives_show_all_and_disabled_activation(self):
        self.app.win.show_all()
        self.assert_back(False)
        self.action.activate(None)
        self.assertEqual(self.app.mode, "month")
        self.assertIsNone(self.app.picked)
        self.assert_back(False)

    def test_day_back_returns_to_month(self):
        self.app.pick(datetime.date(self.app.year, self.app.month, 15))
        self.assert_back(True)
        self.action.activate(None)
        self.assertIsNone(self.app.picked)
        self.assertEqual(self.app.mode, "month")
        self.assert_back(False)

    def test_year_back_returns_to_month(self):
        month = self.app.month
        self.app.show_year()
        self.assert_back(True)
        self.action.activate(None)
        self.assertEqual((self.app.mode, self.app.month), ("month", month))
        self.assert_back(False)

    def test_year_over_selected_day_takes_two_back_steps(self):
        day = datetime.date(self.app.year, self.app.month, 15)
        self.app.pick(day)
        self.app.show_year()
        self.assert_back(True)
        self.action.activate(None)
        self.assertEqual(self.app.mode, "month")
        self.assertEqual(self.app.picked, day)
        self.assert_back(True)
        self.action.activate(None)
        self.assertIsNone(self.app.picked)
        self.assert_back(False)

    def test_header_button_activates_application_action(self):
        self.assertEqual(self.app.back_btn.get_action_name(), "app.back")
        self.app.show_year()
        self.app.back_btn.clicked()
        self.assertEqual(self.app.mode, "month")
        self.assert_back(False)

    def test_navigation_updates_back_state(self):
        self.app.pick(datetime.date(self.app.year, self.app.month, 15))
        self.app.turn(1)
        self.assert_back(False)
        self.app.show_year()
        self.app.turn(1)
        self.assert_back(True)
        self.app.open_month(3)
        self.assert_back(False)
        self.app.go_today()
        self.assert_back(True)
        self.app.redraw()
        self.assert_back(True)
        self.action.activate(None)
        self.assert_back(False)

    def test_header_left_slot_contains_only_back(self):
        header = self.app.win.get_titlebar()
        start = [child for child in header.get_children()
                 if header.child_get_property(child, "pack-type") == Gtk.PackType.START]
        self.assertEqual(len(start), 1)
        slot = start[0]
        self.assertEqual(slot.get_size_request().width, 110)
        self.assertEqual(slot.get_children(), [self.app.back_btn])
        self.assertEqual(self.app.back_btn.get_label(), "←")
        self.assertEqual(header.get_decoration_layout(), ":close")


if __name__ == "__main__":
    unittest.main()
