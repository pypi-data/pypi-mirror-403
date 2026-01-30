import os
import sys
import unittest
import io
import contextlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from civilutils.indian_standards.concrete import (
    ConcreteMixDesign,
    ConcreteGrade,
    MaximumNominalSize,
    MineralAdmixture,
    ChemicalAdmixture,
    ExposureCondition,
    SpecificGravity,
    FineAggregateZone,
    Materials,
)


class TestConcreteMixDesignExtra(unittest.TestCase):
    def setUp(self):
        self.sg_list = [
            SpecificGravity(Materials.CEMENT, 3.15),
            SpecificGravity(Materials.FINE_AGGREGATE, 2.60),
            SpecificGravity(Materials.COARSE_AGGREGATE, 2.70),
            SpecificGravity(Materials.WATER, 1.00),
            SpecificGravity(Materials.ADMIXTURE, 1.145),
        ]

    def test_specific_gravities_accepts_dict(self):
        sg_dict = {sg.material: sg for sg in self.sg_list}
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=sg_dict,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        self.assertIn(Materials.CEMENT, design.specific_gravities)
        self.assertAlmostEqual(design.specific_gravities[Materials.CEMENT].value, 3.15)

    def test_get_specific_gravity_missing_raises(self):
        # omit ADMIXTURE from list to provoke missing lookup
        sg_partial = [
            SpecificGravity(Materials.CEMENT, 3.15),
            SpecificGravity(Materials.FINE_AGGREGATE, 2.60),
            SpecificGravity(Materials.COARSE_AGGREGATE, 2.70),
            SpecificGravity(Materials.WATER, 1.00),
        ]
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M15,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=sg_partial,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        with self.assertRaises(Exception):
            # private method should raise when SG missing
            design._ConcreteMixDesign__get_specific_gravity(Materials.ADMIXTURE)

    def test_calculate_volume_based_on_mass_and_specific_gravity(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        vol = design.calculate_volume_based_on_mass_and_specific_gravity(1000.0, 2.0)
        # (1000 / 2) * 1/1000 = 0.5
        self.assertAlmostEqual(vol, 0.5)

    def test_slump_adjustment_increases_and_decreases_water_content(self):
        base = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
        )
        w_base = base._ConcreteMixDesign__calculate_water_content()

        higher_slump = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=75.0,
        )
        w_high = higher_slump._ConcreteMixDesign__calculate_water_content()
        self.assertGreaterEqual(w_high, w_base)

        lower_slump = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=25.0,
        )
        w_low = lower_slump._ConcreteMixDesign__calculate_water_content()
        self.assertLessEqual(w_low, w_base)

    def test_coarse_fine_proportions_for_zone_and_size(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_40,
            fine_aggregate_zone=FineAggregateZone.ZONE_IV,
            slump_mm=50.0,
        )
        # compute only aggregate related internals
        # some implementations compute aggregates inside compute_mix_design
        try:
            design.compute_mix_design(display_result=False)
        except Exception:
            # if compute_mix_design is not fully implemented, call the aggregate method directly
            design._ConcreteMixDesign__calculate_water_cement_ratio_by_is456()
            design._ConcreteMixDesign__calculate_water_content()
            design._ConcreteMixDesign__calculate_aggregate_content()
        cap = getattr(design, "coarse_aggregate_proportion", None)
        fap = getattr(design, "fine_aggregate_proportion", None)
        self.assertIsInstance(cap, float)
        self.assertIsInstance(fap, float)
        self.assertAlmostEqual(cap + fap, 1.0, places=6)
        self.assertGreaterEqual(cap, 0.0)
        self.assertLessEqual(cap, 1.0)

    def test_water_cement_ratio_plain_vs_reinforced(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M25,
            exposure_condition=ExposureCondition.SEVERE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        w_reinf = design._ConcreteMixDesign__calculate_water_cement_ratio_by_is456(reinforced=True)
        # call again for plain (non-reinforced)
        w_plain = design._ConcreteMixDesign__calculate_water_cement_ratio_by_is456(reinforced=False)
        # per IS mapping reinforced <= plain for same exposure
        self.assertLessEqual(w_reinf, w_plain)
        # specific expected values for SEVERE: plain 0.50, reinforced 0.45
        self.assertAlmostEqual(w_plain, 0.50, places=3)
        self.assertAlmostEqual(w_reinf, 0.45, places=3)

    def test_compute_mix_design_sets_expected_basic_attributes(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M25,
            exposure_condition=ExposureCondition.MODERATE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            mineral_admixture=None,
            fine_aggregate_zone=FineAggregateZone.ZONE_II
        )

        # run the mix design routine
        design.compute_mix_design(display_result=False)

        # target mean compressive strength for M25:
        # fck = 25, std dev = 4.0 -> target = 25 + 1.65*4 = 31.6
        self.assertAlmostEqual(getattr(design, "target_mean_compressive_strength"), 31.6, places=3, msg="Failed: target_mean_compressive_strength")

        # water/cement ratio for reinforced moderate exposure should be 0.50 (per IS456 mapping)
        self.assertAlmostEqual(getattr(design, "water_cement_ratio"), 0.50, places=5, msg="Failed: water_cement_ratio")

        # maximum water content for 20 mm nominal size with 50 mm slump should be 186 kg/m3
        self.assertAlmostEqual(getattr(design, "maximum_water_content"), 186.0, places=3, msg="Failed: maximum_water_content")

        # minimum cement content should be max(water_content/wcr, code_min). With 186/0.5 = 372
        self.assertAlmostEqual(getattr(design, "minimum_cement_content"), 372.0, places=3, msg="Failed: minimum_cement_content")

        # coarse + fine proportions should sum to 1.0
        cap = getattr(design, "coarse_aggregate_proportion")
        fap = getattr(design, "fine_aggregate_proportion")
        self.assertIsInstance(cap, float)
        self.assertIsInstance(fap, float)
        self.assertAlmostEqual(cap + fap, 1.0, places=6)

    def test_superplasticizer_reduces_water_content(self):
        # with same inputs but using superplasticizer, water content should reduce relative to base
        base = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            chemical_admixture=None,
        )
        base.compute_mix_design(display_result=False)
        base_water = getattr(base, "maximum_water_content")

        sp = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            chemical_admixture=ChemicalAdmixture.SUPERPLASTICIZER,
        )
        sp.compute_mix_design(display_result=False)
        sp_water = getattr(sp, "maximum_water_content")

        # superplasticizer should not increase water content; typically it reduces it
        self.assertLessEqual(sp_water, base_water)

    # --- New tests added below ------------------------------------------------

    def test_private_water_cement_ratio_prints_when_display_flag_set(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MODERATE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        # enable printing and capture stdout
        design._display_flag = True
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            design._ConcreteMixDesign__calculate_water_cement_ratio_by_is456(reinforced=True)
        out = buf.getvalue()
        self.assertIn("Water / Cement Ratio (IS456 Table 5)", out)
        self.assertIn("Calculated W/C", out)

    def test_compute_mix_design_prints_summary_when_requested(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M30,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ret = design.compute_mix_design(display_result=True)
        out = buf.getvalue()
        self.assertIn("Concrete Mix Design - Calculation Summary", out)
        # ensure compute_mix_design returned the expected top-level keys and total volume
        self.assertIsInstance(ret, dict)
        self.assertIn("mix_per_m3", ret)
        self.assertEqual(ret["mix_per_m3"]["total_concrete_volume_m3"], 1.0)

    def test_compute_mix_design_per_volume_prints_summary_when_requested(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M30,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        buf = io.StringIO()
        input_volume=5.0
        with contextlib.redirect_stdout(buf):
            ret = design.compute_mix_design_for_volume(volume_m3=input_volume, display_result=True)
        out = buf.getvalue()
        self.assertIn(f"Concrete Mix Design - Quantities for {input_volume:.3f} m^3", out)
        self.assertEqual(ret["mix_for_volume_m3"]["total_concrete_volume_m3"], input_volume)

    def test_mineral_admixture_default_and_override_percentage(self):
        # default percentage from enum should be used if no explicit percentage passed
        design_default = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            mineral_admixture=MineralAdmixture.FLY_ASH,
            mineral_admixture_percentage=None,
        )
        self.assertAlmostEqual(design_default.mineral_admixture_percentage, float(MineralAdmixture.FLY_ASH.default_percentage))

        # user provided percentage should override enum default
        design_override = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            mineral_admixture=MineralAdmixture.FLY_ASH,
            mineral_admixture_percentage=15.0,
        )
        self.assertAlmostEqual(design_override.mineral_admixture_percentage, 15.0)

    def test_compute_mix_design_return_contains_expected_structure_and_placeholders(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M25,
            exposure_condition=ExposureCondition.MODERATE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            mineral_admixture=None,
            fine_aggregate_zone=FineAggregateZone.ZONE_II
        )
        result = design.compute_mix_design(display_result=False)
        # verify top-level keys exist
        for k in ("summary", "mix_per_m3", "aggregate_adjustments_kg", "provenance"):
            self.assertIn(k, result)
        # ensure provenance contains expected fields
        prov = result["provenance"]
        self.assertIn("maximum_nominal_size_mm", prov)
        self.assertIn("fine_aggregate_zone", prov)
        self.assertIn("slump_mm", prov)
        # mix_per_m3 should indicate 1.0 m3 total
        self.assertEqual(result["mix_per_m3"]["total_concrete_volume_m3"], 1.0)

    # --- Tests for new volume-scaling API -------------------------------------

    def test_compute_mix_design_for_volume_scales_components(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M25,
            exposure_condition=ExposureCondition.MODERATE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            mineral_admixture=None,
            fine_aggregate_zone=FineAggregateZone.ZONE_II
        )
        base = design.compute_mix_design(display_result=False)
        scale = 2.5
        scaled = design.compute_mix_design_for_volume(scale, display_result=False)

        self.assertIn("mix_for_volume_m3", scaled)
        self.assertEqual(scaled["mix_for_volume_m3"]["total_concrete_volume_m3"], scale)

        base_components = base["mix_per_m3"]["components"]
        scaled_components = scaled["mix_for_volume_m3"]["components"]

        for name, comp in base_components.items():
            base_mass = comp.get("mass_kg", 0.0) or 0.0
            scaled_mass = scaled_components.get(name, {}).get("mass_kg", 0.0) or 0.0
            self.assertAlmostEqual(scaled_mass, base_mass * scale, places=6)

    def test_compute_mix_design_for_volume_invalid_volume_raises(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M20,
            exposure_condition=ExposureCondition.MILD,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
        )
        with self.assertRaises(ValueError):
            design.compute_mix_design_for_volume(0, display_result=False)

    def test_compute_mix_design_with_flyash_adjusts_cement_and_includes_flyash(self):
        design = ConcreteMixDesign(
            concrete_grade=ConcreteGrade.M25,
            exposure_condition=ExposureCondition.MODERATE,
            specific_gravities=self.sg_list,
            maximum_nominal_size=MaximumNominalSize.SIZE_20,
            slump_mm=50.0,
            mineral_admixture=MineralAdmixture.FLY_ASH,
            mineral_admixture_percentage=None,  # should pick up enum default (30%)
            fine_aggregate_zone=FineAggregateZone.ZONE_II
        )

        result = design.compute_mix_design(display_result=False)

        # enum default percentage should be applied
        self.assertAlmostEqual(design.mineral_admixture_percentage, float(MineralAdmixture.FLY_ASH.default_percentage))

        # fly ash calculation should have produced a positive fly_ash_content
        self.assertGreater(getattr(design, "fly_ash_content", 0.0), 0.0)

        # returned mix must include fly_ash component matching computed value
        components = result["mix_per_m3"]["components"]
        self.assertIn("fly_ash", components)
        self.assertAlmostEqual(components["fly_ash"]["mass_kg"], design.fly_ash_content, places=6)

        # cement in the mix should reflect the adjusted (post-replacement) cement content
        self.assertAlmostEqual(components["cement"]["mass_kg"], design.new_cement_content, places=6)
        # and the instance minimum_cement_content should have been updated to the new cement content
        self.assertAlmostEqual(design.minimum_cement_content, design.new_cement_content, places=6)


if __name__ == "__main__":
    unittest.main()
