import type { AtomicConstraintsPropertySchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import AtomicConstraintsProperty from "../../../src/js/proto_properties/AtomicConstraintsProperty";
import { PropertyName } from "../../../src/js/settings";

describe("AtomicConstraintsProperty", () => {
    it("should create an atomic constraints property with correct constructor and propertyName", () => {
        const config: Omit<AtomicConstraintsPropertySchema, "name"> = {
            values: [
                {
                    id: 0,
                    value: [true, true, false],
                },
            ],
        };

        const atomicConstraintsProperty = new AtomicConstraintsProperty(config);

        expect(atomicConstraintsProperty).to.be.instanceOf(AtomicConstraintsProperty);
        expect(AtomicConstraintsProperty.propertyName).equal(PropertyName.atomic_constraints);
    });
});
