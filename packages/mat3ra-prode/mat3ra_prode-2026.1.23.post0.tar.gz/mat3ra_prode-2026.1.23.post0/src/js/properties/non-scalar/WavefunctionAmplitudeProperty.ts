/* eslint-disable class-methods-use-this */
/* eslint-disable max-classes-per-file */
import type { Constructor } from "@mat3ra/code/dist/js/utils/types";
import type { WavefunctionAmplitudePropertySchema } from "@mat3ra/esse/dist/js/types";
import type { Options } from "highcharts";
import zip from "lodash/zip";

import {
    WavefunctionAmplitudePropertySchemaMixin,
    wavefunctionAmplitudePropertySchemaMixin,
} from "../../generated/WavefunctionAmplitudePropertySchemaMixin";
import Property from "../../Property";
import { PropertyName, PropertyType } from "../../settings";
import { TwoDimensionalHighChartConfigMixin } from "../include/mixins/2d_plot";

type Schema = WavefunctionAmplitudePropertySchema;

export class WavefunctionAmplitudeConfig extends TwoDimensionalHighChartConfigMixin {
    // TODO: figure out how and where from to pass axis so it's `z coordinate` or so.
    readonly tooltipXAxisName: string = "coordinate";

    readonly tooltipYAxisName: string = "amplitude";

    get series() {
        return this.yDataSeries.map((item, index) => {
            return {
                animation: false,
                name: `wavefunction ${index + 1}`,
                data: zip(this.xDataArray, item) as [number, number][],
            };
        });
    }

    get overrideConfig() {
        return {
            ...super.overrideConfig,
            legend: {
                layout: "horizontal",
                align: "center",
                verticalAlign: "bottom",
                borderWidth: 0,
            },
        };
    }
}

type Base = typeof Property<Schema> & Constructor<WavefunctionAmplitudePropertySchemaMixin>;

class WavefunctionAmplitudeProperty extends (Property as Base) implements Schema {
    readonly subtitle: string = "Wavefunction Amplitude";

    readonly yAxisTitle: string = "Amplitude";

    readonly xAxisTitle: string = "Coordinate";

    readonly chartConfig: Options = new WavefunctionAmplitudeConfig(this).config;

    static readonly isRefined = true;

    static readonly propertyName = PropertyName.wavefunction_amplitude;

    static readonly propertyType = PropertyType.non_scalar;

    constructor(config: Omit<Schema, "name">) {
        super({ ...config, name: WavefunctionAmplitudeProperty.propertyName });
    }
}

wavefunctionAmplitudePropertySchemaMixin(WavefunctionAmplitudeProperty.prototype);

export default WavefunctionAmplitudeProperty;
