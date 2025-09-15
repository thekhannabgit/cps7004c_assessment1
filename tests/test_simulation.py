import unittest
from model.location import Location
from model.bridge import Bridge
from model.hero import ReedRichards, SueStorm, JohnnyStorm, BenGrimm
from model.silver_surfer import SilverSurfer
from model.galactus import GalactusProjection
from model.mars import Mars

class BaseSimTest(unittest.TestCase):

    def setUp(self):
        self.mars = Mars()
        self.centre = Location(self.mars.get_width() // 2,
                               self.mars.get_height() // 2)


# Bridge tests
class TestBridge(BaseSimTest):
    def test_bridge_repair_and_damage(self):
        bridge = Bridge(Location(1, 1), max_health=50)

        self.assertEqual(bridge.health, 0)
        self.assertFalse(bridge.is_complete())

        bridge.repair(30)
        self.assertEqual(bridge.health, 30)
        self.assertFalse(bridge.is_complete())

        bridge.repair(30)  # should cap at max_health
        self.assertTrue(bridge.is_complete())
        self.assertFalse(bridge.damaged)

        bridge.damage(20)
        self.assertEqual(bridge.health, 30)
        self.assertTrue(bridge.damaged)


# Hero tests
class TestHero(BaseSimTest):
    def test_hero_recharges_at_hq(self):
        hero = ReedRichards(Location(5, 5))
        hero.energy = 0
        hero.set_location(self.centre)

        hero.check_recharge(self.mars)
        self.assertGreater(hero.energy, 0, "Hero should recharge at HQ")

    def test_sue_moves_towards_bridge(self):
        # Place a bridge
        loc = Location(3, 3)
        bridge = Bridge(loc)
        self.mars.add_bridge(bridge)

        hero = SueStorm(Location(0, 0))
        hero.energy = hero.max_energy

        old_loc = hero.get_location()
        hero.act(self.mars)
        new_loc = hero.get_location()

        self.assertNotEqual((old_loc.get_x(), old_loc.get_y()),
                            (new_loc.get_x(), new_loc.get_y()),
                            "Sue should move towards a bridge when available")


# Silver Surfer tests
class TestSilverSurfer(BaseSimTest):
    def test_surfer_targets_only_undamaged_bridge(self):
        loc = Location(3, 3)
        bridge = Bridge(loc)
        self.mars.add_bridge(bridge)

        surfer = SilverSurfer(Location(0, 0))
        target = surfer.find_target_bridge(self.mars)
        self.assertEqual(target, bridge)

        # Damage the bridge: Surfer should skip it now
        bridge.damage(10)
        target2 = surfer.find_target_bridge(self.mars)
        self.assertIsNone(target2, "Surfer should ignore damaged bridges")


# Galactus tests
class TestGalactus(BaseSimTest):
    def test_galactus_eventually_moves_towards_franklin(self):
        start_loc = Location(5, 5)
        gal = GalactusProjection(start_loc, Location(0, 0))

        start = gal.get_location()
        moved = False

        # Allow up to 5 ticks in case of cooldown
        for _ in range(5):
            gal.act(self.mars)
            end = gal.get_location()
            if (end.get_x(), end.get_y()) != (start.get_x(), start.get_y()):
                moved = True
                break

        self.assertTrue(moved, "Galactus should eventually move towards Franklin")


# Environment wrap-around
class TestEnvironment(BaseSimTest):
    def test_wraparound_coordinates(self):
        w, h = self.mars.get_width(), self.mars.get_height()
        loc = Location(w, h)  # outside bounds
        wrapped = Location(0, 0)

        self.assertEqual((loc.get_x() % w, loc.get_y() % h),
                         (wrapped.get_x(), wrapped.get_y()),
                         "Location should wrap around grid size")


if __name__ == "__main__":
    unittest.main()