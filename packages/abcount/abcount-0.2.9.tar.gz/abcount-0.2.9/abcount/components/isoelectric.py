import logging

from abcount.model.common import PKaAttribute
from abcount.model.isoelectric import NetCharge
from abcount.model.isoelectric import pH

logger = logging.getLogger(__name__)


class pIPredictor:
    @staticmethod
    def predict_input(
        pka_dict: dict, pka_attribute_cls=PKaAttribute, rounding_digits=2
    ):
        if not pIPredictor.any_pkas(pka_dict, pka_attribute_cls):
            return None
        result = pIPredictor._predict_exact(
            pka_dict, pka_attribute_cls=pka_attribute_cls
        )
        return round(result, rounding_digits)

    @staticmethod
    def _predict_exact(pka_dict, pka_attribute_cls=PKaAttribute):
        # The pI is the pH where the net charge is zero.
        # Bisect only works when charges cross zero:
        # If neutrality lies between two pKa values, pI is their average.
        # If neutrality occurs at a single pKa boundary, pI equals that pKa:
        # Just take the bound on either acidic or basic
        if pIPredictor._q_interval_crosses_zero(
            *pIPredictor._predict_initial_q_bounds(pka_dict, pka_attribute_cls)
        ):
            return pIPredictor._predict_by_bisect(
                pka_dict, pka_attribute_cls=pka_attribute_cls
            )
        else:
            return pIPredictor._predict_by_bound(pka_dict, pka_attribute_cls)

    @staticmethod
    def any_pkas(pka_dict, __pka_attribute_cls__):
        pka_attributes = [
            __pka_attribute_cls__.ACID_1,
            __pka_attribute_cls__.ACID_2,
            __pka_attribute_cls__.BASE_1,
            __pka_attribute_cls__.BASE_2,
        ]
        return any([pka_dict[attr] for attr in pka_attributes])

    @staticmethod
    def _predict_by_bound(pka_dict: dict, pka_attribute_cls=PKaAttribute):
        return BoundRetriever(pka_attribute_cls).retrieve_bound(pka_dict)

    @staticmethod
    def _predict_by_bisect(pka_dict: dict, pka_attribute_cls=PKaAttribute):
        """Compute pI by finding pH where net charge = 0 using bisection.
        https://en.wikipedia.org/wiki/Bisection_method"""
        low, high = pIPredictor._initialise_low_and_high_pkas()
        q_low, q_high = pIPredictor._predict_initial_q_bounds(
            pka_dict, pka_attribute_cls
        )

        # this must be negative because of basic env
        # we assume that the interval crosses zero
        # otherwise, we cannot apply the bisect method
        if not pIPredictor._q_interval_crosses_zero(q_low, q_high):
            raise ValueError(f"Net charge does not cross zero in [{low}, {high}]")

        while (high - low) > 1e-4:  # tolerance for iteration
            mid = (low + high) / 2
            q_mid = NetChargeCalculator(pka_attribute_cls).calculate_at_pH(
                pka_dict, pH=pH(mid)
            )
            logger.debug(
                {
                    "low pH": low,
                    "mid pH": mid,
                    "high pH": high,
                    "q_low": q_low,
                    "q_mid": q_mid,
                    "q_high": q_high,
                }
            )

            if q_mid == 0:
                return mid

            # apply the bisect
            # reduce interval by probing which direction to go using q_mid.
            # q_low is positive (acidic environment protonates centres +1)
            # if q_mid is positive, reduce low interval (positive charge)
            elif q_mid > 0:
                low = mid
                q_low = q_mid
            # q_high is negative (basic environment deprotonates centres -1)
            # if q_mid is negative, reduce high interval (negative charge)
            elif q_mid < 0:
                high = mid
                q_high = q_mid

        return 0.5 * (low + high)

    @staticmethod
    def _initialise_low_and_high_pkas():
        return 0.0, 14.0

    @staticmethod
    def _predict_initial_q_bounds(pka_dict: dict, pka_attribute_cls=PKaAttribute):
        low, high = pIPredictor._initialise_low_and_high_pkas()

        q_low = NetChargeCalculator(pka_attribute_cls).calculate_at_pH(
            pka_dict, pH=pH(low)
        )  # this must be positive because of acidic env
        q_high = NetChargeCalculator(pka_attribute_cls).calculate_at_pH(
            pka_dict, pH=pH(high)
        )
        return q_low, q_high

    @staticmethod
    def _q_interval_crosses_zero(q1: float, q2: float) -> bool:
        # if multiplication is negative, then
        # the interval crosses 0
        return q1 * q2 < 0


class NetChargeCalculator:
    def __init__(self, pka_attribute_cls=PKaAttribute):
        self.__pka_attribute_cls__ = pka_attribute_cls
        self._set_attribute_lists()

    def _set_attribute_lists(self) -> None:
        self.acid_attribute_list = [
            self.__pka_attribute_cls__.ACID_1,
            self.__pka_attribute_cls__.ACID_2,
        ]
        self.base_attribute_list = [
            self.__pka_attribute_cls__.BASE_1,
            self.__pka_attribute_cls__.BASE_2,
        ]

    def calculate_at_pH(self, pka_dict: dict, pH: pH):
        nq = NetCharge()

        # Acidic charges
        for att in self.acid_attribute_list:
            pka_value = pka_dict[att]
            if pka_value:
                nq.add(ChargeCalculator.calculate_acid_charge(pka_value, pH.value))

        # Basic charges
        for att in self.base_attribute_list:
            pka_value = pka_dict[att]
            if pka_value:
                nq.add(ChargeCalculator.calculate_base_charge(pka_value, pH.value))
        return nq.value


class ChargeCalculator:
    """Calculates the fraction of protonated/deprotonated species based on
    pKa and pH."""

    ROUNDING_DIGITS = 5

    @staticmethod
    def calculate_acid_charge(pKa: float, pH: float) -> float:
        return round(-1.0 / (1.0 + 10 ** (pKa - pH)), ChargeCalculator.ROUNDING_DIGITS)

    @staticmethod
    def calculate_base_charge(pKa: float, pH: float) -> float:
        return round(1.0 / (1.0 + 10 ** (pH - pKa)), ChargeCalculator.ROUNDING_DIGITS)


class BoundRetriever:
    """Determine bound of either acidic or basic pKas in a dictionary."""

    def __init__(self, pka_attribute_cls=PKaAttribute):
        self.__pka_attribute_cls__ = pka_attribute_cls
        self._set_attribute_lists()

    def _set_attribute_lists(self) -> None:
        self.acid_attribute_list = [
            self.__pka_attribute_cls__.ACID_1,
            self.__pka_attribute_cls__.ACID_2,
        ]
        self.base_attribute_list = [
            self.__pka_attribute_cls__.BASE_1,
            self.__pka_attribute_cls__.BASE_2,
        ]

    def retrieve_bound(self, pka_dict: dict):
        acidic_pkas = [
            pka_dict[att]
            for att in self.acid_attribute_list
            if pka_dict[att] is not None
        ]
        basic_pkas = [
            pka_dict[att]
            for att in self.base_attribute_list
            if pka_dict[att] is not None
        ]
        if acidic_pkas and basic_pkas:
            raise ValueError(
                f"Both acidic and basic pKas found. Cannot determine bound. (got {pka_dict})"
            )
        elif acidic_pkas:
            return min(acidic_pkas)
        elif basic_pkas:
            return max(basic_pkas)
        raise ValueError(f"(got {pka_dict})")


if __name__ == "__main__":
    # Test
    example = {
        "pka_acid1": 3,
        "pka_acid2": 5.5,
        "pka_base1": None,
        "pka_base2": None,
    }
    print(pIPredictor.predict_input(example))
