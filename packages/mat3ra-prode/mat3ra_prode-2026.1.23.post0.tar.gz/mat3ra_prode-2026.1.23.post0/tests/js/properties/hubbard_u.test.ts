import type { HubbardUParametersPropertySchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import HubbardUProperty from "../../../src/js/properties/non-scalar/HubbardUProperty";
import { PropertyName, PropertyType } from "../../../src/js/settings";

describe("HubbardUProperty", () => {
    it("should create a hubbard u property with correct constructor, propertyType, and propertyName", () => {
        const config: Omit<HubbardUParametersPropertySchema, "name"> = {
            units: "eV",
            values: [
                {
                    id: 0,
                    atomicSpecies: "Fe",
                    orbitalName: "3d",
                    value: 4.0,
                },
            ],
        };

        const hubbardUProperty = new HubbardUProperty(config);

        expect(hubbardUProperty).to.be.instanceOf(HubbardUProperty);
        expect(HubbardUProperty.propertyType).equal(PropertyType.non_scalar);
        expect(HubbardUProperty.propertyName).equal(PropertyName.hubbard_u);
    });
});
