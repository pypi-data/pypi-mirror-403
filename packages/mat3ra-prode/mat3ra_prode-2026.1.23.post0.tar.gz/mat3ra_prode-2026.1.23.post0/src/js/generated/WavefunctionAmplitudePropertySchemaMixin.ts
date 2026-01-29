import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import type { WavefunctionAmplitudePropertySchema } from "@mat3ra/esse/dist/js/types";

export type WavefunctionAmplitudePropertySchemaMixin = Omit<
    WavefunctionAmplitudePropertySchema,
    "_id" | "slug" | "systemName" | "schemaVersion"
>;

export type WavefunctionAmplitudePropertyInMemoryEntity = InMemoryEntity &
    WavefunctionAmplitudePropertySchemaMixin;

export function wavefunctionAmplitudePropertySchemaMixin(item: InMemoryEntity) {
    // @ts-expect-error
    const properties: InMemoryEntity & WavefunctionAmplitudePropertySchemaMixin = {
        get xAxis() {
            return this.requiredProp<WavefunctionAmplitudePropertySchema["xAxis"]>("xAxis");
        },
        get yAxis() {
            return this.requiredProp<WavefunctionAmplitudePropertySchema["yAxis"]>("yAxis");
        },
        get name() {
            return this.requiredProp<WavefunctionAmplitudePropertySchema["name"]>("name");
        },
        get xDataArray() {
            return this.requiredProp<WavefunctionAmplitudePropertySchema["xDataArray"]>(
                "xDataArray",
            );
        },
        get yDataSeries() {
            return this.requiredProp<WavefunctionAmplitudePropertySchema["yDataSeries"]>(
                "yDataSeries",
            );
        },
    };

    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
