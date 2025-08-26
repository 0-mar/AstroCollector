import * as yup from "yup";
import type {InferType} from "yup";

/*export const zoomFormSchema = yup
    .object({
        min: yup.number().optional(),
        max: yup.number().optional(),
    })

export type ZoomValues = InferType<typeof zoomFormSchema>*/

const numField = yup
    .number()
    .transform((value, originalValue) =>
        originalValue === "" ? undefined : value
    )
    .typeError("Must be a number")
    .nullable()
    .notRequired();

export const zoomFormSchema = yup
    .object({
        min: numField,
        max: numField,
    })
    .test(
        "both-or-none",
        "Enter both values or leave both empty",
        (values) => {
            const { min, max } = values || {};
            const empty = (v: unknown) => v === undefined || v === null;
            const bothEmpty = empty(min) && empty(max);
            const bothNumbers =
                typeof min === "number" &&
                !Number.isNaN(min) &&
                typeof max === "number" &&
                !Number.isNaN(max);
            return bothEmpty || bothNumbers;
        }
    )
    // OPTIONAL: also enforce min ≤ max when both provided
    .test("order", "Min must be ≤ Max", (values) => {
        const { min, max } = values || {};
        if (min == null || max == null) return true; // handled by previous test
        return min <= max;
    });

export type ZoomValues = InferType<typeof zoomFormSchema>;
