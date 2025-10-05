import { z } from "zod";


const num = z.coerce.number("Must be a number")

export const zoomFormSchema = z
    .object({
        xMin: num,
        xMax: num,
        yMin: num,
        yMax: num,
    })
    .refine(function (values) {
        const { xMin, xMax, yMin, yMax } = values || {};
        return xMin <= xMax && yMin <= yMax;

    }, "Min must be ≤ Max");

export type ZoomValues = z.infer<typeof zoomFormSchema>;


export const phaseFormSchema = z
    .object({
        period: z.number(),
        epoch: z.number(),
    })

export type PhaseValues = z.infer<typeof phaseFormSchema>;
