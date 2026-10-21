#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Back action checks; widget checks also run when a GTK display is available."""
import datetime
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

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

    def test_action_returns_from_year_without_selected_day(self):
        self.app.mode = "year"
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


class MidnightTests(unittest.TestCase):
    def check_tick(self, before, after, mode, displayed, picked, expected, expected_pick):
        app = Calendar()
        app.back_btn = Mock()
        app.shown_today = before
        app.year, app.month = displayed
        app.mode, app.picked = mode, picked
        # Keep the real redraw and back-state logic without needing a display.
        with patch.object(calendar["datetime"], "date") as clock, \
                patch.object(app, "show_month", side_effect=app.update_back) as month, \
                patch.object(app, "show_year", side_effect=app.update_back) as year:
            clock.today.return_value = after
            self.assertTrue(app.tick())
        self.assertEqual((app.year, app.month), expected)
        self.assertEqual(app.picked, expected_pick)
        self.assertEqual(app.mode, mode)
        (month if mode == "month" else year).assert_called_once_with()
        (year if mode == "month" else month).assert_not_called()
        enabled = mode == "year" or expected_pick is not None
        self.assertEqual(app.back_action.get_enabled(), enabled)
        app.back_btn.set_visible.assert_called_once_with(enabled)

    def test_month_and_year_rollover(self):
        for before, after in (
            (datetime.date(2026, 10, 31), datetime.date(2026, 11, 1)),
            (datetime.date(2026, 12, 31), datetime.date(2027, 1, 1)),
        ):
            for mode in ("month", "year"):
                for picked in (None, before):
                    with self.subTest(before=before, mode=mode, picked=picked):
                        self.check_tick(before, after, mode,
                                        (before.year, before.month), picked,
                                        (after.year, after.month), None)

    def test_browsed_month_is_preserved(self):
        for before, after in (
            (datetime.date(2026, 10, 31), datetime.date(2026, 11, 1)),
            (datetime.date(2026, 12, 31), datetime.date(2027, 1, 1)),
        ):
            for mode in ("month", "year"):
                for picked in (None, datetime.date(2025, 3, 15)):
                    with self.subTest(before=before, mode=mode, picked=picked):
                        self.check_tick(before, after, mode, (2025, 3), picked,
                                        (2025, 3), picked)

    def test_same_month_preserves_selected_day(self):
        before = datetime.date(2026, 10, 21)
        self.check_tick(before, datetime.date(2026, 10, 22), "month",
                        (2026, 10), before, (2026, 10), before)

    def test_same_day_does_not_redraw(self):
        app = Calendar()
        app.shown_today = datetime.date.today()
        with patch.object(app, "redraw") as redraw:
            self.assertTrue(app.tick())
        redraw.assert_not_called()


@unittest.skipUnless(Gtk.init_check()[0], "GTK display required")
class BackWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # GLib registers one GApplication per process, so all the checks share
        # one Calendar. Without an application id it stays off the session
        # bus and cannot meet a running Calendar.
        cls.app = Calendar()
        cls.app.set_application_id(None)
        if not cls.app.register(None):
            raise RuntimeError("the Calendar did not register")
        with patch.object(calendar["GLib"], "timeout_add_seconds"):
            cls.app.activate()
        cls.action = cls.app.lookup_action("back")

    @classmethod
    def tearDownClass(cls):
        cls.app.win.destroy()

    def setUp(self):
        # Every check starts on the root screen: this month, no day picked.
        today = datetime.date.today()
        self.app.year, self.app.month = today.year, today.month
        self.app.picked = None
        self.app.show_month()

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
