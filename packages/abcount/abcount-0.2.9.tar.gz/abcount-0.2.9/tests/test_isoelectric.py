import math

from abcount import PKaClassBuilder
from abcount.components.isoelectric import ChargeCalculator
from abcount.components.isoelectric import NetChargeCalculator
from abcount.components.isoelectric import pIPredictor
from abcount.model.isoelectric import pH


def test_pI_predict_mono():
    example = {
        "pka_acid1": 3,
        "pka_acid2": None,
        "pka_base1": 12,
        "pka_base2": None,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 7.5, abs_tol=1e-1)


def test_pI_predict_diacid():
    example = {
        "pka_acid1": 3,
        "pka_acid2": 5.5,
        "pka_base1": None,
        "pka_base2": None,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 3, abs_tol=1e-1)


def test_pI_predict_dibasic():
    example = {
        "pka_acid1": None,
        "pka_acid2": None,
        "pka_base1": 12,
        "pka_base2": 8.5,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 12, abs_tol=1e-1)


def test_pI_predict_di_and_mono():
    example = {
        "pka_acid1": 3,
        "pka_acid2": None,
        "pka_base1": 12,
        "pka_base2": 8.5,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 10.25, abs_tol=1e-1)


def test_pI_predict_di_di_custom():
    CustomPKaAttribute = PKaClassBuilder.build(
        ACID_1="my_pka_acid1",
        BASE_1="my_pka_base1",
        ACID_2="my_pka_acid2",
        BASE_2="my_pka_base2",
    )
    example = {
        "my_pka_acid1": 3,
        "my_pka_base1": 5.5,
        "my_pka_acid2": 12,
        "my_pka_base2": 8.5,
    }
    pI = pIPredictor.predict_input(example, CustomPKaAttribute)
    assert math.isclose(pI, 7, abs_tol=1e-1)


def test_pI_predict_di_di():
    example = {
        "pka_acid1": 3,
        "pka_acid2": 5.5,
        "pka_base1": 12,
        "pka_base2": 8.5,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 7, abs_tol=1e-1)


def test_pI_predict_weak_leaking():
    example = {
        "pka_acid1": 10,
        "pka_acid2": None,
        "pka_base1": 2.4,
        "pka_base2": 2.3,
    }
    pI = pIPredictor.predict_input(example)
    assert math.isclose(pI, 6.33, abs_tol=1e-1)


def test_netcharge_calc():
    example = {
        "pka_acid1": 3,
        "pka_acid2": None,
        "pka_base1": 11,
        "pka_base2": None,
    }
    nq = NetChargeCalculator().calculate_at_pH(example, pH=pH(7.4))
    assert math.isclose(nq, 0.0, abs_tol=1e-2)


def test_no_groups():
    example = {
        "pka_acid1": None,
        "pka_acid2": None,
        "pka_base1": None,
        "pka_base2": None,
    }
    pI = pIPredictor.predict_input(example)
    assert pI is None


def test_netcharge_custom_calc():
    example = {"pka_1": 3, "pka_2": None, "pkb_1": 11, "pkb_2": None}
    CustomPKaAttribute = PKaClassBuilder.build(
        ACID_1="pka_1", ACID_2="pka_2", BASE_1="pkb_1", BASE_2="pkb_2"
    )
    nq = NetChargeCalculator(CustomPKaAttribute).calculate_at_pH(example, pH=pH(7.4))
    assert math.isclose(nq, 0.0, abs_tol=1e-2)


def test_acid_charge_half_species():
    q = ChargeCalculator.calculate_acid_charge(pKa=7.4, pH=7.4)
    assert math.isclose(q, -0.5, abs_tol=1e-2)


def test_acid_charge_proto_species():
    q = ChargeCalculator.calculate_acid_charge(pKa=3, pH=7.4)
    assert math.isclose(q, -1.0, abs_tol=1e-2)


def test_acid_charge_deproto_species():
    q = ChargeCalculator.calculate_acid_charge(pKa=11, pH=7.4)
    assert math.isclose(q, 0.0, abs_tol=1e-2)


def test_base_charge_half_species():
    q = ChargeCalculator.calculate_base_charge(pKa=7.4, pH=7.4)
    assert math.isclose(q, 0.5, abs_tol=1e-2)


def test_base_charge_proto_species():
    q = ChargeCalculator.calculate_base_charge(pKa=11, pH=7.4)
    assert math.isclose(q, 1.0, abs_tol=1e-2)


def test_base_charge_deproto_species():
    q = ChargeCalculator.calculate_base_charge(pKa=3, pH=7.4)
    assert math.isclose(q, 0.0, abs_tol=1e-2)
