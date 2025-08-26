import * as yup from "yup";
import type {InferType} from "yup";

const numField = yup
    .number()
    .optional()
    .transform((value, originalValue) =>
       originalValue === "" ? undefined : value
    )
    .typeError("Must be a number");

export const zoomFormSchema = yup
    .object({
        min: numField,
        max: numField,
    })
    .test(
        "both-or-none",
        "Enter both values or leave both empty",
        function (values) {
            const { min, max } = values || {};
            const empty = (v: unknown) => v === undefined;
            const bothEmpty = empty(min) && empty(max);
            const bothNumbers =
                typeof min === "number" &&
                !Number.isNaN(min) &&
                typeof max === "number" &&
                !Number.isNaN(max);

            if (!(bothEmpty || bothNumbers)) {
                return this.createError({
                    message: 'Enter both values or leave both empty',
                    path: "global",
                });
            }

            return true;
        }
    )
    .test("order", "Min must be ≤ Max", function (values) {
        const { min, max } = values || {};
        if (min === undefined || max === undefined) return true;
        if (min > max) {
            return this.createError({
                message: 'Lower bound must be smaller or equal to upper bound.',
                path: "global",
            });
        }
        return true;
    });

export type ZoomValues = InferType<typeof zoomFormSchema>;
