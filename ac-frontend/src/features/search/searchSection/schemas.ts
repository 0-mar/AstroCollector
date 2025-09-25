import { z } from "zod";

// TODO limit search radius and coordinates

const optionalNumberFromText = (msg: string) =>
    z.preprocess(
        (v) => {
            if (v === "" || v == null) return undefined;           // treat empty as omitted
            if (typeof v === "string") return Number(v);           // "12.3" -> 12.3
            return v;                                              // already a number
        },
        z
            .number(msg)
            .refine((n) => Number.isFinite(n), { message: msg })   // reject NaN/Infinity
            .optional()
    );

export const searchFormSchema = z
    .object({
        objectName: z.string().optional(),
        rightAscension: optionalNumberFromText("Right ascension must be a number"),
        declination:   optionalNumberFromText("Declination must be a number"),
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
