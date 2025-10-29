import { z } from "zod";

export const searchFormSchema = z
    .object({
        objectName: z.string().optional(),
        rightAscension: z.preprocess(
            (v) => {
                if (v === "" || v == null) return undefined; // treat empty as omitted
                if (typeof v === "string") return Number(v);
                return v;
            },
            z
                .number("Right ascension must be a number")
                .refine((n) => Number.isFinite(n), { message: "Right ascension must be a number" })
                .gte(0, { message: "Right ascension must be equal or greater than 0°" })
                .lte(360, { message: "Right ascension must be equal or less than 360°" })
                .optional()
        ),
        declination: z.preprocess(
            (v) => {
                if (v === "" || v == null) return undefined; // treat empty as omitted
                if (typeof v === "string") return Number(v);
                return v;
            },
            z
                .number("Declination must be a number")
                .refine((n) => Number.isFinite(n), { message: "Declination must be a number" })
                .gte(-90, { message: "Declination must be equal or greater than -90°" })
                .lte(90, { message: "Right ascension must be equal or less than 90°" })
                .optional()
        ),
        radius: z.preprocess(
            (v) => {
                if (v === "" || v == null) return undefined;
                return typeof v === "string" ? Number(v) : v;
            },
            z
                .number("Radius must be a number")
                .refine((n) => Number.isFinite(n), { message: "Radius must be a number" })
                .gt(0, { message: "Radius must be greater than zero" })
                .optional()
        ),
    })
    .superRefine((value, ctx) => {
        const hasObjectName = (value.objectName ?? "").trim() !== "";
        const hasPartialCoords =
            value.rightAscension !== undefined ||
            value.declination !== undefined ||
            value.radius !== undefined;
        const hasAllCoords =
            value.rightAscension !== undefined &&
            value.declination !== undefined &&
            value.radius !== undefined;

        if ((hasObjectName && hasPartialCoords) || (!hasObjectName && !hasAllCoords)) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                path: ["global"],
                message: "Provide object name, or coordinates and radius",
            });
        }
    });


export type SearchFormValues = z.infer<typeof searchFormSchema>;
