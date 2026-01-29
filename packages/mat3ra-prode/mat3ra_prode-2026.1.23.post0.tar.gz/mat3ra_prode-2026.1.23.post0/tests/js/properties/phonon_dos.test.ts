import type { PhononDensityOfStatesPropertySchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import PhononDOSProperty from "../../../src/js/properties/non-scalar/PhononDOSProperty";
import { PropertyName, PropertyType } from "../../../src/js/settings";

describe("PhononDOSProperty", () => {
    it("should create a phonon dos property with correct constructor, propertyType, and propertyName", () => {
        const config: Omit<PhononDensityOfStatesPropertySchema, "name"> = {
            xAxis: {
                label: "frequency" as const,
                units: "cm-1",
            },
            yAxis: {
                label: "Phonon DOS" as const,
                units: "states/cm-1",
            },
            xDataArray: [0.0, 100.0, 200.0, 300.0],
            yDataSeries: [[0.1, 0.2, 0.3, 0.4] as [number, ...number[]]],
        };

        const phononDOSProperty = new PhononDOSProperty(config);

        expect(phononDOSProperty).to.be.instanceOf(PhononDOSProperty);
        expect(PhononDOSProperty.propertyType).equal(PropertyType.non_scalar);
        expect(PhononDOSProperty.propertyName).equal(PropertyName.phonon_dos);
    });
});
