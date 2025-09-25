import { z } from "zod";


const numField = z
    .number()

export const zoomFormSchema = z
    .object({
        min: numField,
        max: numField,
    })
    .refine(function (values) {
        const { min, max } = values || {};
        if (min === undefined || max === undefined) return true;
        return min <= max;

    }, "Min must be ≤ Max");

export type ZoomValues = z.infer<typeof zoomFormSchema>;


export const phaseFormSchema = z
    .object({
        period: z.number(),
        epoch: z.number(),
    })

export type PhaseValues = z.infer<typeof phaseFormSchema>;
