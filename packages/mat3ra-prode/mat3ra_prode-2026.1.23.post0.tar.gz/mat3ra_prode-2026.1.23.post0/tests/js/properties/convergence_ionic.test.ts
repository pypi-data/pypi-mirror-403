import type { ConvergenceIonicPropertySchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import ConvergenceIonicProperty from "../../../src/js/properties/non-scalar/convergence/ConvergenceIonicProperty";
import { PropertyName, PropertyType } from "../../../src/js/settings";

describe("ConvergenceIonicProperty", () => {
    it("should create a convergence ionic property", () => {
        const config: Omit<ConvergenceIonicPropertySchema, "name"> = {
            units: "eV",
            data: [{ energy: -100.5 }, { energy: -100.6 }],
        };

        const property = new ConvergenceIonicProperty(config);

        expect(property).to.be.instanceOf(ConvergenceIonicProperty);
        expect(ConvergenceIonicProperty.propertyType).equal(PropertyType.non_scalar);
        expect(ConvergenceIonicProperty.propertyName).equal(PropertyName.convergence_ionic);
    });
});
