/* eslint-disable no-unused-expressions */
import ExampleWavefunctionAmplitude from "@mat3ra/esse/dist/js/example/properties_directory/non_scalar/wavefunction_amplitude.json";
import type { WavefunctionAmplitudePropertySchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import WavefunctionAmplitudeProperty from "../../../src/js/properties/non-scalar/WavefunctionAmplitudeProperty";
import { PropertyName, PropertyType } from "../../../src/js/settings";

describe("WavefunctionAmplitudeProperty", () => {
    const config: Omit<WavefunctionAmplitudePropertySchema, "name"> =
        ExampleWavefunctionAmplitude as unknown as Omit<
            WavefunctionAmplitudePropertySchema,
            "name"
        >;

    it("should create a wavefunction amplitude property with correct constructor, propertyType, propertyName, and defined properties", () => {
        const wavefunctionAmplitudeProperty = new WavefunctionAmplitudeProperty(config);

        // Test basic properties
        expect(wavefunctionAmplitudeProperty).to.be.instanceOf(WavefunctionAmplitudeProperty);
        expect(WavefunctionAmplitudeProperty.propertyType).equal(PropertyType.non_scalar);
        expect(WavefunctionAmplitudeProperty.propertyName).equal(
            PropertyName.wavefunction_amplitude,
        );
        expect(WavefunctionAmplitudeProperty.isRefined).to.be.true;

        // Test defined properties
        expect(wavefunctionAmplitudeProperty.subtitle).to.equal("Wavefunction Amplitude");
        expect(wavefunctionAmplitudeProperty.yAxisTitle).to.equal("Amplitude");
        expect(wavefunctionAmplitudeProperty.xAxisTitle).to.equal("Coordinate");
        expect(wavefunctionAmplitudeProperty.chartConfig).to.exist;
        expect(wavefunctionAmplitudeProperty.chartConfig).to.be.an("object");
    });
});
